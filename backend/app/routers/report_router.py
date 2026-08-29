"""
name: report_router.py
description: FastAPI router for generating and listing on-demand stock PDF reports.
             Saves report artifacts to Cloudflare R2 / Local Storage and persists
             metadata/URLs into PostgreSQL (Neon) database.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fpdf import FPDF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.infra.storage import S3StorageProvider
from app.models import GeneratedReport
from app.schemas import (
    ReportDeleteResponse,
    ReportListResponse,
    ReportResponse,
)
from app.services import market_service, news_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["Report"])


async def get_db() -> AsyncSession:
    """Dependency: yields an async database session."""
    async with async_session_maker() as session:
        yield session


@router.post("/symbol/{symbol}", response_model=ReportResponse, summary="Generate Quick PDF Report")
async def generate_symbol_report(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Generates a quick PDF summary for a stock symbol, uploads to storage,
    and records the resulting URL and metadata into Neon database.
    """
    symbol = symbol.upper()
    try:
        # 1. Fetch data
        ohlcv = market_service.get_stock_history(symbol=symbol)
        symbol_news = await news_service.get_news_by_symbol(db, symbol=symbol, limit=10)

        fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
        font_regular = str(fonts_dir / "Arial.ttf")
        font_bold = str(fonts_dir / "Arial-Bold.ttf")
        font_italic = str(fonts_dir / "Arial-Italic.ttf")

        # 2. Create PDF Template
        class PDF(FPDF):
            def header(self):
                self.set_font("Arial", 'B', 15)
                self.cell(0, 10, f"BÁO CÁO TỔNG HỢP CỔ PHIẾU: {symbol}", align="C", new_x="LMARGIN", new_y="NEXT")
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font("Arial", 'I', 8)
                self.cell(0, 10, f"Trang {self.page_no()}", align="C")

        pdf = PDF()

        # Load Unicode fonts before add_page()
        if Path(font_regular).exists():
            pdf.add_font("Arial", "", font_regular)
            pdf.add_font("Arial", "B", font_bold if Path(font_bold).exists() else font_regular)
            pdf.add_font("Arial", "I", font_italic if Path(font_italic).exists() else font_regular)
            font_family = "Arial"
        else:
            font_family = "Helvetica"

        pdf.add_page()
        pdf.set_font(font_family, size=12)

        # Section 1: Price History
        pdf.set_font(font_family, "B", size=14)
        pdf.cell(0, 10, "1. Thông tin giao dịch gần nhất", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, size=11)

        records = ohlcv.get("records", [])
        if records:
            latest = records[-1]
            date_str = latest.get("time", "")
            close_val = f"{latest.get('close', 0):,}" if isinstance(latest.get('close'), (int, float)) else str(latest.get('close'))
            vol_val = f"{latest.get('volume', 0):,}" if isinstance(latest.get('volume'), (int, float)) else str(latest.get('volume'))
            high_val = f"{latest.get('high', 0):,}" if isinstance(latest.get('high'), (int, float)) else str(latest.get('high'))
            low_val = f"{latest.get('low', 0):,}" if isinstance(latest.get('low'), (int, float)) else str(latest.get('low'))
            pdf.multi_cell(0, 6, text=f"Ngày: {date_str}\nGiá đóng cửa: {close_val}\nKhối lượng: {vol_val}\nCao/Thấp: {high_val} / {low_val}")
        else:
            pdf.multi_cell(0, 6, text="Không có dữ liệu giao dịch.")

        pdf.ln(5)

        # Section 2: News
        pdf.set_font(font_family, "B", size=14)
        pdf.cell(0, 10, "2. Tin tức liên quan", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_family, size=10)

        if symbol_news:
            for i, article in enumerate(symbol_news, 1):
                title = article.get('title', '')
                source = article.get('source', '')
                pub_date = article.get('published_at', '')
                if pub_date and hasattr(pub_date, "strftime"):
                    pub_date = pub_date.strftime("%Y-%m-%d %H:%M")

                pdf.multi_cell(0, 6, text=f"{i}. {title} ({source} - {pub_date})")
                pdf.ln(2)
        else:
            pdf.multi_cell(0, 6, text="Không có tin tức gần đây.")

        pdf_bytes = bytes(pdf.output())
        size_kb = round(len(pdf_bytes) / 1024, 1)

        # 3. Save & Upload
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        filename = f"report_quick_{symbol}_{date_str}.pdf"
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
            import tempfile
            try:
                static_dir = Path(__file__).resolve().parent.parent.parent / "static" / "reports"
                static_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                static_dir = Path(tempfile.gettempdir()) / "static" / "reports"
                static_dir.mkdir(parents=True, exist_ok=True)
            local_file_path = static_dir / filename
            local_file_path.write_bytes(pdf_bytes)
            url = f"/static/reports/{filename}"
            object_name = f"local://static/reports/{filename}"


        # 4. Save metadata and URL into Neon PostgreSQL
        report_record = GeneratedReport(
            title=f"Báo Cáo Nhanh: {symbol}",
            report_type="quick_symbol",
            symbol=symbol,
            filename=filename,
            storage_path=object_name,
            pdf_url=url,
            size_kb=size_kb,
            created_at=datetime.now(timezone.utc),
        )
        db.add(report_record)
        await db.commit()
        await db.refresh(report_record)

        return ReportResponse(
            status="success",
            pdf_url=url,
            id=report_record.id,
            title=report_record.title,
        )
    except Exception as e:
        logger.exception("Error generating quick report for %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ReportListResponse, summary="List Generated PDF Reports")
async def list_reports(db: AsyncSession = Depends(get_db)):
    """
    Retrieve generated PDF reports directly from PostgreSQL (Neon).
    Generates fresh presigned URLs for Cloudflare R2 files.
    Falls back to storage/static scanning if database has no records yet.
    """
    try:
        # 1. Query records from Neon database
        result = await db.execute(
            select(GeneratedReport).order_by(GeneratedReport.created_at.desc())
        )
        db_reports = list(result.scalars().all())

        if db_reports:
            provider = S3StorageProvider()
            use_r2 = bool(provider.settings.r2_endpoint_url and provider.settings.bucket_name)

            reports_data = []
            for r in db_reports:
                report_url = r.pdf_url
                # Refresh presigned URL if stored on R2
                if use_r2 and r.storage_path.startswith("reports/"):
                    try:
                        report_url = await provider.get_file_url(r.storage_path, expires_in=604800)
                    except Exception:
                        report_url = r.pdf_url

                reports_data.append({
                    "id": r.id,
                    "title": r.title,
                    "report_type": r.report_type,
                    "symbol": r.symbol,
                    "filename": r.filename,
                    "url": report_url,
                    "size_kb": r.size_kb,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                })
            return {"reports": reports_data}
    except Exception as db_err:
        logger.warning("Failed to query reports from database: %s", db_err)

    # 2. Fallback: Query Cloudflare R2 directly if DB returned nothing
    try:
        provider = S3StorageProvider()
        if provider.settings.r2_endpoint_url and provider.settings.bucket_name:
            r2_reports = await provider.list_files(prefix="reports/")
            if r2_reports:
                return {"reports": r2_reports}
    except Exception as err:
        logger.warning("Failed to fetch reports from Cloudflare R2, falling back to local: %s", err)

    # 3. Fallback: Local static storage
    import tempfile
    try:
        static_dir = Path(__file__).resolve().parent.parent.parent / "static" / "reports"
        if not static_dir.exists():
            static_dir = Path(tempfile.gettempdir()) / "static" / "reports"
    except OSError:
        static_dir = Path(tempfile.gettempdir()) / "static" / "reports"

    if not static_dir.exists():
        return {"reports": []}

    reports = []
    for p in sorted(static_dir.glob("*.pdf"), key=lambda f: f.stat().st_mtime, reverse=True):
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
        size_kb = round(p.stat().st_size / 1024, 1)
        reports.append({
            "filename": p.name,
            "url": f"/static/reports/{p.name}",
            "size_kb": size_kb,
            "created_at": mtime,
        })
    return {"reports": reports}



@router.delete("/{report_id}", response_model=ReportDeleteResponse, summary="Delete a Generated PDF Report")
async def delete_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes a generated report from PostgreSQL (Neon) and removes the physical
    file from Cloudflare R2 / local storage.
    """
    try:
        # Search by UUID or by filename
        result = await db.execute(
            select(GeneratedReport).where(
                (GeneratedReport.id == report_id) | (GeneratedReport.filename == report_id)
            )
        )
        report_record = result.scalar_one_or_none()

        provider = S3StorageProvider()
        if report_record:
            # 1. Delete from Cloudflare R2 / Local
            storage_path = report_record.storage_path
            if storage_path.startswith("reports/"):
                await provider.delete_file(storage_path)
            elif storage_path.startswith("local://"):
                local_path = Path(__file__).resolve().parent.parent.parent / storage_path.replace("local://", "")
                if local_path.exists():
                    local_path.unlink()

            # 2. Delete from database
            await db.delete(report_record)
            await db.commit()
            return ReportDeleteResponse(
                status="success",
                message=f"Báo cáo '{report_record.title}' đã được xoá thành công.",
                id=report_id,
            )
        else:
            # Fallback check if file exists in R2 or local static without DB record
            deleted_storage = False
            if provider.settings.r2_endpoint_url and provider.settings.bucket_name:
                key = report_id if report_id.startswith("reports/") else f"reports/{report_id}"
                deleted_storage = await provider.delete_file(key)

            import tempfile
            try:
                static_dir = Path(__file__).resolve().parent.parent.parent / "static" / "reports"
            except OSError:
                static_dir = Path(tempfile.gettempdir()) / "static" / "reports"
            local_file = static_dir / report_id
            if local_file.exists():
                local_file.unlink()
                deleted_storage = True


            if deleted_storage:
                return ReportDeleteResponse(
                    status="success",
                    message=f"File báo cáo '{report_id}' đã được xoá khỏi bộ nhớ.",
                    id=report_id,
                )

            raise HTTPException(status_code=404, detail=f"Không tìm thấy báo cáo '{report_id}'.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting report %s", report_id)
        raise HTTPException(status_code=500, detail=str(e))

