"""
name: __init__.py
description: Package entry point for Pydantic schemas.
             Exports all request and response models across domains:
             watchlist, news, analysis, report, and market.
"""

from app.schemas.analyze_schema import (
    AnalysisResponse,
    DetailAnalysisRequest,
)
from app.schemas.market_schema import (
    BatchQuoteItem,
    IndexQuote,
    MarketOverviewResponse,
    StockDetailResponse,
)
from app.schemas.news_schema import (
    NewsArticleResponse,
    NewsListResponse,
    NewsSymbolResponse,
)
from app.schemas.report_schema import (
    ReportItemResponse,
    ReportListResponse,
    ReportResponse,
)
from app.schemas.watchlist_schema import (
    WatchlistActionResponse,
    WatchlistAddRequest,
    WatchlistItemResponse,
    WatchlistListResponse,
    WatchlistSymbolItem,
)

__all__ = [
    # Watchlist
    "WatchlistAddRequest",
    "WatchlistItemResponse",
    "WatchlistSymbolItem",
    "WatchlistListResponse",
    "WatchlistActionResponse",
    # News
    "NewsArticleResponse",
    "NewsListResponse",
    "NewsSymbolResponse",
    # Analysis
    "DetailAnalysisRequest",
    "AnalysisResponse",
    # Reports
    "ReportResponse",
    "ReportItemResponse",
    "ReportListResponse",
    # Market
    "BatchQuoteItem",
    "IndexQuote",
    "MarketOverviewResponse",
    "StockDetailResponse",
]
