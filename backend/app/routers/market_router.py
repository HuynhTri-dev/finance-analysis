"""
name: market_router.py
description: FastAPI router for market data endpoints.
             Exposes market overview (indexes + top 10) and
             per-symbol OHLCV history via clean JSON responses.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services import market_service

router = APIRouter(prefix="/api/market", tags=["Market"])


@router.get("/overview", summary="Market Overview — Indexes + Top 10")
async def get_market_overview():
    """
    Returns VNINDEX, HNXINDEX, UPCOMINDEX snapshots plus Top 10 gainers
    and Top 10 by volume. Data is cached in-memory for 5 minutes.
    """
    try:
        data = market_service.get_market_overview()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market overview: {e}")


@router.get("/stock/{symbol}", summary="OHLCV History for a Single Ticker")
async def get_stock_history(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    interval: str = "1D",
):
    """
    Returns historical OHLCV price data for the given stock symbol.

    - **symbol**: Ticker (e.g. FPT, ACB, HPG)
    - **start**: Start date YYYY-MM-DD (default: 60 days ago)
    - **end**: End date YYYY-MM-DD (default: today)
    - **interval**: Timeframe (1D / 1W / 1M)
    """
    try:
        data = market_service.get_stock_history(
            symbol=symbol.upper(), start=start, end=end, interval=interval
        )
        if not data.get("records"):
            raise HTTPException(
                status_code=404,
                detail=f"No data found for symbol '{symbol.upper()}' in the requested date range.",
            )
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
