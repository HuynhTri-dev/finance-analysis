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
from app.schemas.finance_analysis_schema import (
    BCTCUploadResponse,
    ChatDocumentRequest,
    ChatDocumentResponse,
    ComprehensiveReportRequest,
    ComprehensiveReportResponse,
    FinancialMetricsExtracted,
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
    ReportDeleteResponse,
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
    # Finance Analysis (BDA Agent)
    "FinancialMetricsExtracted",
    "BCTCUploadResponse",
    "ComprehensiveReportRequest",
    "ComprehensiveReportResponse",
    "ChatDocumentRequest",
    "ChatDocumentResponse",
    # Reports
    "ReportResponse",
    "ReportItemResponse",
    "ReportListResponse",
    "ReportDeleteResponse",
    # Market
    "BatchQuoteItem",
    "IndexQuote",
    "MarketOverviewResponse",
    "StockDetailResponse",
]

