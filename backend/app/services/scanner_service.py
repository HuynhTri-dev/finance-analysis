"""
name: scanner_service.py
description: Market scanner service that performs a nightly quantitative sweep of
             all VN-Index listed symbols (sourced from SSI iBoard full listing).
             Computes RSI(14), Bollinger Bands, and Moving Averages for each symbol,
             scores them against a composite buy filter, and persists the top-rated
             symbols to the `top_recommendation` table with a FOMO `days_in_top` counter.
             Designed to be called once per day by APScheduler after market close.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd
import requests
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.models import TopRecommendation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Minimum composite tech score required to enter Top list (max possible = 5)
_MIN_BUY_SCORE = 3

# Delay between each symbol fetch to respect source rate-limits (seconds)
_INTER_SYMBOL_DELAY = 0.8

# Lookback days for OHLCV data download (60 sessions ≈ 3 months, enough for MA50)
_LOOKBACK_DAYS = 90


# ---------------------------------------------------------------------------
# Step 1: Fetch the full listing of VN-Index symbols from SSI
# ---------------------------------------------------------------------------

def _fetch_vnindex_symbols() -> list[str]:
    """
    Fetch all actively listed stock symbols on HOSE (VN-Index) from SSI iBoard
    via their stock list endpoint. Falls back to a hardcoded VN30 list if unavailable.

    Output:
        list[str]: Sorted list of ticker symbols (e.g. ["ACB", "BID", "CTG", ...])
    """
    try:
        url = "https://iboard-query.ssi.com.vn/stock/exchange/HOSE"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # SSI returns a list of dicts or a data wrapper
            items = data if isinstance(data, list) else data.get("data", [])
            symbols = sorted(
                set(
                    str(item.get("stockCode") or item.get("symbol") or "").upper().strip()
                    for item in items
                    if (item.get("stockCode") or item.get("symbol"))
                )
            )
            symbols = [s for s in symbols if 2 <= len(s) <= 5]
            if symbols:
                logger.info("Scanner: Fetched %d HOSE symbols from SSI iBoard.", len(symbols))
                return symbols
    except Exception as exc:
        logger.warning("Scanner: SSI HOSE symbol fetch failed: %s. Falling back to VN30.", exc)

    # --- Hardcoded fallback: VN30 + extended blue-chips ---
    return [
        "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR",
        "HDB", "HPG", "MBB", "MSN", "MWG", "NVL", "PDR", "PLX",
        "POW", "SAB", "SBT", "SSB", "SSI", "STB", "TCB", "TPB",
        "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
        "CMG", "DGC", "DCM", "DPM", "EIB", "EVF", "GEX", "HAG",
        "HCM", "HDG", "HSG", "KBC", "KDC", "KDH", "LPB", "NAB",
        "OCB", "PAN", "PHR", "PNJ", "PPC", "PTB", "REE", "SHS",
        "SZC", "TCH", "TNG", "TRA", "VGC", "VGS", "VND", "VNS",
    ]


# ---------------------------------------------------------------------------
# Step 2: Compute technical indicators for a single symbol
# ---------------------------------------------------------------------------

def _compute_indicators(symbol: str) -> dict[str, Any] | None:
    """
    Download 90-day OHLCV for a symbol and compute RSI(14), MA20, MA50,
    Bollinger Bands(20, 2σ). Returns None if insufficient data.

    Input:
        symbol (str): Stock ticker.

    Output:
        dict | None: Technical indicators dict, or None if data unavailable.
    """
    from vnstock.api.quote import Quote

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    df = None
    for source in ["VCI", "TCBS"]:
        try:
            q = Quote(symbol=symbol, source=source)
            df = q.history(start=start_date, end=end_date, interval="1D")
            if df is not None and not df.empty:
                break
        except Exception:
            continue

    if df is None or df.empty or len(df) < 20:
        return None

    df = df.sort_values("time").reset_index(drop=True)
    close = pd.to_numeric(df["close"], errors="coerce")
    volume = pd.to_numeric(df.get("volume", pd.Series(dtype=float)), errors="coerce")

    # Moving averages
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()

    # Bollinger Bands (20-period, 2σ)
    std20 = close.rolling(20).std()
    bb_upper = ma20 + 2 * std20
    bb_lower = ma20 - 2 * std20

    # RSI(14)
    delta = close.diff()
    avg_gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    avg_loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))

    last = -1
    rsi_val = float(rsi_series.iloc[last]) if pd.notna(rsi_series.iloc[last]) else None
    close_val = float(close.iloc[last]) if pd.notna(close.iloc[last]) else None
    ma20_val = float(ma20.iloc[last]) if pd.notna(ma20.iloc[last]) else None
    ma50_val = float(ma50.iloc[last]) if pd.notna(ma50.iloc[last]) else None
    bb_up_val = float(bb_upper.iloc[last]) if pd.notna(bb_upper.iloc[last]) else None
    bb_lo_val = float(bb_lower.iloc[last]) if pd.notna(bb_lower.iloc[last]) else None
    vol_val = float(volume.iloc[last]) if not volume.empty and pd.notna(volume.iloc[last]) else None

    return {
        "symbol": symbol,
        "price": close_val,
        "rsi": rsi_val,
        "ma20": ma20_val,
        "ma50": ma50_val,
        "bb_upper": bb_up_val,
        "bb_lower": bb_lo_val,
        "volume": vol_val,
    }


# ---------------------------------------------------------------------------
# Step 3: Score each symbol — composite buy signal algorithm
# ---------------------------------------------------------------------------

def _score_symbol(indicators: dict[str, Any]) -> tuple[int, str, list[str]]:
    """
    Apply a composite quantitative scoring algorithm based on:
        - RSI(14): Oversold zone (< 40) +2pts, extreme oversold (< 30) +3pts
        - Bollinger Bands: Price touching/below BB lower +2pts
        - Moving Average trend: MA20 > MA50 (Golden cross tendency) +1pt
        - Price proximity to BB lower band (within 2%) +1pt extra

    Input:
        indicators (dict): Technical metrics for the symbol.

    Output:
        tuple[int, str, list[str]]: (score, rating_label, reasons list)

    Description:
        Total score of 3 = "MUA"; 4+ = "MUA MẠNH".
        Score < 3 means the symbol does not qualify.
    """
    score = 0
    reasons: list[str] = []

    rsi = indicators.get("rsi")
    close = indicators.get("price")
    ma20 = indicators.get("ma20")
    ma50 = indicators.get("ma50")
    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")

    # --- RSI Signal ---
    if rsi is not None:
        if rsi < 30:
            score += 3
            reasons.append(f"RSI={rsi:.1f} — Vùng quá bán cực mạnh (< 30)")
        elif rsi < 40:
            score += 2
            reasons.append(f"RSI={rsi:.1f} — Vùng quá bán (< 40)")

    # --- Bollinger Bands Signal ---
    if close is not None and bb_lower is not None and bb_upper is not None:
        band_width = bb_upper - bb_lower if bb_upper > bb_lower else 1
        dist_to_lower_pct = ((close - bb_lower) / band_width) * 100

        if close <= bb_lower:
            score += 3
            reasons.append(f"Giá ({close:,.0f}) đâm thủng dải dưới Bollinger Bands ({bb_lower:,.0f})")
        elif dist_to_lower_pct <= 10:
            score += 2
            reasons.append(f"Giá ({close:,.0f}) tiệm cận dải dưới Bollinger Bands ({bb_lower:,.0f})")

    # --- Moving Average Trend Signal ---
    if ma20 is not None and ma50 is not None:
        if ma20 > ma50:
            score += 1
            reasons.append(f"MA20 ({ma20:,.0f}) > MA50 ({ma50:,.0f}) — Xu hướng tích cực")
        else:
            # Small penalty: do not add bonus for downtrend
            pass

    # Classify rating
    if score >= 4:
        rating = "MUA MẠNH"
    elif score >= _MIN_BUY_SCORE:
        rating = "MUA"
    else:
        rating = ""

    return score, rating, reasons


# ---------------------------------------------------------------------------
# Step 4: Persist results to DB
# ---------------------------------------------------------------------------

async def _upsert_top_results(results: list[dict[str, Any]]) -> None:
    """
    Upsert a list of qualified top-recommendation records into the DB.
    If a symbol already exists in the table, increment its days_in_top counter.
    If a symbol is NOT in the new scan but exists in DB, remove it
    (it no longer qualifies).

    Input:
        results (list[dict]): List of qualified symbol indicator dicts with rating, score, reason.
    """
    now_utc = datetime.now(timezone.utc)
    qualifying_symbols = {r["symbol"] for r in results}

    async with async_session_maker() as db:
        # 1. Fetch existing TopRecommendation rows
        existing_rows_result = await db.execute(select(TopRecommendation))
        existing_rows: dict[str, TopRecommendation] = {
            row.symbol: row for row in existing_rows_result.scalars().all()
        }

        # 2. Upsert qualifying symbols
        for rec in results:
            symbol = rec["symbol"]
            if symbol in existing_rows:
                # Symbol survived — increment streak
                row = existing_rows[symbol]
                row.days_in_top += 1
                row.recommended_date = now_utc
                row.rating = rec["rating"]
                row.reason = rec["reason"]
                row.price = rec.get("price")
                row.rsi = rec.get("rsi")
                row.ma20 = rec.get("ma20")
                row.ma50 = rec.get("ma50")
                row.bb_upper = rec.get("bb_upper")
                row.bb_lower = rec.get("bb_lower")
                row.volume = rec.get("volume")
                row.tech_score = rec["tech_score"]
            else:
                # New symbol — first appearance
                new_row = TopRecommendation(
                    symbol=symbol,
                    recommended_date=now_utc,
                    first_recommended_date=now_utc,
                    days_in_top=1,
                    tech_score=rec["tech_score"],
                    rating=rec["rating"],
                    reason=rec["reason"],
                    price=rec.get("price"),
                    rsi=rec.get("rsi"),
                    ma20=rec.get("ma20"),
                    ma50=rec.get("ma50"),
                    bb_upper=rec.get("bb_upper"),
                    bb_lower=rec.get("bb_lower"),
                    exchange=rec.get("exchange"),
                    volume=rec.get("volume"),
                )
                db.add(new_row)

        # 3. Remove symbols that dropped out of the criteria
        symbols_to_drop = set(existing_rows.keys()) - qualifying_symbols
        if symbols_to_drop:
            await db.execute(
                delete(TopRecommendation).where(TopRecommendation.symbol.in_(symbols_to_drop))
            )
            logger.info("Scanner: Dropped %d symbols from Top list: %s", len(symbols_to_drop), symbols_to_drop)

        await db.commit()
        logger.info(
            "Scanner: DB upsert complete — %d qualified, %d removed.",
            len(results),
            len(symbols_to_drop),
        )


# ---------------------------------------------------------------------------
# Step 5: Public entry point — run the full scan
# ---------------------------------------------------------------------------

async def run_market_scan() -> dict[str, Any]:
    """
    Orchestrate the full market scan pipeline:
        1. Fetch all HOSE symbols.
        2. For each symbol (with throttle delay), download OHLCV and compute indicators.
        3. Score each symbol and filter those that qualify.
        4. Persist results to DB with days_in_top tracking.

    Output:
        dict: Summary of scan results (scanned, qualified, elapsed_seconds).
    """
    logger.info("=== Market Scanner: Starting nightly full-market scan ===")
    scan_start = time.time()

    symbols = _fetch_vnindex_symbols()
    logger.info("Scanner: Universe size = %d symbols", len(symbols))

    qualified: list[dict[str, Any]] = []
    scanned = 0
    errors = 0

    for symbol in symbols:
        try:
            # Non-blocking sleep to yield control to asyncio event loop
            await asyncio.sleep(_INTER_SYMBOL_DELAY)

            indicators = _compute_indicators(symbol)
            scanned += 1

            if indicators is None:
                continue

            score, rating, reasons = _score_symbol(indicators)

            if score >= _MIN_BUY_SCORE:
                qualified.append({
                    **indicators,
                    "tech_score": score,
                    "rating": rating,
                    "reason": "; ".join(reasons),
                    "exchange": "HOSE",
                })
                logger.info(
                    "Scanner [✓] %s — Score=%d (%s) — RSI=%.1f",
                    symbol, score, rating,
                    indicators.get("rsi") or 0,
                )
        except Exception as exc:
            errors += 1
            logger.warning("Scanner [✗] %s — Error: %s", symbol, exc)

    # Sort by score descending so top ranked symbols appear first in API
    qualified.sort(key=lambda x: x["tech_score"], reverse=True)

    if qualified:
        await _upsert_top_results(qualified)

    elapsed = round(time.time() - scan_start, 1)
    summary = {
        "scanned": scanned,
        "qualified": len(qualified),
        "errors": errors,
        "elapsed_seconds": elapsed,
        "top_symbols": [r["symbol"] for r in qualified[:10]],
    }
    logger.info("=== Market Scanner: Finished in %ss — %d/%d qualified ===", elapsed, len(qualified), scanned)
    return summary


# ---------------------------------------------------------------------------
# Step 6: Fetch top recommendations from DB (for API endpoint)
# ---------------------------------------------------------------------------

async def get_top_recommendations(limit: int = 20) -> list[dict[str, Any]]:
    """
    Retrieve the current top recommendation list from DB, ordered by tech_score
    descending then days_in_top descending.

    Input:
        limit (int): Maximum number of records to return.

    Output:
        list[dict]: List of top recommendation records.
    """
    async with async_session_maker() as db:
        result = await db.execute(
            select(TopRecommendation)
            .order_by(TopRecommendation.tech_score.desc(), TopRecommendation.days_in_top.desc())
            .limit(limit)
        )
        rows = result.scalars().all()

    return [
        {
            "symbol": r.symbol,
            "rating": r.rating,
            "reason": r.reason,
            "tech_score": r.tech_score,
            "days_in_top": r.days_in_top,
            "price": r.price,
            "rsi": r.rsi,
            "ma20": r.ma20,
            "ma50": r.ma50,
            "bb_upper": r.bb_upper,
            "bb_lower": r.bb_lower,
            "exchange": r.exchange or "HOSE",
            "volume": r.volume,
            "recommended_date": r.recommended_date.isoformat() if r.recommended_date else None,
            "first_recommended_date": r.first_recommended_date.isoformat() if r.first_recommended_date else None,
        }
        for r in rows
    ]
