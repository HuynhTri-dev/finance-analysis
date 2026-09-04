"""
name: finance_analysis_router.py
description: FastAPI router providing endpoints for BCTC PDF upload, structured
             financial metric extraction, multi-factor comprehensive risk reporting,
             and grounded document Q&A according to the BDA specifications.
             Persists extracted Markdown files to Cloudflare R2 storage for durable,
             continuous retrieval during interactive chat sessions.
"""

from __future__ import annotations

import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.infra.l1_cache import doc_session_cache
from app.infra.storage import S3StorageProvider
from app.models import BCTCDocument, GeneratedReport
from app.routers.analyze_router import _upload_report_to_storage, get_risk_analysis
from app.schemas.finance_analysis_schema import (
    BCTCUploadResponse,
    ChatDocumentRequest,
    ChatDocumentResponse,
    ComprehensiveReportRequest,
    ComprehensiveReportResponse,
)
from app.services import ai_orchestrator_service
from app.services.pdf_processor import bctc_document_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/finance", tags=["Finance Analysis"])


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:
    """Dependency: yields an async database session."""
    async with async_session_maker() as session:
        yield session


# ---------------------------------------------------------------------------
# Storage Helpers: Cloudflare R2 Upload & Download for BCTC Markdown
# ---------------------------------------------------------------------------

async def _save_markdown_to_storage(markdown_text: str, doc_id: str, filename: str) -> tuple[str, str | None]:
    """
    Upload markdown text bytes to Cloudflare R2 object storage with local filesystem fallback.

    Args:
        markdown_text: Extracted Markdown content of the BCTC.
        doc_id: Unique document UUID.
        filename: Original PDF filename for reference.

    Returns:
        Tuple of (storage_path, public_or_presigned_url).
    """
    object_name = f"bctc_markdown/{doc_id}.md"
    url = None
    md_bytes = markdown_text.encode("utf-8")

    # 1. Try Cloudflare R2 (S3-compatible)
    try:
        provider = S3StorageProvider()
        if provider.settings.r2_endpoint_url and provider.settings.bucket_name:
            await provider.upload_file(
                file_data=md_bytes,
                object_name=object_name,
                content_type="text/markdown; charset=utf-8",
            )
            url = await provider.get_file_url(object_name, expires_in=604800)
            logger.info("[Storage] Uploaded Markdown to Cloudflare R2: %s", object_name)
            return object_name, url
    except Exception as err:
        logger.warning("[Storage] Cloudflare R2 upload failed for %s, using local fallback: %s", object_name, err)

    # 2. Local Fallback Static Storage
    try:
        static_dir = Path(__file__).resolve().parent.parent.parent / "static" / "bctc_markdown"
        static_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        static_dir = Path(tempfile.gettempdir()) / "static" / "bctc_markdown"
        static_dir.mkdir(parents=True, exist_ok=True)

    local_file = static_dir / f"{doc_id}.md"
    local_file.write_bytes(md_bytes)
    url = f"/static/bctc_markdown/{doc_id}.md"
    storage_path = f"local://static/bctc_markdown/{doc_id}.md"
    logger.info("[Storage] Saved Markdown to local static fallback: %s", storage_path)
    return storage_path, url


async def _load_markdown_from_storage(storage_path: str, doc_id: str) -> str | None:
    """
    Retrieve markdown text from Cloudflare R2 storage or local static filesystem.

    Args:
        storage_path: Stored object key or local URI.
        doc_id: Unique document UUID.

    Returns:
        Decoded Markdown string, or None if not found.
    """
    # 1. Local filesystem check
    if storage_path.startswith("local://"):
        rel_path = storage_path.removeprefix("local://")
        local_file = Path(__file__).resolve().parent.parent.parent / rel_path
        if local_file.exists():
            return local_file.read_text(encoding="utf-8")
        tmp_file = Path(tempfile.gettempdir()) / rel_path
        if tmp_file.exists():
            return tmp_file.read_text(encoding="utf-8")

    # 2. Cloudflare R2 download
    try:
        provider = S3StorageProvider()
        if provider.settings.r2_endpoint_url and provider.settings.bucket_name:
            clean_key = storage_path.removeprefix("r2://")
            if not clean_key.startswith("bctc_markdown/"):
                clean_key = f"bctc_markdown/{doc_id}.md"
            data_bytes = await provider.download_file(clean_key)
            logger.info("[Storage] Loaded Markdown from Cloudflare R2: %s", clean_key)
            return data_bytes.decode("utf-8")
    except Exception as r2_err:
        logger.warning("[Storage] Cloudflare R2 download error for %s: %s", storage_path, r2_err)

    # 3. Direct local static check
    static_file = Path(__file__).resolve().parent.parent.parent / "static" / "bctc_markdown" / f"{doc_id}.md"
    if static_file.exists():
        return static_file.read_text(encoding="utf-8")

    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/upload-bctc",
    response_model=BCTCUploadResponse,
    summary="Upload & Parse PDF Financial Statements (BCTC)",
)
async def upload_bctc(
    file: UploadFile = File(..., description="Corporate financial report PDF file (BCTC, max 50MB)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts an uploaded BCTC PDF, converts layout to structured Markdown preserving
    tables, saves the Markdown artifact to Cloudflare R2 / Local storage for durable
    chat access, extracts key metrics via LLM, and caches the document in memory.
    """
    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Định dạng file không hợp lệ. Hệ thống chỉ chấp nhận file định dạng PDF.",
        )

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="File PDF rỗng (0 bytes).")

        # 1. Parse PDF to Markdown
        parsed = bctc_document_processor.parse_pdf_to_markdown(file_bytes, filename=filename)
        doc_id = parsed["doc_id"]
        markdown_text = parsed["markdown"]

        # 2. Upload Markdown to Cloudflare R2 (or local fallback)
        storage_path, markdown_url = await _save_markdown_to_storage(markdown_text, doc_id, filename)

        # 3. Extract Fundamental Metrics via LLM
        extracted_metrics = await ai_orchestrator_service.extract_financial_metrics_from_bctc(
            bctc_markdown=markdown_text,
            symbol=None,
        )

        # 4. Persist Record to Database
        doc_record = BCTCDocument(
            id=doc_id,
            symbol=extracted_metrics.symbol if extracted_metrics else None,
            filename=filename,
            storage_path=storage_path,
            markdown_url=markdown_url,
            page_count=parsed["page_count"],
            tables_found=parsed["tables_found"],
            extracted_metrics_json=extracted_metrics.model_dump_json() if extracted_metrics else None,
            created_at=datetime.now(timezone.utc),
        )
        try:
            db.add(doc_record)
            await db.commit()
        except Exception as db_err:
            logger.warning("[Finance Router] Could not save BCTCDocument metadata to DB: %s", db_err)


        # 5. Store in Document Session Cache (TTL 1 hour)
        doc_session_cache.set(
            doc_id,
            {
                "doc_id": doc_id,
                "filename": filename,
                "markdown": markdown_text,
                "storage_path": storage_path,
                "markdown_url": markdown_url,
                "page_count": parsed["page_count"],
                "tables_found": parsed["tables_found"],
                "extracted_metrics": extracted_metrics,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            },
            ttl=3600.0,
        )

        # Truncate summary for initial response payload
        preview_summary = (
            markdown_text[:3500] + "\n\n...(Nội dung tài liệu đã được lưu trữ an toàn trên Cloudflare R2)..."
            if len(markdown_text) > 3500
            else markdown_text
        )

        return BCTCUploadResponse(
            status="success",
            doc_id=doc_id,
            filename=filename,
            page_count=parsed["page_count"],
            tables_found=parsed["tables_found"],
            extracted_metrics=extracted_metrics,
            summary_markdown=preview_summary,
            markdown_url=markdown_url,
            storage_path=storage_path,
        )

    except ValueError as val_err:
        logger.warning("[Finance Router] Validation/Parsing error on %s: %s", filename, val_err)
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        logger.exception("[Finance Router] Unexpected error uploading BCTC %s", filename)
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi xử lý PDF: {exc}")


@router.get(
    "/risk/{symbol}",
    summary="Get Technical Risk & Fundamental F-Score",
)
async def get_symbol_risk(
    symbol: str,
    force_refresh: bool = Query(False, description="Bỏ qua cache EOD trong ngày và tính toán lại"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves or calculates Piotroski F-Score (9 criteria) and Technical Risk Scores (BUY_RISK / SELL_RISK).
    Reuses the database EOD cache from RiskAnalysisCache.
    """
    return await get_risk_analysis(symbol=symbol, force_refresh=force_refresh, db=db)


@router.post(
    "/comprehensive-report",
    response_model=ComprehensiveReportResponse,
    summary="Generate Multi-Factor 3-Part Financial Report",
)
async def generate_comprehensive_report(
    request: ComprehensiveReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Synthesizes a 3-part comprehensive financial analysis combining Fundamental
    health (F-Score + BCTC) and Technical Risk Scoring (BUY_RISK / SELL_RISK).
    Optionally exports the report as a PDF artifact to Cloudflare R2 / Local storage.
    """
    symbol = request.symbol.upper()

    try:
        # 1. Fetch Technical & Fundamental Risk Data
        risk_data = await get_risk_analysis(symbol=symbol, force_refresh=False, db=db)

        # 2. Retrieve Uploaded BCTC context: check cache first, then Cloudflare R2 / DB
        bctc_context = None
        if request.doc_id:
            session_data = doc_session_cache.get(request.doc_id)
            md_text = session_data.get("markdown", "") if session_data else ""

            # Cache miss: load from DB and Cloudflare storage
            if not md_text:
                stmt = select(BCTCDocument).where(BCTCDocument.id == request.doc_id)
                res = await db.execute(stmt)
                doc_record = res.scalar_one_or_none()
                if doc_record:
                    md_text = await _load_markdown_from_storage(doc_record.storage_path, doc_record.id) or ""

            if md_text:
                bctc_context = {
                    "filename": session_data.get("filename") if session_data else "bctc.pdf",
                    "extracted_metrics": session_data.get("extracted_metrics") if session_data else None,
                    "markdown_excerpt": md_text[:4000],
                }

        # 3. Generate 3-Part AI Report
        report_markdown = await ai_orchestrator_service.generate_comprehensive_analysis_report(
            symbol=symbol,
            risk_cache=risk_data,
            bctc_summary=bctc_context,
        )

        pdf_url = None
        # 4. Optional PDF Render & Artifact Storage
        if request.include_pdf_export:
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
            filename = f"comprehensive_{symbol}_{date_str}.pdf"

            # Generate correlation chart image
            chart_bytes = None
            try:
                from app.services.pdf_generator_service import generate_correlation_chart_image
                from app.services.market_service import market_service
                from datetime import timedelta

                start_date = (datetime.now() - timedelta(days=150)).strftime("%Y-%m-%d")
                end_date = datetime.now().strftime("%Y-%m-%d")
                stock_df = market_service._fetch_historical_ohlcv(symbol=symbol, start_date=start_date, end_date=end_date)
                benchmark_df = market_service._fetch_historical_ohlcv(symbol="VNINDEX", start_date=start_date, end_date=end_date)

                chart_bytes = generate_correlation_chart_image(
                    symbol=symbol,
                    stock_df=stock_df,
                    benchmark_df=benchmark_df,
                    buy_score=risk_data.get("buy_score", 50),
                    sell_score=risk_data.get("sell_score", 50),
                    f_score=risk_data.get("f_score"),
                )
            except Exception as chart_err:
                logger.warning("[Finance Router] Could not generate correlation chart for %s: %s", symbol, chart_err)

            upload_meta = await _upload_report_to_storage(
                content=report_markdown,
                filename=filename,
                symbol=symbol,
                chart_image_bytes=chart_bytes,
                risk_data=risk_data,
            )

            if upload_meta:
                pdf_url = upload_meta.get("url")
                # Record to Database
                report_record = GeneratedReport(
                    title=f"Báo Cáo Toàn Cảnh: {symbol} ({datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')})",
                    report_type="ai_comprehensive",
                    symbol=symbol,
                    filename=upload_meta["filename"],
                    storage_path=upload_meta["object_name"],
                    pdf_url=upload_meta["url"],
                    size_kb=upload_meta["size_kb"],
                    created_at=datetime.now(timezone.utc),
                )
                db.add(report_record)
                await db.commit()

        return ComprehensiveReportResponse(
            status="success",
            symbol=symbol,
            report_markdown=report_markdown,
            f_score=risk_data.get("f_score"),
            buy_score=risk_data.get("buy_score"),
            sell_score=risk_data.get("sell_score"),
            buy_level=risk_data.get("buy_level"),
            sell_level=risk_data.get("sell_level"),
            scenario=risk_data.get("scenario"),
            pdf_url=pdf_url,
        )

    except Exception as e:
        logger.exception("[Finance Router] Error generating comprehensive report for %s", symbol)
        raise HTTPException(status_code=500, detail=f"Lỗi sinh báo cáo toàn cảnh: {e}")


@router.post(
    "/chat",
    response_model=ChatDocumentResponse,
    summary="Interactive Grounded Q&A on Uploaded BCTC",
)
async def chat_with_bctc(
    request: ChatDocumentRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Allows the user to ask specific questions about an uploaded financial statement.
    Answers are grounded strictly on BCTC content with anti-hallucination guardrails.
    Reads from fast in-memory L1 cache, or retrieves directly from Cloudflare R2
    storage if session expired or server was restarted.
    """
    bctc_markdown = None
    filename = "bctc.pdf"

    # Step 1: Check in-memory L1 cache
    session_data = doc_session_cache.get(request.doc_id)
    if session_data and session_data.get("markdown"):
        bctc_markdown = session_data["markdown"]
        filename = session_data.get("filename", filename)

    # Step 2: If cache miss, read from Database & Cloudflare R2 / Storage
    if not bctc_markdown:
        logger.info("[Chat] Cache miss for doc_id %s, re-reading from Cloudflare storage...", request.doc_id)
        try:
            stmt = select(BCTCDocument).where(BCTCDocument.id == request.doc_id)
            res = await db.execute(stmt)
            doc_record = res.scalar_one_or_none()

            if doc_record:
                bctc_markdown = await _load_markdown_from_storage(doc_record.storage_path, doc_record.id)
                filename = doc_record.filename
        except Exception as db_err:
            logger.warning("[Chat] Database lookup failed (%s), attempting direct storage lookup", db_err)

        # If not found in DB record, attempt direct storage key by doc_id
        if not bctc_markdown:
            bctc_markdown = await _load_markdown_from_storage(f"bctc_markdown/{request.doc_id}.md", request.doc_id)


        # Repopulate L1 cache so subsequent conversation turns are instantaneous
        if bctc_markdown:
            doc_session_cache.set(
                request.doc_id,
                {
                    "doc_id": request.doc_id,
                    "filename": filename,
                    "markdown": bctc_markdown,
                },
                ttl=3600.0,
            )

    if not bctc_markdown:
        raise HTTPException(
            status_code=404,
            detail="Tài liệu BCTC không tồn tại trên hệ thống lưu trữ Cloudflare/Local hoặc đã bị xóa. Vui lòng tải lại file BCTC.",
        )

    try:
        result = await ai_orchestrator_service.chat_with_document_context(
            query=request.query,
            bctc_markdown=bctc_markdown,
            chat_history=request.chat_history,
        )

        return ChatDocumentResponse(
            status="success",
            doc_id=request.doc_id,
            answer=result["answer"],
            citations=result.get("citations", []),
        )
    except Exception as e:
        logger.exception("[Finance Router] Error during chat for doc_id %s", request.doc_id)
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý câu hỏi: {e}")
