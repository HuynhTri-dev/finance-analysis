"""
name: news_schema.py
description: Pydantic schemas for financial news articles and listings.
             Defines request and response structures for macro and symbol news.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NewsArticleResponse(BaseModel):
    """Schema representing a single news article item."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique UUID identifier for the news article.")
    title: str = Field(..., description="Headline of the article.")
    url: str = Field(..., description="Original article URL.")
    source: str = Field(..., description="News publisher source (e.g., CafeF, VnEconomy).")
    summary: Optional[str] = Field(default=None, description="Cleaned excerpt or summary.")
    published_at: str = Field(..., description="Publication datetime string.")
    category: Optional[str] = Field(default=None, description="Category: 'macro' or 'watchlist'.")


class NewsListResponse(BaseModel):
    """Response container for categorised news articles."""
    type: str = Field(..., description="Category type ('macro' or 'watchlist').")
    total: int = Field(..., description="Number of articles returned.")
    articles: list[NewsArticleResponse] = Field(
        default_factory=list,
        description="List of news articles.",
    )


class NewsSymbolResponse(BaseModel):
    """Response container for symbol-specific news articles."""
    symbol: str = Field(..., description="Target ticker symbol.")
    total: int = Field(..., description="Number of articles returned.")
    articles: list[NewsArticleResponse] = Field(
        default_factory=list,
        description="List of news articles matching the symbol.",
    )
