"""
name: watchlist_router.py
description: FastAPI router for managing the user's watchlist (add/remove symbols).
             Symbols in the watchlist drive the per-ticker news crawl and detail analysis.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.models import Watchlist

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


class WatchlistAddRequest(BaseModel):
    symbol: str


@router.get("/", summary="List all active watchlist symbols")
async def list_watchlist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Watchlist).where(Watchlist.is_active == True).order_by(Watchlist.added_at.desc())
    )
    items = result.scalars().all()
    return {"total": len(items), "symbols": [{"symbol": i.symbol, "added_at": i.added_at.isoformat()} for i in items]}


@router.post("/", summary="Add a symbol to the watchlist")
async def add_to_watchlist(request: WatchlistAddRequest, db: AsyncSession = Depends(get_db)):
    symbol = request.symbol.upper()
    existing = await db.execute(select(Watchlist).where(Watchlist.symbol == symbol))
    item = existing.scalar_one_or_none()

    if item:
        item.is_active = True
        await db.commit()
        return {"message": f"{symbol} already exists, set to active.", "symbol": symbol}

    db.add(Watchlist(symbol=symbol))
    await db.commit()
    return {"message": f"{symbol} added to watchlist.", "symbol": symbol}


@router.delete("/{symbol}", summary="Remove a symbol from the watchlist")
async def remove_from_watchlist(symbol: str, db: AsyncSession = Depends(get_db)):
    symbol = symbol.upper()
    result = await db.execute(select(Watchlist).where(Watchlist.symbol == symbol))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found in watchlist.")
    item.is_active = False
    await db.commit()
    return {"message": f"{symbol} deactivated from watchlist.", "symbol": symbol}
