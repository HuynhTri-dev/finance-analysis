"""
name: report_router.py
description: FastAPI router for generating and listing on-demand stock PDF reports.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.infra.storage import S3StorageProvider
from app.schemas import ReportListResponse, ReportResponse
from app.services import market_service, news_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["Report"])

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

@router.post("/symbol/{symbol}", response_model=ReportResponse, summary="Generate Quick PDF Report")
async def generate_symbol_report(symbol: str, db: AsyncSession = Depends(get_db)):
    symbol = symbol.upper()
    try:
        # Fetch data
        ohlcv = market_service.get_stock_history(symbol=symbol)
        symbol_news = await news_service.get_news_by_symbol(db, symbol=symbol, limit=10)
        
        from pathlib import Path
        fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
        font_regular = str(fonts_dir / "Arial.ttf")
        font_bold = str(fonts_dir / "Arial-Bold.ttf")
        font_italic = str(fonts_dir / "Arial-Italic.ttf")

        # Create PDF Template
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
        
        # Save & Upload
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        filename = f"report_quick_{symbol}_{date_str}.pdf"
        
        url = None
        try:
            provider = S3StorageProvider()
            if provider.settings.r2_endpoint_url and provider.settings.bucket_name:
                object_name = f"reports/{filename}"
                await provider.upload_file(
                    file_data=pdf_bytes,
                    object_name=object_name,
                    content_type="application/pdf",
                )
                url = await provider.get_file_url(object_name, expires_in=604800)
        except Exception as storage_err:
            logger.warning(f"R2 upload failed, falling back to local static storage: {storage_err}")

        if not url:
            # Fallback to local static file
            static_dir = Path(__file__).resolve().parent.parent.parent / "static" / "reports"
            static_dir.mkdir(parents=True, exist_ok=True)
            local_file_path = static_dir / filename
            local_file_path.write_bytes(pdf_bytes)
            url = f"http://localhost:8001/static/reports/{filename}"
        
        return ReportResponse(status="success", pdf_url=url)
    except Exception as e:
        logger.exception(f"Error generating quick report for {symbol}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ReportListResponse, summary="List Generated PDF Reports")
async def list_reports():
    """
    Retrieve generated PDF reports from Cloudflare R2 storage.
    Falls back to local static files if R2 is not configured or returns no items.
    """
    try:
        provider = S3StorageProvider()
        if provider.settings.r2_endpoint_url and provider.settings.bucket_name:
            r2_reports = await provider.list_files(prefix="reports/")
            if r2_reports:
                return {"reports": r2_reports}
    except Exception as err:
        logger.warning("Failed to fetch reports from Cloudflare R2, falling back to local: %s", err)

    # Fallback to local static storage
    static_dir = Path(__file__).resolve().parent.parent.parent / "static" / "reports"
    if not static_dir.exists():
        return {"reports": []}

    reports = []
    for p in sorted(static_dir.glob("*.pdf"), key=lambda f: f.stat().st_mtime, reverse=True):
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
        size_kb = round(p.stat().st_size / 1024, 1)
        reports.append({
            "filename": p.name,
            "url": f"http://localhost:8001/static/reports/{p.name}",
            "size_kb": size_kb,
            "created_at": mtime,
        })
    return {"reports": reports}

