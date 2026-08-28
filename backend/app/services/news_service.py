"""
name: news_service.py
description: News crawler and retrieval service.
             Crawls RSS feeds from CafeF and VnEconomy on a scheduled basis
             (08:00, 11:30, 16:30 ICT). Persists articles to PostgreSQL (Neon)
             categorised as 'macro' or 'watchlist'. Provides query helpers
             for the API routers.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Sequence

import feedparser
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ArticleSymbol, NewsArticle, Watchlist

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RSS source catalogue
# ---------------------------------------------------------------------------
RSS_FEEDS: dict[str, list[str]] = {
    "macro": [
        "https://cafef.vn/thi-truong-chung-khoan.rss",
        "https://vneconomy.vn/chung-khoan.rss",
        "https://cafef.vn/kinh-te-vi-mo.rss",
    ],
    "watchlist": [
        # Per-ticker feeds are assembled dynamically in crawl_watchlist_news()
    ],
}

# CafeF supports per-ticker RSS — pattern used to build watchlist feeds
CAFEF_TICKER_RSS = "https://cafef.vn/du-lieu/{ticker}.rss"


# ---------------------------------------------------------------------------
# HTML → plain text helper
# ---------------------------------------------------------------------------

def _strip_html(raw: str) -> str:
    """
    Remove HTML tags and normalise whitespace from an RSS summary.

    Args:
        raw: HTML string from feedparser entry summary.

    Returns:
        Clean plain-text string (max 500 chars).
    """
    soup = BeautifulSoup(raw or "", "html.parser")
    text = soup.get_text(separator=" ")
    return " ".join(text.split())[:500]


# ---------------------------------------------------------------------------
# Core crawl function
# ---------------------------------------------------------------------------

async def crawl_macro_news(db: AsyncSession) -> int:
    """
    Crawl macro RSS feeds and persist new articles to the database.

    Args:
        db: Active async SQLAlchemy session.

    Returns:
        Number of newly inserted articles.
    """
    inserted = 0
    for url in RSS_FEEDS["macro"]:
        inserted += await _crawl_feed(db, feed_url=url, category="macro", symbols=[])
    logger.info("Macro crawl complete — %d new articles", inserted)
    return inserted


async def crawl_watchlist_news(db: AsyncSession) -> int:
    """
    Crawl per-ticker RSS feeds for all active watchlist symbols.

    Args:
        db: Active async SQLAlchemy session.

    Returns:
        Number of newly inserted articles.
    """
    # Fetch active watchlist symbols
    result = await db.execute(select(Watchlist).where(Watchlist.is_active == True))
    symbols: list[str] = [row.symbol for row in result.scalars().all()]

    inserted = 0
    for symbol in symbols:
        feed_url = CAFEF_TICKER_RSS.format(ticker=symbol.lower())
        inserted += await _crawl_feed(db, feed_url=feed_url, category="watchlist", symbols=[symbol])

    logger.info("Watchlist crawl complete — %d new articles for %d symbols", inserted, len(symbols))
    return inserted


async def _crawl_feed(db: AsyncSession, feed_url: str, category: str, symbols: list[str]) -> int:
    """
    Parse a single RSS feed URL and insert non-duplicate entries.

    Args:
        db:       Active async SQLAlchemy session.
        feed_url: RSS feed URL string.
        category: Either "macro" or "watchlist".
        symbols:  List of ticker strings to link via article_symbol.

    Returns:
        Number of newly inserted articles.
    """
    try:
        parsed = feedparser.parse(feed_url)
    except Exception as e:
        logger.warning("Failed to parse feed %s: %s", feed_url, e)
        return 0

    inserted = 0
    for entry in parsed.entries:
        url = entry.get("link", "")
        if not url:
            continue

        # Idempotency: skip if URL already exists
        exists = await db.execute(select(NewsArticle).where(NewsArticle.url == url))
        if exists.scalar_one_or_none():
            continue

        published_at = datetime.now(tz=timezone.utc)
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                import calendar
                ts = calendar.timegm(entry.published_parsed)
                published_at = datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                pass

        article = NewsArticle(
            id=str(uuid.uuid4()),
            title=entry.get("title", "")[:255],
            url=url,
            source=parsed.feed.get("title", feed_url)[:100],
            content_summary=_strip_html(entry.get("summary", "")),
            published_at=published_at,
            category=category,
        )
        db.add(article)
        await db.flush()  # flush to get the ID before linking symbols

        # Link to watchlist symbols
        for sym in symbols:
            link = ArticleSymbol(article_id=article.id, symbol=sym.upper())
            db.add(link)

        inserted += 1

    await db.commit()
    return inserted


# ---------------------------------------------------------------------------
# Query helpers for API routers
# ---------------------------------------------------------------------------

async def get_news_by_category(db: AsyncSession, category: str, limit: int = 20) -> list[dict]:
    """
    Retrieve the most recent news articles for a given category.

    Args:
        db:       Active async SQLAlchemy session.
        category: "macro" or "watchlist".
        limit:    Maximum number of articles to return.

    Returns:
        List of article dicts.
    """
    result = await db.execute(
        select(NewsArticle)
        .where(NewsArticle.category == category)
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
    )
    articles = result.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "source": a.source,
            "summary": a.content_summary,
            "published_at": a.published_at.isoformat(),
            "category": a.category,
        }
        for a in articles
    ]


async def get_news_by_symbol(db: AsyncSession, symbol: str, limit: int = 10) -> list[dict]:
    """
    Retrieve the latest articles linked to a specific watchlist symbol.

    Args:
        db:     Active async SQLAlchemy session.
        symbol: Stock ticker (e.g. "FPT").
        limit:  Max articles to return.

    Returns:
        List of article dicts.
    """
    result = await db.execute(
        select(NewsArticle)
        .join(ArticleSymbol, ArticleSymbol.article_id == NewsArticle.id)
        .where(ArticleSymbol.symbol == symbol.upper())
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
    )
    articles = result.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "source": a.source,
            "summary": a.content_summary,
            "published_at": a.published_at.isoformat(),
        }
        for a in articles
    ]
