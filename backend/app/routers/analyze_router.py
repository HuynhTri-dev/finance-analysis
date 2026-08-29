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

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.infra.storage import S3StorageProvider
from app.models import GeneratedReport
from app.schemas import AnalysisResponse, DetailAnalysisRequest
from app.services import ai_orchestrator_service, market_service, news_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:
    """Dependency: yields an async database session."""
    async with async_session_maker() as session:
        yield session


# ---------------------------------------------------------------------------
# Helper: render markdown → PDF & upload to Cloudflare R2 / Local fallback
# ---------------------------------------------------------------------------

async def _upload_report_to_storage(content: str, filename: str) -> dict | None:
    """
    Convert markdown report to PDF bytes and upload to Cloudflare R2 / local fallback.
    Returns metadata dictionary or None on failure.

    Args:
        content:  Markdown string from AI.
        filename: Destination filename (e.g. "overview_20260828.pdf").

    Returns:
        Dict with url, object_name, size_kb, filename or None.
    """
    try:
        from fpdf import FPDF
        
        class PDF(FPDF):
            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", 'I', 8)
                self.cell(0, 10, f"Trang {self.page_no()}", align="C")
            
        pdf = PDF()
        
        # Load Unicode fonts
        fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
        font_regular = str(fonts_dir / "Arial.ttf")
        font_bold = str(fonts_dir / "Arial-Bold.ttf")
        font_italic = str(fonts_dir / "Arial-Italic.ttf")

        if Path(font_regular).exists():
            pdf.add_font("Arial", "", font_regular)
            pdf.add_font("Arial", "B", font_bold if Path(font_bold).exists() else font_regular)
            pdf.add_font("Arial", "I", font_italic if Path(font_italic).exists() else font_regular)
            font_family = "Arial"
        else:
            font_family = "Helvetica"
            content = content.encode("ascii", "ignore").decode("ascii")

        pdf.add_page()
        pdf.set_font(font_family, size=11)
        pdf.multi_cell(0, 6, text=content)
        pdf_bytes = bytes(pdf.output())
        size_kb = round(len(pdf_bytes) / 1024, 1)

        # Upload to R2
        object_name = f"reports/{filename}"
        url = None
        try:
            provider = S3StorageProvider()
            if provider.settings.r2_endpoint_url and provider.settings.bucket_name:
                await provider.upload_file(
                    file_data=pdf_bytes,
                    object_name=object_name,
                    content_type="application/pdf",
                )
                url = await provider.get_file_url(object_name, expires_in=604800)
        except Exception as storage_err:
            logger.warning("R2 upload failed, falling back to local static storage: %s", storage_err)

        if not url:
            # Fallback to local static file
            static_dir = Path(__file__).resolve().parent.parent.parent / "static" / "reports"
            static_dir.mkdir(parents=True, exist_ok=True)
            local_file_path = static_dir / filename
            local_file_path.write_bytes(pdf_bytes)
            url = f"http://localhost:8001/static/reports/{filename}"
            object_name = f"local://static/reports/{filename}"

        return {
            "url": url,
            "object_name": object_name,
            "size_kb": size_kb,
            "filename": filename,
        }
    except Exception as e:
        logger.warning("Failed to render/upload AI report: %s", e)
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/overview", response_model=AnalysisResponse, summary="AI Market Overview Report")
async def analyze_overview(db: AsyncSession = Depends(get_db)):
    """
    Generates an AI-powered Markdown analysis of the current market
    based on index data and macro news. Uploads result as PDF to Cloudflare R2
    and persists metadata into Neon PostgreSQL database.
    """
    try:
        market_data = market_service.get_market_overview()
        macro_news = await news_service.get_news_by_category(db, category="macro", limit=10)
        markdown = await ai_orchestrator_service.analyze_market_overview(
            market_data=market_data, macro_news=macro_news
        )

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        filename = f"overview_{date_str}.pdf"
        upload_meta = await _upload_report_to_storage(markdown, filename)

        pdf_url = upload_meta.get("url") if upload_meta else None

        # Save record to Neon PostgreSQL
        if upload_meta:
            report_record = GeneratedReport(
                title=f"Phân Tích AI: Toàn Cảnh Thị Trường ({datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')})",
                report_type="ai_overview",
                symbol=None,
                filename=upload_meta["filename"],
                storage_path=upload_meta["object_name"],
                pdf_url=upload_meta["url"],
                size_kb=upload_meta["size_kb"],
                created_at=datetime.now(timezone.utc),
            )
            db.add(report_record)
            await db.commit()

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
    Uploads result as PDF to Cloudflare R2 and persists into Neon database.
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
        upload_meta = await _upload_report_to_storage(markdown, filename)

        pdf_url = upload_meta.get("url") if upload_meta else None

        # Save record to Neon PostgreSQL
        if upload_meta:
            report_record = GeneratedReport(
                title=f"Phân Tích AI: {symbol} ({datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')})",
                report_type="ai_detail",
                symbol=symbol,
                filename=upload_meta["filename"],
                storage_path=upload_meta["object_name"],
                pdf_url=upload_meta["url"],
                size_kb=upload_meta["size_kb"],
                created_at=datetime.now(timezone.utc),
            )
            db.add(report_record)
            await db.commit()

        return AnalysisResponse(
            status="success",
            markdown_content=markdown,
            pdf_url=pdf_url,
        )
    except Exception as e:
        logger.exception("Error in /api/analyze/detail for symbol %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))
