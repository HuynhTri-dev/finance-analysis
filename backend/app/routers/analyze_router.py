"""
name: analyze_router.py
description: FastAPI router for AI analysis endpoints.
             Triggers the AI Orchestrator to generate Markdown reports
             for market overview and per-symbol detail analysis.
             Reports are uploaded to Cloudflare R2 as PDFs via the
             existing S3StorageProvider infrastructure.
"""

from __future__ import annotations

from typing import Optional
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.infra.storage import S3StorageProvider, get_r2_client
from app.schemas import AnalysisResponse, DetailAnalysisRequest
from app.services import ai_orchestrator_service, market_service, news_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


# ---------------------------------------------------------------------------
# Helper: upload markdown → PDF to Cloudflare R2
# ---------------------------------------------------------------------------

async def _upload_report_to_r2(content: str, filename: str) -> str | None:
    """
    Convert markdown report to PDF bytes and upload to Cloudflare R2.
    Returns the public URL or None on failure.

    Args:
        content:  Markdown string from AI.
        filename: Destination filename in R2 bucket (e.g. "overview_20260828.pdf").

    Returns:
        Public URL string or None.
    """
    try:
        from fpdf import FPDF
        
        # Simple PDF generation using fpdf2
        class PDF(FPDF):
            pass
            
        pdf = PDF()
        pdf.add_page()
        # Add unicode font
        try:
            pdf.add_font("Roboto", "", "app/Roboto-Regular.ttf", uni=True)
            pdf.set_font("Roboto", size=11)
        except Exception:
            pdf.set_font("Helvetica", size=11)
            # Remove non-ascii if fallback font is used
            content = content.encode("ascii", "ignore").decode("ascii")
            
        # Write markdown content (fpdf2 supports basic html, but we'll use multi_cell for raw text for safety)
        pdf.multi_cell(0, 6, txt=content)
        pdf_bytes = pdf.output(dest='S')
        
        # Upload to R2
        provider = S3StorageProvider()
        object_name = f"reports/{filename}"
        await provider.upload_file(
            file_data=pdf_bytes,
            object_name=object_name,
            content_type="application/pdf",
        )
        
        # Generate presigned URL (valid for 7 days)
        url = await provider.get_file_url(object_name, expires_in=604800)
        return url
    except Exception as e:
        logger.warning("Failed to upload report to R2: %s", e)
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/overview", response_model=AnalysisResponse, summary="AI Market Overview Report")
async def analyze_overview(db: AsyncSession = Depends(get_db)):
    """
    Generates an AI-powered Markdown analysis of the current market
    based on index data and macro news. Uploads result as PDF to Cloudflare R2.

    The AI is strictly constrained to trend probability analysis.
    No buy/sell recommendations are produced (FR-AI-002).
    """
    try:
        market_data = market_service.get_market_overview()
        macro_news = await news_service.get_news_by_category(db, category="macro", limit=10)
        markdown = await ai_orchestrator_service.analyze_market_overview(
            market_data=market_data, macro_news=macro_news
        )

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        filename = f"overview_{date_str}.pdf"
        pdf_url = await _upload_report_to_r2(markdown, filename)

        return AnalysisResponse(
            status="success",
            markdown_content=markdown,
            pdf_url=pdf_url,
        )
    except Exception as e:
        logger.exception("Error in /api/analyze/overview")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detail", response_model=AnalysisResponse, summary="AI Detail Report for a Symbol")
async def analyze_detail(
    request: DetailAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates an AI-powered detail analysis for a single watchlist symbol.
    Fetches OHLCV data and symbol-specific news, then sends to AI.
    Uploads result as PDF to Cloudflare R2.

    The AI is strictly constrained to trend probability analysis.
    No buy/sell recommendations are produced (FR-AI-002).
    """
    symbol = request.symbol.upper()
    try:
        ohlcv = market_service.get_stock_history(symbol=symbol)
        symbol_news = await news_service.get_news_by_symbol(db, symbol=symbol, limit=8)

        markdown = await ai_orchestrator_service.analyze_stock_detail(
            symbol=symbol,
            ohlcv_summary=ohlcv,
            news_articles=symbol_news,
        )

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        filename = f"detail_{symbol}_{date_str}.pdf"
        pdf_url = await _upload_report_to_r2(markdown, filename)

        return AnalysisResponse(
            status="success",
            markdown_content=markdown,
            pdf_url=pdf_url,
        )
    except Exception as e:
        logger.exception("Error in /api/analyze/detail for symbol %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))
