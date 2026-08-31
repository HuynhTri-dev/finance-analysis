"""
name: market_service.py
description: Service layer for retrieving Vietnam stock market data, realtime quotes,
             order book depth, foreign flows, technical indicators, and historical OHLCV.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any

import os
import tempfile

_tmp = tempfile.gettempdir()
os.environ.setdefault("HOME", _tmp)
os.environ.setdefault("MPLCONFIGDIR", _tmp)

import numpy as np
import pandas as pd
import requests
from vnstock.api.quote import Quote
from vnstock.api.trading import Trading



logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple In-Memory TTL Cache
# ---------------------------------------------------------------------------
_CACHE: dict[str, tuple[float, Any]] = {}
_TTL_OVERVIEW_SECONDS = 60  # 1 min for overview
_TTL_QUOTE_SECONDS = 15     # 15s for realtime quote
_TTL_HISTORY_SECONDS = 300  # 5 min for historical charts


def _cached(key: str, ttl_seconds: float, fn, *args, **kwargs) -> Any:
    """
    Retrieve value from in-memory cache or compute and store it.

    Input:
        key (str): Unique cache identifier.
        ttl_seconds (float): Time-to-live in seconds.
        fn (callable): Callback function on cache miss.

    Output:
        Any: Cached or freshly computed value.

    Description & Logic:
        - Check if key exists and timestamp is still within ttl_seconds.
        - If valid, return cached value.
        - Otherwise, execute fn(*args, **kwargs), store with current monotonic time, and return.
    """
    now = time.monotonic()
    if key in _CACHE:
        ts, value = _CACHE[key]
        if now - ts < ttl_seconds:
            return value

    value = fn(*args, **kwargs)
    _CACHE[key] = (now, value)
    return value


# ---------------------------------------------------------------------------
# Internal Data Fetching Helpers
# ---------------------------------------------------------------------------

def _fetch_ssi_quote(symbol: str) -> dict[str, Any]:
    """
    Fetch realtime stock quote and order book from SSI iBoard API.

    Input:
        symbol (str): Stock ticker code (e.g., "FPT").

    Output:
        dict[str, Any]: Normalized quote and market depth payload.

    Description & Logic:
        - BR_MARKET_01: Call SSI iBoard market data endpoint for realtime quote, order book, and foreign trade.
        - Parse best 3 bids and best 3 offers.
        - Calculate market capitalization based on listed shares and matched price.
    """
    url = f"https://iboard-query.ssi.com.vn/stock/{symbol.upper()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            if data:
                price = float(data.get("matchedPrice") or data.get("refPrice") or 0)
                ref_price = float(data.get("refPrice") or 0)
                change = float(data.get("priceChange") or 0)
                change_pct = float(data.get("priceChangePercent") or 0)
                listed_shares = int(data.get("listedShare") or 0)
                market_cap = int(listed_shares * price) if listed_shares and price else 0

                # Order book top 3 bids & asks
                bids = [
                    {"price": float(data.get("best1Bid") or 0), "volume": int(data.get("best1BidVol") or 0)},
                    {"price": float(data.get("best2Bid") or 0), "volume": int(data.get("best2BidVol") or 0)},
                    {"price": float(data.get("best3Bid") or 0), "volume": int(data.get("best3BidVol") or 0)},
                ]
                offers = [
                    {"price": float(data.get("best1Offer") or 0), "volume": int(data.get("best1OfferVol") or 0)},
                    {"price": float(data.get("best2Offer") or 0), "volume": int(data.get("best2OfferVol") or 0)},
                    {"price": float(data.get("best3Offer") or 0), "volume": int(data.get("best3OfferVol") or 0)},
                ]

                # Foreign trade & order flow
                foreign_buy_qty = int(data.get("buyForeignQtty") or 0)
                foreign_buy_val = float(data.get("buyForeignValue") or 0)
                foreign_sell_qty = int(data.get("sellForeignQtty") or 0)
                foreign_sell_val = float(data.get("sellForeignValue") or 0)
                foreign_net_val = foreign_buy_val - foreign_sell_val
                foreign_room = int(data.get("remainForeignQtty") or 0)

                active_buy_vol = int(data.get("stockBUVol") or 0)
                active_sell_vol = int(data.get("stockSDVol") or 0)
                total_vol = int(data.get("stockVol") or data.get("nmTotalTradedQty") or 0)
                total_val = float(data.get("nmTotalTradedValue") or 0)

                return {
                    "symbol": symbol.upper(),
                    "company_name_vi": data.get("clientName") or data.get("companyNameVi") or f"Công ty CP {symbol.upper()}",
                    "company_name_en": data.get("clientNameEn") or data.get("companyNameEn") or f"{symbol.upper()} Corp",
                    "exchange": (data.get("exchange") or "HOSE").upper(),
                    "isin": data.get("isin", ""),
                    "price": price,
                    "change": change,
                    "change_pct": change_pct,
                    "ref_price": ref_price,
                    "ceiling": float(data.get("ceiling") or 0),
                    "floor": float(data.get("floor") or 0),
                    "high": float(data.get("highest") or price),
                    "low": float(data.get("lowest") or price),
                    "open": float(data.get("openPrice") or price),
                    "avg_price": float(data.get("avgPrice") or price),
                    "total_volume": total_vol,
                    "total_value": total_val,
                    "listed_shares": listed_shares,
                    "market_cap": market_cap,
                    "bids": bids,
                    "offers": offers,
                    "foreign_flow": {
                        "buy_qty": foreign_buy_qty,
                        "buy_val": foreign_buy_val,
                        "sell_qty": foreign_sell_qty,
                        "sell_val": foreign_sell_val,
                        "net_val": foreign_net_val,
                        "room": foreign_room,
                    },
                    "order_flow": {
                        "active_buy_vol": active_buy_vol,
                        "active_sell_vol": active_sell_vol,
                        "buy_pressure_pct": round((active_buy_vol / (active_buy_vol + active_sell_vol)) * 100, 1) if (active_buy_vol + active_sell_vol) > 0 else 50.0,
                    },
                }
    except Exception as e:
        logger.warning("SSI quote fetch error for %s: %s", symbol, e)

    # Fallback default empty quote structure
    return {
        "symbol": symbol.upper(),
        "company_name_vi": f"Công ty Cổ phần {symbol.upper()}",
        "company_name_en": f"{symbol.upper()} Joint Stock Company",
        "exchange": "HOSE",
        "isin": "",
        "price": 0.0,
        "change": 0.0,
        "change_pct": 0.0,
        "ref_price": 0.0,
        "ceiling": 0.0,
        "floor": 0.0,
        "high": 0.0,
        "low": 0.0,
        "open": 0.0,
        "avg_price": 0.0,
        "total_volume": 0,
        "total_value": 0.0,
        "listed_shares": 0,
        "market_cap": 0,
        "bids": [],
        "offers": [],
        "foreign_flow": {"buy_qty": 0, "buy_val": 0, "sell_qty": 0, "sell_val": 0, "net_val": 0, "room": 0},
        "order_flow": {"active_buy_vol": 0, "active_sell_vol": 0, "buy_pressure_pct": 50.0},
    }


def _compute_technical_indicators(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calculate MA20, MA50, RSI(14), and 52-Week High/Low technical indicators.

    Input:
        df (pd.DataFrame): Historical OHLCV dataframe with columns ['time', 'open', 'high', 'low', 'close', 'volume'].

    Output:
        dict[str, Any]: Summary metrics (RSI, MAs, 52W levels, Trend Signal).

    Description & Logic:
        - BR_TECH_01: Calculate 20-day and 50-day Simple Moving Averages.
        - BR_TECH_02: Calculate RSI with 14-period lookback.
        - BR_TECH_03: Derive technical status based on price vs MA and RSI thresholds.
    """
    if df is None or df.empty or len(df) < 5:
        return {
            "rsi_14": None,
            "ma20": None,
            "ma50": None,
            "high_52w": None,
            "low_52w": None,
            "dist_52w_high_pct": None,
            "dist_52w_low_pct": None,
            "signal": "Chưa đủ dữ liệu",
        }

    close_series = pd.to_numeric(df["close"], errors="coerce")
    high_series = pd.to_numeric(df["high"], errors="coerce")
    low_series = pd.to_numeric(df["low"], errors="coerce")

    # 52-week High/Low
    high_52w = float(high_series.max())
    low_52w = float(low_series.min())
    latest_close = float(close_series.iloc[-1])

    # Moving averages
    ma20_val = float(close_series.rolling(window=20).mean().iloc[-1]) if len(close_series) >= 20 else None
    ma50_val = float(close_series.rolling(window=50).mean().iloc[-1]) if len(close_series) >= 50 else None

    # RSI 14
    rsi_14 = None
    if len(close_series) >= 15:
        delta = close_series.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=14).mean()
        last_gain = gain.iloc[-1]
        last_loss = loss.iloc[-1]
        if last_loss == 0:
            rsi_14 = 100.0
        else:
            rs = last_gain / last_loss
            rsi_14 = round(float(100.0 - (100.0 / (1.0 + rs))), 2)

    # Distances from 52-week extremes
    dist_high_pct = round(((latest_close - high_52w) / high_52w) * 100, 2) if high_52w else 0.0
    dist_low_pct = round(((latest_close - low_52w) / low_52w) * 100, 2) if low_52w else 0.0

    # Signal synthesis
    signal = "Trung lập"
    if rsi_14 is not None:
        if rsi_14 >= 70:
            signal = "Vùng Quá Mua (Cẩn trọng)"
        elif rsi_14 <= 30:
            signal = "Vùng Quá Bán (Cân nhắc gom)"
        elif ma20_val and ma50_val and latest_close > ma20_val > ma50_val:
            signal = "Xu hướng Tăng Mạnh"
        elif ma20_val and latest_close > ma20_val:
            signal = "Tích cực Ngắn hạn"
        elif ma20_val and ma50_val and latest_close < ma20_val < ma50_val:
            signal = "Xu hướng Giảm"
        elif ma20_val and latest_close < ma20_val:
            signal = "Tiêu cực Ngắn hạn"

    return {
        "rsi_14": rsi_14,
        "ma20": round(ma20_val, 2) if ma20_val else None,
        "ma50": round(ma50_val, 2) if ma50_val else None,
        "high_52w": high_52w,
        "low_52w": low_52w,
        "dist_52w_high_pct": dist_high_pct,
        "dist_52w_low_pct": dist_low_pct,
        "signal": signal,
    }


def _fetch_historical_ohlcv(symbol: str, start_date: str, end_date: str, interval: str = "1D") -> pd.DataFrame | None:
    """
    Safely retrieve historical OHLCV data using vnstock 4.x Quote API,
    with fallbacks across multiple data sources (VCI, TCBS).
    """
    sym = symbol.upper().strip()

    # Try vnstock 4.x Quote API with VCI and TCBS sources
    for source in ["VCI", "TCBS"]:
        try:
            q = Quote(symbol=sym, source=source)
            df = q.history(start=start_date, end=end_date, interval=interval)
            if df is not None and not df.empty:
                return df
        except Exception:
            continue

    return None



def _fetch_index_data(symbol: str) -> dict[str, Any]:
    """
    Fetch latest snapshot for a market index (VNINDEX / HNXINDEX / UPCOMINDEX).

    Input:
        symbol (str): Index ticker string.

    Output:
        dict[str, Any]: Index snapshot (close, change, change_pct, volume).

    Description & Logic:
        - Fetch historical daily records from vnstock for the last 7 days.
        - Calculate day-over-day price change and percentage.
    """
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        df = _fetch_historical_ohlcv(symbol=symbol, start_date=start, end_date=end, interval="1D")

        if df is None or df.empty:
            return {"symbol": symbol, "close": None, "change": None, "change_pct": None, "volume": None}

        df.columns = [c.lower() for c in df.columns]
        close_col = "close" if "close" in df.columns else df.columns[-1]

        latest = df.iloc[-1]
        prev_close = df.iloc[-2][close_col] if len(df) >= 2 else latest[close_col]
        change = round(float(latest[close_col]) - float(prev_close), 2)
        change_pct = round((change / float(prev_close)) * 100, 2) if prev_close else 0.0

        return {
            "symbol": symbol,
            "close": float(latest[close_col]),
            "change": change,
            "change_pct": change_pct,
            "volume": int(latest.get("volume", 0) or 0),
        }
    except Exception as e:
        logger.warning("Failed to fetch index %s: %s", symbol, e)
        return {"symbol": symbol, "close": None, "change": None, "change_pct": None, "volume": None}



def _fetch_top_movers() -> tuple[list[dict], list[dict]]:
    """
    Fetch top 10 gainers (by % change) and top 10 by volume across VN30 / HOSE.

    Output:
        tuple[list[dict], list[dict]]: Tuple of (top_gainers, top_volume).
    """
    # 1. Primary: Realtime Priceboard from SSI iBoard API (VN30 / HOSE)
    try:
        url = "https://iboard-query.ssi.com.vn/stock/group/VN30"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            stocks = []
            for item in data:
                sym = item.get("stockSymbol")
                if not sym:
                    continue
                price = float(item.get("matchedPrice") or item.get("refPrice") or 0)
                change_pct = float(item.get("priceChangePercent") or 0)
                vol = int(item.get("nmTotalTradedQty") or item.get("stockVol") or 0)
                stocks.append({
                    "symbol": sym,
                    "close": price,
                    "change_pct": change_pct,
                    "volume": vol,
                })

            if stocks:
                top_gainers = sorted(
                    [s for s in stocks if s["change_pct"] > 0],
                    key=lambda x: x["change_pct"],
                    reverse=True,
                )[:10]
                if not top_gainers:
                    top_gainers = sorted(stocks, key=lambda x: x["change_pct"], reverse=True)[:10]

                top_volume = sorted(stocks, key=lambda x: x["volume"], reverse=True)[:10]
                return top_gainers, top_volume
    except Exception as err:
        logger.warning("SSI top movers fetch error: %s", err)

    # 2. Secondary fallback: vnstock 4.x Trading price_board
    try:
        from vnstock.api.trading import Trading
        t = Trading()
        sample_symbols = ["FPT", "ACB", "TCB", "VCB", "VNM", "HPG", "VIC", "SSI", "MBB", "MWG"]
        df = t.price_board(sample_symbols)
        if df is not None and not df.empty:
            df.columns = [c.lower() for c in df.columns]
            ticker_col = next((c for c in df.columns if c in ("ticker", "symbol", "code")), None)
            change_col = next((c for c in df.columns if "change" in c and "%" in c or "pct" in c), None)
            vol_col = next((c for c in df.columns if "vol" in c or "qty" in c), None)
            close_col = next((c for c in df.columns if c in ("close", "price", "lastprice", "matchedprice")), None)

            if ticker_col:
                df = df.rename(columns={ticker_col: "symbol"})
                if close_col:
                    df["close"] = pd.to_numeric(df[close_col], errors="coerce")
                if change_col:
                    df["change_pct"] = pd.to_numeric(df[change_col], errors="coerce").fillna(0)
                if vol_col:
                    df["volume"] = pd.to_numeric(df[vol_col], errors="coerce").fillna(0)

                top_gainers = (
                    df[df["change_pct"] > 0]
                    .nlargest(10, "change_pct")[["symbol", "close", "change_pct"]]
                    .to_dict(orient="records")
                ) if "change_pct" in df.columns else []
                top_volume = (
                    df.nlargest(10, "volume")[["symbol", "close", "volume"]]
                    .to_dict(orient="records")
                ) if "volume" in df.columns else []
                return top_gainers, top_volume
    except Exception as err:
        logger.warning("Vnstock Trading price board fallback error: %s", err)

    return [], []



# ---------------------------------------------------------------------------
# Public Service APIs
# ---------------------------------------------------------------------------

def get_market_overview() -> dict[str, Any]:
    """
    Build the complete market overview payload for the Dashboard.

    Output:
        dict[str, Any]: Indexes, top gainers, and top volume.

    Description & Logic:
        - Query VNINDEX, HNXINDEX, UPCOMINDEX snapshots and top movers.
        - Cache results in memory for 60 seconds.
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

    return _cached("market_overview", _TTL_OVERVIEW_SECONDS, _build)


def _clean_nan_inf(val: Any) -> Any:
    """
    Recursively replace NaN and Inf float values with None to prevent JSON serialization errors.
    """
    if isinstance(val, dict):
        return {k: _clean_nan_inf(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_clean_nan_inf(v) for v in val]
    elif isinstance(val, float):
        if np.isnan(val) or np.isinf(val):
            return None
    return val


def get_stock_detail(
    symbol: str,
    timeframe: str = "3M",
) -> dict[str, Any]:
    """
    Retrieve comprehensive stock details for the individual Stock Dashboard.

    Input:
        symbol (str): Stock ticker (e.g., "FPT").
        timeframe (str): Chart lookback timeframe ("1M", "3M", "6M", "1Y").

    Output:
        dict[str, Any]: Full dashboard data including realtime quote, order book,
                        foreign flow, technical indicators, and OHLCV records.

    Description & Logic:
        - Step 1: Fetch realtime quote and order book from SSI iBoard API.
        - Step 2: Fetch 365-day OHLCV history to compute 52W High/Low and technicals (MA20, MA50, RSI).
        - Step 3: Filter OHLCV records according to the requested timeframe (1M, 3M, 6M, 1Y).
        - Step 4: Cache response for 15 seconds.
    """
    sym = symbol.upper().strip()
    cache_key = f"stock_detail_{sym}_{timeframe}"

    def _build() -> dict[str, Any]:
        # 1. Realtime Quote & Order Book
        quote_data = _fetch_ssi_quote(sym)

        # 2. Historical OHLCV (up to 365 days for accurate 52W & MA50 calculation)
        now = datetime.now()
        end_date = now.strftime("%Y-%m-%d")
        start_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")

        try:
            df = _fetch_historical_ohlcv(
                symbol=sym, start_date=start_date, end_date=end_date, interval="1D"
            )
        except Exception as e:
            logger.warning("Historical data fetch error for %s: %s", sym, e)
            df = None


        technicals = {}
        records = []

        if df is not None and not df.empty:
            df = df.sort_values("time").reset_index(drop=True)
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            df["open"] = pd.to_numeric(df["open"], errors="coerce")
            df["high"] = pd.to_numeric(df["high"], errors="coerce")
            df["low"] = pd.to_numeric(df["low"], errors="coerce")
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

            # Calculate Moving Averages for chart overlay
            df["ma20"] = df["close"].rolling(window=20).mean().round(2)
            df["ma50"] = df["close"].rolling(window=50).mean().round(2)

            # Calculate Bollinger Bands
            std20 = df["close"].rolling(window=20).std()
            df["bb_upper"] = (df["ma20"] + 2 * std20).round(2)
            df["bb_lower"] = (df["ma20"] - 2 * std20).round(2)

            # Calculate RSI series
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            # Avoid division by zero
            with np.errstate(divide='ignore', invalid='ignore'):
                rs = avg_gain / avg_loss
                df["rsi"] = 100.0 - (100.0 / (1.0 + rs))
            
            df.loc[avg_loss == 0, "rsi"] = 100.0
            df.loc[(avg_gain == 0) & (avg_loss == 0), "rsi"] = 50.0
            df["rsi"] = df["rsi"].round(2)

            # Compute technical indicators
            technicals = _compute_technical_indicators(df)

            # Filter dataframe for requested timeframe
            days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
            lookback_days = days_map.get(timeframe.upper(), 90)
            cutoff_date = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
            
            df_filtered = df[df["time"].astype(str) >= cutoff_date].copy()
            if df_filtered.empty:
                df_filtered = df.tail(60).copy()

            df_filtered["time"] = df_filtered["time"].astype(str)
            df_filtered = df_filtered.where(pd.notnull(df_filtered), None)
            records = df_filtered.to_dict(orient="records")

            # If SSI quote price was 0 (e.g. after hours or failure), fallback to last historical close
            if quote_data.get("price", 0) == 0 and len(df) > 0:
                last_row = df.iloc[-1]
                quote_data["price"] = float(last_row["close"])
                quote_data["high"] = float(last_row["high"])
                quote_data["low"] = float(last_row["low"])
                quote_data["open"] = float(last_row["open"])
                quote_data["total_volume"] = int(last_row["volume"])
                if len(df) >= 2:
                    prev_close = float(df.iloc[-2]["close"])
                    quote_data["ref_price"] = prev_close
                    quote_data["change"] = round(quote_data["price"] - prev_close, 2)
                    quote_data["change_pct"] = round((quote_data["change"] / prev_close) * 100, 2)

        return _clean_nan_inf({
            "symbol": sym,
            "company_name": quote_data.get("company_name_vi", f"Công ty Cổ phần {sym}"),
            "company_name_en": quote_data.get("company_name_en", f"{sym} Corporation"),
            "exchange": quote_data.get("exchange", "HOSE"),
            "quote": quote_data,
            "order_book": {
                "bids": quote_data.get("bids", []),
                "offers": quote_data.get("offers", []),
            },
            "foreign_flow": quote_data.get("foreign_flow", {}),
            "order_flow": quote_data.get("order_flow", {}),
            "technicals": technicals,
            "history": {
                "timeframe": timeframe,
                "total": len(records),
                "records": records,
            },
            # Compatibility field so legacy consumers expecting top-level records won't break
            "records": records,
        })

    return _cached(cache_key, _TTL_QUOTE_SECONDS, _build)


def get_stock_history(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    interval: str = "1D",
) -> dict[str, Any]:
    """
    Retrieve OHLCV history for a single ticker (legacy compatibility).

    Input:
        symbol (str): Stock ticker (e.g. "FPT").
        start (str | None): Start date YYYY-MM-DD.
        end (str | None): End date YYYY-MM-DD.
        interval (str): Chart interval ("1D", "1W", "1M").

    Output:
        dict[str, Any]: OHLCV records list and metadata.
    """
    return get_stock_detail(symbol=symbol, timeframe="3M")


def get_batch_quotes(symbols: list[str]) -> list[dict[str, Any]]:
    """
    Retrieve quick quotes for a list of stock symbols (used by Watchlist sidebar).

    Input:
        symbols (list[str]): List of stock tickers (e.g. ["FPT", "VNM", "CMG"]).

    Output:
        list[dict[str, Any]]: List of quick quote objects with price and % change.

    Description & Logic:
        - Query each symbol from cached SSI quote helper.
        - Return lightweight list for fast watchlist rendering.
    """
    results = []
    for sym in symbols:
        clean_sym = sym.strip().upper()
        if not clean_sym:
            continue
        try:
            quote = _cached(f"quick_quote_{clean_sym}", _TTL_QUOTE_SECONDS, _fetch_ssi_quote, clean_sym)
            results.append({
                "symbol": clean_sym,
                "price": quote.get("price", 0.0),
                "change": quote.get("change", 0.0),
                "change_pct": quote.get("change_pct", 0.0),
                "ref_price": quote.get("ref_price", 0.0),
                "company_name": quote.get("company_name_vi", ""),
            })
        except Exception as e:
            logger.warning("Error getting quick quote for %s: %s", clean_sym, e)
            results.append({
                "symbol": clean_sym,
                "price": 0.0,
                "change": 0.0,
                "change_pct": 0.0,
                "ref_price": 0.0,
                "company_name": "",
            })
    return results
