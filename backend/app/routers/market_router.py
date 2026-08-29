"""
name: market_router.py
description: FastAPI router for market data endpoints.
             Exposes market overview, per-symbol dashboard data (realtime quotes,
             order book, foreign flows, technical indicators, OHLCV), and batch quotes.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas import BatchQuoteItem
from app.services import market_service

router = APIRouter(prefix="/api/market", tags=["Market"])


@router.get("/overview", summary="Market Overview — Indexes + Top 10")
def get_market_overview():
    """
    Returns VNINDEX, HNXINDEX, UPCOMINDEX snapshots plus Top 10 gainers
    and Top 10 by volume. Data is cached in-memory.

    Output:
        dict: Market overview with indexes and top movers.
    """
    try:
        data = market_service.get_market_overview()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market overview: {e}")


@router.get("/stock/{symbol}", summary="Complete Dashboard Details for a Single Ticker")
def get_stock_detail(
    symbol: str,
    timeframe: str = Query("3M", description="Chart timeframe: 1M, 3M, 6M, 1Y"),
    start: Optional[str] = None,
    end: Optional[str] = None,
    interval: str = "1D",
):
    """
    Returns comprehensive stock details for the individual Stock Dashboard:
    - Realtime Quote (price, change, ref, ceiling, floor, high, low, open, vol, value)
    - Order Book Depth (Top 3 Bids & Offers)
    - Foreign Flow (Buy, Sell, Net, Room)
    - Order Flow (Active Buy vs Sell volume)
    - Technical Indicators (MA20, MA50, RSI 14, 52W High/Low, Trend signal)
    - Interactive OHLCV records list for the selected timeframe.

    Input:
        symbol (str): Stock ticker (e.g. FPT, VNM, HPG).
        timeframe (str): Chart timeframe (1M, 3M, 6M, 1Y).
    """
    try:
        data = market_service.get_stock_detail(
            symbol=symbol.upper(),
            timeframe=timeframe,
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock details for {symbol}: {e}")


@router.get("/quotes", response_model=list[BatchQuoteItem], summary="Batch Quotes for Watchlist")
def get_batch_quotes(
    symbols: str = Query(..., description="Comma-separated stock symbols (e.g. FPT,VNM,CMG)"),
):
    """
    Returns quick price and % change for a comma-separated list of stock tickers.

    Input:
        symbols (str): Comma-separated symbols.

    Output:
        list[dict]: Array of quick quote objects.
    """
    try:
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
        if not symbol_list:
            return []
        return market_service.get_batch_quotes(symbol_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch batch quotes: {e}")
