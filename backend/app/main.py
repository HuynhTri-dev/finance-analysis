"""
name: main.py
description: FastAPI application entry point for the Finance Analysis backend.
             Configures CORS, mounts all API routers, and starts the APScheduler
             for automated RSS news crawling at 08:00, 11:30, and 16:30 ICT.
"""

from __future__ import annotations

import os
import tempfile

# ---------------------------------------------------------------------------
# Serverless Environment Fix (Vercel / AWS Lambda Read-Only Filesystem)
# Redirect $HOME and cache dirs to /tmp so vnstock, matplotlib, etc. can write
# ---------------------------------------------------------------------------
_tmp_dir = tempfile.gettempdir()
os.environ.setdefault("HOME", _tmp_dir)
os.environ.setdefault("MPLCONFIGDIR", _tmp_dir)
os.environ.setdefault("XDG_CACHE_HOME", os.path.join(_tmp_dir, ".cache"))
os.environ.setdefault("XDG_CONFIG_HOME", os.path.join(_tmp_dir, ".config"))

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.infra.database import async_session_maker, engine
from sqlalchemy import text
from app.routers import analyze_router, market_router, news_router, watchlist_router, report_router
from app.services import news_service, scanner_service

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Finance Analysis API",
    description="Backend API for the AI Financial Analysis Dashboard",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow Next.js dev server and production domain
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://your-domain.com",
        "https://finance-analysis-black.vercel.app"
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import tempfile
from pathlib import Path
from fastapi.staticfiles import StaticFiles

try:
    static_dir = Path(__file__).resolve().parent.parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "reports").mkdir(parents=True, exist_ok=True)
except OSError:
    # Serverless runtime (e.g. Vercel/AWS Lambda where root is read-only)
    static_dir = Path(tempfile.gettempdir()) / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "reports").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(market_router.router)
app.include_router(news_router.router)
app.include_router(analyze_router.router)
app.include_router(watchlist_router.router)
app.include_router(report_router.router)


# ---------------------------------------------------------------------------
# APScheduler — RSS crawl jobs
# ICT = UTC+7, so 08:00 ICT = 01:00 UTC, 11:30 ICT = 04:30 UTC, 16:30 ICT = 09:30 UTC
# ---------------------------------------------------------------------------
scheduler = AsyncIOScheduler()


async def _run_crawl_job() -> None:
    """Scheduled task: crawl macro and watchlist RSS feeds."""
    logger.info("Scheduled crawl job started.")
    async with async_session_maker() as db:
        macro_count = await news_service.crawl_macro_news(db)
        watchlist_count = await news_service.crawl_watchlist_news(db)
    logger.info("Crawl complete: %d macro + %d watchlist articles inserted.", macro_count, watchlist_count)


async def _run_scanner_job() -> None:
    """Scheduled task: run nightly full-market quantitative scan."""
    logger.info("Nightly market scanner job triggered.")
    summary = await scanner_service.run_market_scan()
    logger.info("Scanner job complete: %s", summary)


@app.on_event("startup")
async def on_startup() -> None:
    """Register cron jobs on app startup."""
    # Auto migrate Watchlist table by adding 'is_holding' if not exists
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE watchlist ADD COLUMN IF NOT EXISTS is_holding BOOLEAN DEFAULT FALSE;"))
        logger.info("Database migration successful: verified 'is_holding' exists in 'watchlist'")
    except Exception as e:
        logger.warning("Database migration check failed: %s", e)

    # Auto-create top_recommendation table if it doesn't exist
    try:
        from app.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database bootstrap: all tables verified/created.")
    except Exception as e:
        logger.warning("Database table bootstrap failed: %s", e)

    # Morning crawl — 08:00 ICT
    scheduler.add_job(_run_crawl_job, CronTrigger(hour=1, minute=0, timezone="UTC"), id="crawl_morning")
    # Midday crawl — 11:30 ICT
    scheduler.add_job(_run_crawl_job, CronTrigger(hour=4, minute=30, timezone="UTC"), id="crawl_midday")
    # Close crawl — 16:30 ICT
    scheduler.add_job(_run_crawl_job, CronTrigger(hour=9, minute=30, timezone="UTC"), id="crawl_close")
    # Nightly market scanner — 15:30 ICT (08:30 UTC) — after market close
    scheduler.add_job(
        _run_scanner_job,
        CronTrigger(hour=8, minute=30, timezone="UTC"),
        id="scanner_nightly",
    )
    scheduler.start()
    logger.info("APScheduler started with 3 crawl jobs + 1 nightly market scanner (15:30 ICT).")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped.")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Finance Analysis API v1.0.0"}

