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
from app.services import market_service, scanner_service

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


@router.get("/top-recommendations", summary="Get Top Buy Recommendations from last nightly scan")
async def get_top_recommendations(limit: int = Query(20, ge=1, le=100)):
    """
    Returns the top-scored stocks from the most recent nightly market scanner run.
    Each record includes technical score, days_in_top (FOMO streak), RSI, Bollinger Bands, and MAs.

    Output:
        list[dict]: Top recommendation list sorted by tech_score desc, then days_in_top desc.
    """
    try:
        data = await scanner_service.get_top_recommendations(limit=limit)
        return {"total": len(data), "items": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch top recommendations: {e}")


@router.post("/scan-top", summary="Manually trigger nightly market scanner")
async def trigger_scan():
    """
    Manually trigger the full-market quantitative scan immediately (outside the scheduled 15:30 ICT window).
    Useful for initial population of the top_recommendation table or on-demand refresh.
    Note: This scans all HOSE symbols and may take 10-15 minutes to complete.

    Output:
        dict: Scanner summary (scanned, qualified, errors, elapsed_seconds, top_symbols).
    """
    try:
        summary = await scanner_service.run_market_scan()
        return {"status": "complete", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market scan failed: {e}")
