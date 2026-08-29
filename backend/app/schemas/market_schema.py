"""
name: market_schema.py
description: Pydantic schemas for stock market overview, ticker dashboard,
             batch quotes, order book depth, and technical indicators.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class BatchQuoteItem(BaseModel):
    """Minimal quote item returned by batch quote queries."""
    symbol: str = Field(..., description="Stock ticker symbol.")
    price: float = Field(..., description="Current match price.")
    change: float = Field(..., description="Absolute price change.")
    change_pct: float = Field(..., description="Percentage price change.")
    ref_price: float = Field(default=0.0, description="Reference price.")
    company_name: str = Field(default="", description="Company name in Vietnamese.")


class IndexQuote(BaseModel):
    """Snapshot for a market index (e.g., VNINDEX, VN30)."""
    index_id: str = Field(..., description="Index code (e.g., VNINDEX).")
    index_name: str = Field(..., description="Readable index name.")
    current_value: float = Field(..., description="Current index points.")
    change: float = Field(..., description="Points change.")
    change_pct: float = Field(..., description="Percentage change.")
    total_volume: int = Field(default=0, description="Total traded volume.")
    total_value: float = Field(default=0.0, description="Total traded value in billion VND.")
    advances: int = Field(default=0, description="Number of gaining stocks.")
    declines: int = Field(default=0, description="Number of declining stocks.")
    no_change: int = Field(default=0, description="Number of unchanged stocks.")


class MarketOverviewResponse(BaseModel):
    """Aggregated market overview with indices and top moving tickers."""
    timestamp: str = Field(..., description="Timestamp of the market snapshot.")
    indexes: list[IndexQuote] = Field(default_factory=list, description="Major market indexes.")
    top_gainers: list[dict[str, Any]] = Field(default_factory=list, description="Top gaining stocks.")
    top_volume: list[dict[str, Any]] = Field(default_factory=list, description="Top volume leaders.")


class StockDetailResponse(BaseModel):
    """Full detail payload for individual stock dashboard."""
    symbol: str = Field(..., description="Stock ticker symbol.")
    quote: dict[str, Any] = Field(default_factory=dict, description="Realtime price and session stats.")
    order_book: dict[str, Any] = Field(default_factory=dict, description="Top 3 bids and offers depth.")
    foreign_flow: dict[str, Any] = Field(default_factory=dict, description="Foreign investor transactions.")
    order_flow: dict[str, Any] = Field(default_factory=dict, description="Active buying vs selling volume.")
    technicals: dict[str, Any] = Field(default_factory=dict, description="Computed technical indicators.")
    history: dict[str, Any] = Field(default_factory=dict, description="Historical OHLCV series.")
    records: list[dict[str, Any]] = Field(default_factory=list, description="Legacy list of OHLCV bars.")
