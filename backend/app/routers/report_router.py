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
    Generates a quick PDF summary for a stock symbol with correlation charts and styled headers.
    """
    symbol = symbol.upper()
    try:
        from app.routers.analyze_router import get_risk_analysis, _upload_report_to_storage
        from app.services.pdf_generator_service import generate_correlation_chart_image
        from datetime import timedelta

        # 1. Fetch risk data & OHLCV history
        risk_data = await get_risk_analysis(symbol=symbol, force_refresh=False, db=db)

        start_date = (datetime.now() - timedelta(days=150)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        stock_df = market_service._fetch_historical_ohlcv(symbol=symbol, start_date=start_date, end_date=end_date)
        benchmark_df = market_service._fetch_historical_ohlcv(symbol="VNINDEX", start_date=start_date, end_date=end_date)

        # Generate chart bytes
        chart_bytes = generate_correlation_chart_image(
            symbol=symbol,
            stock_df=stock_df,
            benchmark_df=benchmark_df,
            buy_score=risk_data.get("buy_score", 50),
            sell_score=risk_data.get("sell_score", 50),
            f_score=risk_data.get("f_score"),
        )

        # 2. Build structured Markdown summary for quick report
        ohlcv = market_service.get_stock_history(symbol=symbol)
        symbol_news = await news_service.get_news_by_symbol(db, symbol=symbol, limit=8)

        records = ohlcv.get("records", [])
        latest_info = "• Chưa có dữ liệu giao dịch chi tiết."
        if records:
            latest = records[-1]
            date_str = latest.get("time", "")
            close_val = f"{latest.get('close', 0):,}" if isinstance(latest.get('close'), (int, float)) else str(latest.get('close'))
            vol_val = f"{latest.get('volume', 0):,}" if isinstance(latest.get('volume'), (int, float)) else str(latest.get('volume'))
            high_val = f"{latest.get('high', 0):,}" if isinstance(latest.get('high'), (int, float)) else str(latest.get('high'))
            low_val = f"{latest.get('low', 0):,}" if isinstance(latest.get('low'), (int, float)) else str(latest.get('low'))
            latest_info = f"• Ngày giao dịch: {date_str}\n• Giá đóng cửa: {close_val} VND\n• Khối lượng: {vol_val}\n• Biên độ Cao / Thấp: {high_val} / {low_val} VND"

        f_score_val = risk_data.get("f_score")
        f_str = f"{f_score_val}/9" if f_score_val is not None else "Đang cập nhật"
        scenario_str = risk_data.get("scenario", "Quan sát thị trường")

        news_txt_list = []
        if symbol_news:
            for i, article in enumerate(symbol_news[:5], 1):
                t = article.get("title", "")
                s = article.get("source", "")
                news_txt_list.append(f"- {i}. **{t}** ({s})")
        news_section = "\n".join(news_txt_list) if news_txt_list else "- Chưa có tin tức nổi bật gần đây."

        quick_markdown = f"""# BÁO CÁO TỔNG HỢP CỔ PHIẾU: {symbol}

## PHẦN 1: THÔNG TIN GIAO DỊCH & RỦI RO THỊ TRƯỜNG
{latest_info}

- Piotroski F-Score: `{f_str}`
- Điểm Rủi ro Mua đuổi (BUY_RISK): `{risk_data.get('buy_score', 0)}/100` ({risk_data.get('buy_level', 'NORMAL')})
- Điểm Rủi ro Bán cạn (SELL_RISK): `{risk_data.get('sell_score', 0)}/100` ({risk_data.get('sell_level', 'NORMAL')})

> Kịch bản gợi ý: {scenario_str}

## PHẦN 2: TIN TỨC & SỰ KIỆN NỔI BẬT
{news_section}

---
*Báo cáo nhanh được tạo tự động bởi AI Finance Pro Engine.*
"""

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        filename = f"report_quick_{symbol}_{date_str}.pdf"
        upload_meta = await _upload_report_to_storage(
            content=quick_markdown,
            filename=filename,
            symbol=symbol,
            chart_image_bytes=chart_bytes,
            risk_data=risk_data,
        )

        url = upload_meta.get("url") if upload_meta else None
        size_kb = upload_meta.get("size_kb", 0) if upload_meta else 0
        object_name = upload_meta.get("object_name", f"reports/{filename}") if upload_meta else f"reports/{filename}"

        # 3. Save metadata into Neon DB
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

