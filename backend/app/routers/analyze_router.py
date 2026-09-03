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
from datetime import datetime, timezone, timedelta

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.infra.storage import S3StorageProvider
from app.models import GeneratedReport, RiskAnalysisCache
from app.schemas import AnalysisResponse, DetailAnalysisRequest
from app.services import ai_orchestrator_service, market_service, news_service
from app.services.risk_scoring import RiskScoringService
from app.services.fundamental_indicators import fundamental_service
from sqlalchemy import select
import json
import pandas as pd

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

REASON_TRANSLATIONS = {
    "MOM_BEAR_DIV": "Phân kỳ giảm giá RSI/MACD (Động lượng suy kiệt khi giá cố tạo đỉnh)",
    "RSI_OVERBOUGHT": "Quá mua RSI > 70 (Áp lực điều chỉnh chốt lời ngắn hạn)",
    "VOLUME_CLIMAX_UPPER_WICK": "Bùng nổ Vol kèm râu nến trên (Áp lực bán chốt lời mạnh vùng giá cao)",
    "PARTIAL_DISTRIBUTION": "Dấu hiệu phân phối từng phần (Thanh khoản tăng kèm lực bán xuất hiện)",
    "PRICE_EXTREME_HIGH_VOLATILITY": "Giá ở cực trị biến động (Z-Score & ATR tăng vọt so với bình quân)",
    "ELEVATED_VOLATILITY": "Biến động giá tăng cao bất thường",
    "STRUCTURE_DOWN": "Gãy cấu trúc tăng giá ngắn hạn (Đóng dưới hỗ trợ kèm khối lượng lớn)",
    "WEAK_REL_STRENGTH": "Hiệu suất giá yếu hơn thị trường chung (Underperform VN-Index)",
    "EXCHANGE_LIMIT_HIT_SUPPRESSED": "Chạm biên độ trần/sàn (Tạm ngưng phân tích cơ học do nghẽn thanh khoản)",
    "EXCHANGE_LIMIT_HIT_CONTEXT": "Chạm biên độ giá trần/sàn theo quy định sàn",
    "MOM_BULL_DIV": "Phân kỳ tăng giá RSI (Động lượng phục hồi dù giá tạo đáy mới)",
    "RSI_OVERSOLD": "Quá bán RSI < 30 (Lực bán suy kiệt, vùng quá bán sâu)",
    "CAPITULATION_VOLUME_LOWER_WICK": "Nến rút chân cạn cung kèm thanh khoản lớn (Lực cầu hấp thụ vùng đáy)",
    "HIGH_SELLING_VOLUME": "Khối lượng bán cao đột biến trong phiên giảm",
    "PANIC_VOLATILITY": "Biến động bán tháo hoảng loạn (Mức giảm thuộc 5% phiên tồi tệ nhất)",
    "STRUCTURE_UP": "Hồi phục cấu trúc ngắn hạn (Đóng vượt đỉnh nến giảm mạnh liền trước)",
    "STRONG_REL_STRENGTH": "Hiệu suất giá vượt trội so với thị trường (Outperform VN-Index)",
    "MFI_DISTRIBUTION_CONFIRM": "Dòng tiền MFI xác nhận phân phối",
    "MFI_ACCUMULATION_CONFIRM": "Dòng tiền MFI xác nhận tích lũy",
}

@router.get("/risk/{symbol}", summary="Get Risk & Fundamental Analysis")
async def get_risk_analysis(
    symbol: str, 
    force_refresh: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves or calculates Piotroski F-Score (full 9 criteria) and Technical Risk Scores (BUY_RISK/SELL_RISK).
    Caches the result in the database per symbol per day.
    """
    symbol = symbol.upper()
    today = datetime.now(timezone.utc).date()
    
    if not force_refresh:
        stmt = select(RiskAnalysisCache).where(
            RiskAnalysisCache.symbol == symbol,
            RiskAnalysisCache.as_of_date >= today
        )
        res = await db.execute(stmt)
        cached = res.scalar_one_or_none()
        
        if cached and cached.result_json:
            try:
                cached_data = json.loads(cached.result_json)
                # If cached data already has new rich details, return it
                if "f_score_details" in cached_data and "valuation" in cached_data:
                    return cached_data
            except Exception:
                pass
            
    # Cache miss or force_refresh or legacy cache format: Calculate
    try:
        # 1. Fundamental — full 9-point details & valuation ratios
        f_details = fundamental_service.calculate_f_score_details(symbol)
        f_score = f_details.get("f_score")
        valuation = fundamental_service.get_valuation_metrics(symbol)

        # 2. Technical — fetch OHLCV for the target symbol (~400 days)
        start_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        df = market_service._fetch_historical_ohlcv(
            symbol=symbol, start_date=start_date, end_date=end_date
        )

        if df is None or df.empty:
            dates = pd.date_range(end=datetime.today(), periods=100)
            df = pd.DataFrame({
                'time': dates,
                'open': [100] * 100, 'high': [105] * 100,
                'low': [95] * 100, 'close': [102] * 100,
                'volume': [200_000] * 100,
            })
            df.set_index('time', inplace=True)
        else:
            df.rename(columns=str.lower, inplace=True)
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)

        # 2b. Fetch VN-Index as benchmark for REL_STRENGTH computation
        benchmark_df = None
        try:
            vnindex_raw = market_service._fetch_historical_ohlcv(
                symbol="VNINDEX", start_date=start_date, end_date=end_date
            )
            if vnindex_raw is not None and not vnindex_raw.empty:
                vnindex_raw.rename(columns=str.lower, inplace=True)
                vnindex_raw['time'] = pd.to_datetime(vnindex_raw['time'])
                vnindex_raw.set_index('time', inplace=True)
                benchmark_df = vnindex_raw
        except Exception as bench_err:
            logger.warning("Could not fetch VNINDEX benchmark: %s", bench_err)

        risk_service = RiskScoringService()
        risk_res = risk_service.evaluate(df, benchmark_df=benchmark_df)

        # 3. Intelligent Multi-Factor Decision Support
        # Critical Rule: Never recommend "BUY" when fundamental quality is genuinely distressed.
        # Distinguish high-profitability growth giants (ROE > 15%, ROA > 7%) whose F-Score is temporarily
        # constrained by heavy capex/asset expansion, from truly distressed companies (ROE/ROA <= 0).
        buy_score = risk_res['buy_score']
        sell_score = risk_res['sell_score']
        roe_val = valuation.get('roe') if valuation else None
        roa_pct = f_details.get('raw_metrics', {}).get('roa_pct', 0.0)

        is_high_quality_growth = (roe_val is not None and roe_val >= 15.0) or (roa_pct >= 7.0)

        if f_score is not None and f_score <= 3:
            if is_high_quality_growth:
                scenario_msg = f"THEO DÕI TÍCH LŨY (Hiệu suất sinh lời cao ROE {roe_val}%, F-Score {f_score}/9 do tốc độ tăng tài sản mở rộng — Vùng kỹ thuật an toàn)"
            else:
                scenario_msg = f"CẢNH BÁO: RỦI RO NỘI TẠI CAO (Chất lượng tài chính rất yếu F-Score {f_score}/9 — Tuyệt đối không mở vị thế mua dài hạn)"
        elif f_score is not None and f_score <= 4 and buy_score <= 40:
            if is_high_quality_growth:
                scenario_msg = f"THEO DÕI NẮM GIỮ (Cơ bản đầu ngành ROE {roe_val}%, biến động kỹ thuật cân bằng)"
            else:
                scenario_msg = f"THẬN TRỌNG QUAN SÁT (Sức khỏe tài chính dưới trung bình F-Score {f_score}/9 — Rủi ro nội tại tiềm ẩn, chỉ xem xét lướt sóng có kỷ luật)"
        elif buy_score >= 75:
            scenario_msg = "GIẢM TỶ TRỌNG / KHÔNG MUA ĐUỔI (Rủi ro mua đuổi ở mức CAO: Giá tiệm cận cực trị hoặc có tín hiệu phân phối mạnh)"
        elif sell_score >= 75:
            scenario_msg = "HẠN CHẾ BÁN ĐUỔI (Rủi ro bán cạn cung CAO: Dễ rơi vào nhịp rũ bỏ trước khi hồi phục kỹ thuật)"
        elif f_score is not None and f_score >= 7 and sell_score >= 60:
            scenario_msg = f"THEO DÕI GOM TÍCH LŨY (Doanh nghiệp chất lượng cao F-Score {f_score}/9 + Đang ở vùng bán cạn cung tiềm năng)"
        elif (f_score is not None and f_score >= 6 and buy_score <= 40) or (is_high_quality_growth and buy_score <= 35):
            f_label = f"F-Score {f_score}/9" if f_score is not None else ""
            scenario_msg = f"CÂN NHẮC TÍCH LŨY / MỞ MUA AN TOÀN (Cơ bản vững mạnh {f_label} + Rủi ro mua đuổi kỹ thuật thấp)"
        elif buy_score <= 40 and sell_score <= 40:
            f_str = f"F-Score {f_score}/9" if f_score is not None else "Cơ bản chưa đủ dữ liệu"
            scenario_msg = f"THEO DÕI TRUNG LẬP ({f_str} — Biến động kỹ thuật cân bằng, chờ xác nhận xu hướng rõ ràng)"
        else:
            scenario_msg = "NẮM GIỮ QUAN SÁT (Không xuất hiện cảnh báo rủi ro cực đoan)"

        # Translate reason codes
        buy_reasons_raw = risk_res.get('buy_reasons', [])
        sell_reasons_raw = risk_res.get('sell_reasons', [])
        buy_reasons_detail = [
            {"code": r, "title": REASON_TRANSLATIONS.get(r, r)} for r in buy_reasons_raw
        ]
        sell_reasons_detail = [
            {"code": r, "title": REASON_TRANSLATIONS.get(r, r)} for r in sell_reasons_raw
        ]

        final_result = {
            "symbol": symbol,
            "as_of_date": today.strftime('%Y-%m-%d'),
            "f_score": f_score,
            "buy_score": buy_score,
            "sell_score": sell_score,
            "buy_level": risk_res['buy_level'],
            "sell_level": risk_res['sell_level'],
            "exchange_limit_hit": risk_res.get('exchange_limit_hit', False),
            "scenario": scenario_msg,
            "valuation": valuation,
            "f_score_details": f_details,
            "details": {
                "buy_reasons": buy_reasons_raw,
                "sell_reasons": sell_reasons_raw,
                "buy_reasons_detail": buy_reasons_detail,
                "sell_reasons_detail": sell_reasons_detail,
                "buy_components": risk_res.get('buy_components', {}),
                "sell_components": risk_res.get('sell_components', {}),
            },
        }

        # 4. Persist to RiskAnalysisCache DB
        cached = await db.get(RiskAnalysisCache, symbol)
        if not cached:
            cached = RiskAnalysisCache(symbol=symbol, as_of_date=today)
            db.add(cached)

        cached.f_score = f_score
        cached.buy_score = buy_score
        cached.sell_score = sell_score
        cached.result_json = json.dumps(final_result, ensure_ascii=False)
        cached.as_of_date = today

        await db.commit()

        return final_result
    except Exception as e:
        logger.exception("Error in /api/analyze/risk for symbol %s", symbol)
        raise HTTPException(status_code=500, detail=str(e))


