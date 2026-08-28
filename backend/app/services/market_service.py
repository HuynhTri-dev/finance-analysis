"""
name: market_service.py
description: Service layer for retrieving Vietnam stock market data via vnstock.
             Fetches VNINDEX/HNX/UPCOM overview, top gainers, top volume, and
             individual OHLCV history. Results are cached in-memory (5 min TTL)
             to avoid hammering the upstream data source.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import vnstock as vn

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple TTL cache wrapper around lru_cache
# ---------------------------------------------------------------------------
_CACHE: dict[str, tuple[float, Any]] = {}
_TTL_SECONDS = 300  # 5 minutes


def _cached(key: str, fn, *args, **kwargs) -> Any:
    """
    Retrieve value from in-memory cache or compute and store it.

    Args:
        key: Cache key string.
        fn: Callable to invoke on cache miss.
        *args / **kwargs: Arguments forwarded to fn.

    Returns:
        Cached or freshly computed value.
    """
    now = time.monotonic()
    if key in _CACHE:
        ts, value = _CACHE[key]
        if now - ts < _TTL_SECONDS:
            return value

    value = fn(*args, **kwargs)
    _CACHE[key] = (now, value)
    return value


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def _fetch_index_data(symbol: str) -> dict[str, Any]:
    """
    Fetch latest snapshot for a market index (VNINDEX / HNXINDEX / UPCOMINDEX).

    Args:
        symbol: Index ticker string.

    Returns:
        Dict with keys: symbol, close, change, change_pct, volume.
    """
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        df = vn.stock_historical_data(
            symbol=symbol, start_date=start, end_date=end, resolution="1D", type="index"
        )

        if df is None or df.empty:
            return {"symbol": symbol, "close": None, "change": None, "change_pct": None, "volume": None}

        latest = df.iloc[-1]
        prev_close = df.iloc[-2]["close"] if len(df) >= 2 else latest["close"]
        change = round(float(latest["close"]) - float(prev_close), 2)
        change_pct = round((change / float(prev_close)) * 100, 2) if prev_close else 0.0

        return {
            "symbol": symbol,
            "close": float(latest["close"]),
            "change": change,
            "change_pct": change_pct,
            "volume": int(latest.get("volume", 0)),
        }
    except Exception as e:
        logger.warning("Failed to fetch index %s: %s", symbol, e)
        return {"symbol": symbol, "close": None, "change": None, "change_pct": None, "volume": None}


def _fetch_top_movers() -> tuple[list[dict], list[dict]]:
    """
    Fetch top 10 gainers (by % change) and top 10 by volume.

    Returns:
        Tuple of (top_gainers, top_volume) — each a list of dicts.
    """
    try:
        df = vn.market_top_mover(group="HOSE")

        if df is None or df.empty:
            return [], []

        df = df.where(pd.notnull(df), None)
        df.columns = [c.lower() for c in df.columns]

        # vnstock 0.2.x returns 'ticker' and 'perChange' (or similar)
        # Map whichever column names are present
        ticker_col = next((c for c in df.columns if c in ("ticker", "symbol", "code")), None)
        change_col = next((c for c in df.columns if "change" in c and "pct" not in c.lower() and "%" not in c), None)
        vol_col = next((c for c in df.columns if "vol" in c), None)
        close_col = next((c for c in df.columns if c in ("close", "price", "lastprice")), None)

        if not ticker_col:
            logger.warning("Could not find ticker column in top movers. Columns: %s", df.columns.tolist())
            return [], []

        df = df.rename(columns={ticker_col: "symbol"})
        if close_col:
            df["close"] = pd.to_numeric(df[close_col], errors="coerce")
        if change_col:
            df["change_pct"] = pd.to_numeric(df[change_col], errors="coerce").fillna(0)
        if vol_col:
            df["volume"] = pd.to_numeric(df[vol_col], errors="coerce").fillna(0)

        top_gainers, top_volume = [], []
        if "change_pct" in df.columns:
            top_gainers = (
                df[df["change_pct"] > 0]
                .nlargest(10, "change_pct")[["symbol", "close", "change_pct"]]
                .to_dict(orient="records")
            )
        if "volume" in df.columns:
            top_volume = (
                df.nlargest(10, "volume")[["symbol", "close", "volume"]]
                .to_dict(orient="records")
            )

        return top_gainers, top_volume

    except Exception as e:
        logger.error("Failed to fetch top movers: %s", e)
        return [], []


def get_market_overview() -> dict[str, Any]:
    """
    Build the complete market overview payload for the Dashboard.

    Fetches indexes and top movers with caching (5-min TTL).

    Returns:
        Dict with keys: indexes, top_gainers, top_volume.
    """
    def _build() -> dict[str, Any]:
        index_symbols = ["VNINDEX", "HNXINDEX", "UPCOMINDEX"]
        indexes = [_fetch_index_data(sym) for sym in index_symbols]
        top_gainers, top_volume = _fetch_top_movers()
        return {
            "indexes": indexes,
            "top_gainers": top_gainers,
            "top_volume": top_volume,
        }

    return _cached("market_overview", _build)


def get_stock_history(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    interval: str = "1D",
) -> dict[str, Any]:
    """
    Retrieve OHLCV history for a single ticker (used by detail chart view).

    Args:
        symbol:   Stock ticker (e.g. "FPT").
        start:    Start date string YYYY-MM-DD (defaults to 60 days ago).
        end:      End date string YYYY-MM-DD (defaults to today).
        interval: Chart interval ("1D", "1W", "1M").

    Returns:
        Dict with symbol metadata and OHLCV records list.
    """
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    if not start:
        start = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    cache_key = f"ohlcv_{symbol}_{start}_{end}_{interval}"

    def _fetch():
        df = vn.stock_historical_data(
            symbol=symbol.upper(), start_date=start, end_date=end, resolution=interval
        )
        if df is None or df.empty:
            return {"symbol": symbol, "records": [], "total": 0}
        df = df.where(pd.notnull(df), None)
        if "time" in df.columns:
            df["time"] = df["time"].astype(str)
        return {
            "symbol": symbol.upper(),
            "start": start,
            "end": end,
            "interval": interval,
            "total": len(df),
            "records": df.to_dict(orient="records"),
        }

    return _cached(cache_key, _fetch)
