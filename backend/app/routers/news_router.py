"""
name: news_router.py
description: FastAPI router for news retrieval and manual crawl trigger endpoints.
             Serves pre-crawled articles from PostgreSQL (Neon) by category.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.services import news_service

router = APIRouter(prefix="/api/news", tags=["News"])


async def get_db() -> AsyncSession:
    """Dependency: yields an async database session."""
    async with async_session_maker() as session:
        yield session


@router.get("/", summary="Get News Articles by Category")
async def get_news(
    type: str = Query(default="macro", pattern="^(macro|watchlist)$"),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the most recent news articles for the specified category.

    - **type**: `macro` (general market news) or `watchlist` (per-ticker news)
    - **limit**: Number of articles to return (max 100)
    """
    try:
        articles = await news_service.get_news_by_category(db, category=type, limit=limit)
        return {"type": type, "total": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbol/{symbol}", summary="Get News for a Specific Symbol")
async def get_news_by_symbol(
    symbol: str,
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns recent articles linked to a specific watchlist symbol.

    - **symbol**: Stock ticker (e.g. FPT, HPG)
    - **limit**: Number of articles (max 50)
    """
    try:
        articles = await news_service.get_news_by_symbol(db, symbol=symbol.upper(), limit=limit)
        return {"symbol": symbol.upper(), "total": len(articles), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
