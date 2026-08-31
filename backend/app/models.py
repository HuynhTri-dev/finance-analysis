"""
name: models.py
description: SQLAlchemy ORM database models for the Finance Analysis application.
             Defines database entities, tables, relationships, and constraints
             for Watchlist symbols and crawled News Articles.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Date, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utc_now() -> datetime:
    """Return the current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


class ArticleSymbol(Base):
    """
    Association table linking NewsArticle and Watchlist models (Many-to-Many).
    """
    __tablename__ = "article_symbol"

    article_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("news_article.id", ondelete="CASCADE"),
        primary_key=True,
        doc="Unique identifier of the related news article.",
    )
    symbol: Mapped[str] = mapped_column(
        String,
        ForeignKey("watchlist.symbol", ondelete="CASCADE"),
        primary_key=True,
        doc="Stock ticker symbol associated with the article.",
    )


class Watchlist(Base):
    """
    Watchlist entity storing stock tickers monitored by the user.
    """
    __tablename__ = "watchlist"

    symbol: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        index=True,
        doc="Stock ticker symbol (e.g. FPT, VNM, HPG).",
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        doc="Timestamp when the symbol was added to the watchlist.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        doc="Flag indicating whether this watchlist item is active.",
    )
    is_holding: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
        doc="Flag indicating whether this watchlist item is currently held by the user.",
    )

    # Relationships
    articles: Mapped[List[NewsArticle]] = relationship(
        "NewsArticle",
        secondary="article_symbol",
        back_populates="symbols",
        lazy="selectin",
        doc="List of news articles tagged with this ticker symbol.",
    )


class NewsArticle(Base):
    """
    News article entity storing crawled financial news articles and summaries.
    """
    __tablename__ = "news_article"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        doc="UUID string uniquely identifying the article.",
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Headline/title of the article.",
    )
    url: Mapped[str] = mapped_column(
        String(1000),
        unique=True,
        nullable=False,
        doc="Original URL source of the news article.",
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Publishing publisher or source domain (e.g. CafeF, VnEconomy).",
    )
    content_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Plain-text summary or excerpt extracted from the article.",
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
        doc="Original publication datetime in UTC.",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        doc="Category classification: 'macro' or 'watchlist'.",
    )

    # Relationships
    symbols: Mapped[List[Watchlist]] = relationship(
        "Watchlist",
        secondary="article_symbol",
        back_populates="articles",
        lazy="selectin",
        doc="List of watchlist symbols linked to this article.",
    )


class GeneratedReport(Base):
    """
    GeneratedReport entity storing metadata and access URLs of PDF reports.
    """
    __tablename__ = "generated_report"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        doc="UUID string uniquely identifying the generated report.",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable title of the report.",
    )
    report_type: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
        doc="Type of report: 'quick_symbol', 'ai_overview', 'ai_detail'.",
    )
    symbol: Mapped[Optional[str]] = mapped_column(
        String(20),
        index=True,
        nullable=True,
        doc="Ticker symbol if the report is symbol-specific.",
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="File name of the report artifact.",
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Storage path/key in Cloudflare R2 or local static directory.",
    )
    pdf_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        doc="Publicly accessible or presigned download URL.",
    )
    size_kb: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="File size in kilobytes.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        index=True,
        doc="Timestamp when the report was created.",
    )


class TopRecommendation(Base):
    """
    TopRecommendation entity storing the daily market scan results.
    Each record represents a stock that meets the quantitative buy criteria
    (RSI oversold, Bollinger Band lower touch, MA cross). The days_in_top
    field tracks consecutive days a symbol has held the top status, which
    serves as a FOMO / demand signal for the user.
    """
    __tablename__ = "top_recommendation"

    symbol: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        index=True,
        doc="Stock ticker symbol.",
    )
    recommended_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        doc="Date when this stock was last confirmed in the top recommendation list.",
    )
    first_recommended_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        doc="Date when this stock first entered the top recommendation list.",
    )
    days_in_top: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Consecutive days this symbol has remained in the Top Buy list (FOMO indicator).",
    )
    tech_score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Composite technical score (RSI + Bollinger + MA contributions).",
    )
    rating: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Recommendation label: 'MUA MẠNH', 'MUA'.",
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed reason string explaining why the stock passed the filter.",
    )
    price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Latest closing price at time of scan.",
    )
    rsi: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="RSI(14) value at time of scan.",
    )
    ma20: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="MA20 value at time of scan.",
    )
    ma50: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="MA50 value at time of scan.",
    )
    bb_upper: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Bollinger Band upper value at time of scan.",
    )
    bb_lower: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Bollinger Band lower value at time of scan.",
    )
    exchange: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        doc="Exchange listing (HOSE, HNX, UPCOM).",
    )
    volume: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Trading volume at time of scan.",
    )
