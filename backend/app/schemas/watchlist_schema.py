"""
name: watchlist_schema.py
description: Pydantic models for watchlist requests and responses.
             Handles validation for stock symbols and data serialization.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class WatchlistAddRequest(BaseModel):
    """Request payload for adding or activating a symbol in the watchlist."""
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Stock ticker symbol (e.g., FPT, VNM, HPG).",
        examples=["FPT"],
    )


class WatchlistItemResponse(BaseModel):
    """Single watchlist item representation."""
    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="Stock ticker symbol.")
    added_at: datetime = Field(..., description="Timestamp when symbol was added.")
    is_active: bool = Field(default=True, description="Active status of the watchlist item.")


class WatchlistSymbolItem(BaseModel):
    """Minimal symbol item for API response listing."""
    symbol: str = Field(..., description="Stock ticker symbol.")
    added_at: str = Field(..., description="ISO 8601 formatted timestamp string.")
    is_holding: bool = Field(default=False, description="Flag indicating if the stock is held in the portfolio.")


class WatchlistListResponse(BaseModel):
    """Response payload for listing active watchlist symbols."""
    total: int = Field(..., description="Total count of active watchlist symbols.")
    symbols: list[WatchlistSymbolItem] = Field(
        default_factory=list,
        description="List of active watchlist items.",
    )


class WatchlistActionResponse(BaseModel):
    """Response payload returned when a symbol is added or removed."""
    message: str = Field(..., description="Status or confirmation message.")
    symbol: str = Field(..., description="Target stock ticker symbol.")
