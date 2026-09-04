"""
name: ai_orchestrator_service.py
description: AI analysis service that orchestrates market data, technical risk scores,
             and parsed BCTC financial statements into structured reports and grounded Q&A
             via the LLMGateway infrastructure. Strictly enforces the no-advice constraint
             (BR-007) and evidence-based anti-hallucination guardrails (BR-008).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from app.infra.gateway.core import LLMGateway
from app.infra.gateway.types import GatewaySettings, ModelConfig, Platform
from app.infra.gw_config import build_gateway_settings
from app.schemas.finance_analysis_schema import FinancialMetricsExtracted

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Finance-specific fallback chain default
# ---------------------------------------------------------------------------
FINANCE_ANALYSIS_CHAIN: list[ModelConfig] = [
    ModelConfig(
        platform=Platform.OLLAMA,
        model_name="llama3",
        timeout_seconds=90,
        thinking_disabled=True,
    ),
    ModelConfig(
        platform=Platform.GEMINI,
        model_name="gemini-1.5-flash",
        timeout_seconds=60,
    ),
]

# ---------------------------------------------------------------------------
# Strict Guardrails (BR-007 & BR-008)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Bạn là một chuyên gia phân tích dữ liệu tài chính & thị trường chứng khoán độc lập, khách quan.
NGUYÊN TẮC BẮT BUỘC (GUARDRAILS):
1. Chỉ đưa ra nhận định xu hướng dựa HOÀN TOÀN vào dữ liệu BCTC và các chỉ báo kỹ thuật được cung cấp.
2. TUYỆT ĐỐI KHÔNG đưa ra lời khuyên/khuyến nghị mua, bán, nắm giữ cá nhân (No-advice constraint). Cấm các từ ngữ: "Tất tay", "Chắc chắn tăng", "Cam kết lợi nhuận".
3. Trình bày trung thực, bảo toàn nguyên vẹn số liệu gốc, không tự suy đoán (anti-hallucination).
4. Luôn kết thúc bằng tuyên bố miễn trừ trách nhiệm chuẩn:
"TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM: Báo cáo phân tích trên dựa trên số liệu định lượng khách quan và xác suất xu hướng thị trường, mang tính chất tham khảo học thuật, không phải lời khuyên đầu tư tài chính."
"""


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

async def analyze_market_overview(
    market_data: dict[str, Any],
    macro_news: list[dict[str, Any]],
) -> str:
    """
    Generate a Markdown market overview report using AI analysis.

    Args:
        market_data: Output from market_service.get_market_overview().
        macro_news:  List of macro news article dicts.

    Returns:
        AI-generated Markdown string.
    """
    indexes_txt = "\n".join(
        f"- {i['symbol']}: {i['close']} ({'+' if (i['change_pct'] or 0) >= 0 else ''}{i['change_pct']}%)"
        for i in market_data.get("indexes", [])
    )

    gainers_txt = "\n".join(
        f"- {g['symbol']}: +{g['change_pct']}%"
        for g in market_data.get("top_gainers", [])[:5]
    )

    news_txt = "\n".join(
        f"- [{a['source']}] {a['title']}"
        for a in (macro_news or [])[:10]
    )

    prompt = f"""{SYSTEM_PROMPT}

## DỮ LIỆU THỊ TRƯỜNG HÔM NAY

### Chỉ số
{indexes_txt or 'Không có dữ liệu'}

### Top 5 cổ phiếu tăng mạnh nhất
{gainers_txt or 'Không có dữ liệu'}

### Tin tức vĩ mô gần nhất
{news_txt or 'Không có tin tức'}

---
Hãy phân tích tổng quan thị trường và xu hướng có thể xảy ra trong phiên tiếp theo.
Trình bày dạng Markdown, ngắn gọn và khách quan.
"""
    return await _call_gateway(prompt, task_type="finance_report")


async def analyze_stock_detail(
    symbol: str,
    ohlcv_summary: dict[str, Any],
    news_articles: list[dict[str, Any]],
) -> str:
    """
    Generate a Markdown detail report for a single stock symbol.

    Args:
        symbol:        Stock ticker (e.g. "FPT").
        ohlcv_summary: Recent OHLCV records from market_service.
        news_articles: Recent news articles linked to this symbol.

    Returns:
        AI-generated Markdown analysis string.
    """
    records = ohlcv_summary.get("records", [])
    price_txt = "Không có dữ liệu giá."
    if records:
        latest = records[-1]
        price_txt = (
            f"Giá đóng cửa gần nhất: {latest.get('close')} | "
            f"Khối lượng: {latest.get('volume')} | "
            f"Cao: {latest.get('high')} | Thấp: {latest.get('low')}"
        )
        if len(records) >= 2:
            prev = records[-2]
            chg = round((float(latest["close"]) - float(prev["close"])) / float(prev["close"]) * 100, 2)
            price_txt += f" | Thay đổi so phiên trước: {'+' if chg >= 0 else ''}{chg}%"

    news_txt = "\n".join(
        f"- [{a.get('source', '')}] {a['title']}"
        for a in (news_articles or [])[:8]
    )

    prompt = f"""{SYSTEM_PROMPT}

## PHÂN TÍCH CHI TIẾT: {symbol.upper()}

### Dữ liệu giá
{price_txt}

### Tin tức liên quan
{news_txt or 'Không có tin tức liên quan.'}

---
Hãy phân tích xu hướng kỹ thuật và đánh giá tác động của tin tức lên cổ phiếu {symbol.upper()}.
Cung cấp bảng tỷ lệ xu hướng (Tăng / Giảm / Đi ngang) dựa trên dữ liệu trên.
"""
    return await _call_gateway(prompt, task_type="finance_report")


async def extract_financial_metrics_from_bctc(
    bctc_markdown: str,
    symbol: Optional[str] = None,
) -> FinancialMetricsExtracted:
    """
    Extract core structured fundamental metrics from parsed BCTC Markdown tables.

    Args:
        bctc_markdown: Parsed Markdown text of the financial statement.
        symbol: Optional stock ticker symbol.

    Returns:
        FinancialMetricsExtracted Pydantic object.
    """
    # Truncate to reasonable context window (~15,000 chars) focusing on core tables
    context = bctc_markdown[:18000]

    prompt = f"""Bạn là một hệ thống trích xuất dữ liệu tài chính chính xác tuyệt đối.
Nhiệm vụ của bạn là đọc Báo cáo tài chính (BCTC) dưới dạng Markdown sau đây và trích xuất các chỉ số tài chính theo định dạng JSON duy nhất.

CÁC QUY TẮC BẮT BUỘC:
1. Đọc kỹ Bảng Cân đối kế toán, Báo cáo Kết quả kinh doanh, và Báo cáo Lưu chuyển tiền tệ.
2. Nếu chỉ số nào KHÔNG có trong tài liệu, trả về giá trị null. Tuyệt đối không tự suy đoán (no hallucination).
3. Đơn vị tính: Chuyển đổi về số nguyên hoặc số thực đơn vị Đồng (VND). Các số âm trong ngoặc đơn ví dụ (1.200.000) đổi thành -1200000.
4. Chỉ trả về một JSON object duy nhất, không kèm giải thích hay văn bản ngoài JSON.

JSON SCHEMA:
{{
  "symbol": "{symbol or 'MÃ_CP'}",
  "period": "Kỳ báo cáo ví dụ Q2/2026 hoặc Năm 2025",
  "net_revenue": null,
  "gross_profit": null,
  "net_profit_after_tax": null,
  "operating_cash_flow": null,
  "total_assets": null,
  "equity": null,
  "short_term_debt": null,
  "long_term_debt": null,
  "eps": null,
  "roa": null,
  "roe": null,
  "notes": "Ghi chú ngắn về đặc điểm nổi bật trong kỳ"
}}

NỘI DUNG BÁO CÁO TÀI CHÍNH (MARKDOWN):
{context}
"""
    response_text = await _call_gateway(prompt, task_type="finance_extract")

    try:
        # Extract json block using regex
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            data = json.loads(json_match.group(0))
            return FinancialMetricsExtracted(**data)
    except Exception as e:
        logger.warning("[AI Orchestrator] Failed to parse JSON metrics from LLM: %s. Raw: %s", e, response_text[:200])

    return FinancialMetricsExtracted(symbol=symbol, notes="Không thể trích xuất tự động qua LLM.")


async def generate_comprehensive_analysis_report(
    symbol: str,
    risk_cache: dict[str, Any],
    bctc_summary: Optional[dict[str, Any]] = None,
) -> str:
    """
    Synthesise a multi-factor 3-part financial analysis report combining
    Fundamental health (F-Score + BCTC) and Technical Risk Scoring (BUY_RISK / SELL_RISK).

    Args:
        symbol: Stock ticker symbol.
        risk_cache: Risk evaluation dictionary from RiskScoringService / RiskAnalysisCache.
        bctc_summary: Optional parsed financial metrics or Markdown summary.

    Returns:
        Standard 3-part Markdown analysis report string.
    """
    symbol = symbol.upper()

    # 1. Format Technical Risk Details
    buy_score = risk_cache.get("buy_score", 0)
    sell_score = risk_cache.get("sell_score", 0)
    buy_level = risk_cache.get("buy_level", "NORMAL")
    sell_level = risk_cache.get("sell_level", "NORMAL")
    scenario = risk_cache.get("scenario", "Không xác định")
    f_score = risk_cache.get("f_score")
    valuation = risk_cache.get("valuation", {})

    buy_reasons = risk_cache.get("details", {}).get("buy_reasons_detail", [])
    sell_reasons = risk_cache.get("details", {}).get("sell_reasons_detail", [])

    buy_reasons_txt = "\n".join(f"- {r.get('title', r.get('code'))}" for r in buy_reasons) or "Không có tín hiệu cảnh báo rủi ro mua đuổi."
    sell_reasons_txt = "\n".join(f"- {r.get('title', r.get('code'))}" for r in sell_reasons) or "Không có tín hiệu bán tháo cạn cung."

    # 2. Format Fundamental Details
    fundamental_txt = f"Điểm Piotroski F-Score: {f_score}/9" if f_score is not None else "Điểm Piotroski: Đang cập nhật"
    if valuation:
        fundamental_txt += (
            f"\nP/E: {valuation.get('pe', 'N/A')} | P/B: {valuation.get('pb', 'N/A')} | "
            f"ROE: {valuation.get('roe', 'N/A')}%"
        )

    bctc_context_txt = "Chưa có file BCTC PDF đính kèm trong phiên."
    if bctc_summary:
        if isinstance(bctc_summary, dict) and "extracted_metrics" in bctc_summary and bctc_summary["extracted_metrics"]:
            m = bctc_summary["extracted_metrics"]
            m_dict = m.model_dump() if hasattr(m, "model_dump") else (m if isinstance(m, dict) else {})
            bctc_context_txt = (
                f"- Kỳ báo cáo: {m_dict.get('period', 'N/A')}\n"
                f"- Doanh thu thuần: {m_dict.get('net_revenue', 'N/A'):,} VND\n"
                f"- Lợi nhuận sau thuế: {m_dict.get('net_profit_after_tax', 'N/A'):,} VND\n"
                f"- Dòng tiền HĐKD (CFO): {m_dict.get('operating_cash_flow', 'N/A'):,} VND\n"
                f"- Tổng tài sản: {m_dict.get('total_assets', 'N/A'):,} VND\n"
                f"- Nợ ngắn hạn / Dài hạn: {m_dict.get('short_term_debt', 'N/A'):,} / {m_dict.get('long_term_debt', 'N/A'):,} VND\n"
                f"- Ghi chú: {m_dict.get('notes', 'N/A')}"
            )
        elif isinstance(bctc_summary, str):
            bctc_context_txt = bctc_summary[:4000]

    # Helper for visual progress bars in Markdown
    def _bar(val: int, max_val: int = 100) -> str:
        pct = min(100, max(0, int((val / max_val) * 10)))
        return f"`[{'█' * pct}{'░' * (10 - pct)}] {val}/{max_val}`"

    buy_bar = _bar(buy_score, 100)
    sell_bar = _bar(sell_score, 100)
    f_bar = _bar(f_score, 9) if f_score is not None else "`[Đang cập nhật]`"

    prompt = f"""{SYSTEM_PROMPT}

Nhiệm vụ của bạn là tổng hợp Báo cáo Phân tích Tài chính Toàn cảnh Đa chiều cho mã cổ phiếu {symbol}.
Báo cáo BẮT BUỘC phải tuân thủ đúng cấu trúc 3 PHẦN sau đây và sử dụng các thanh hiển thị chỉ số trực quan:

# BÁO CÁO PHÂN TÍCH TOÀN CẢNH ĐA CHIỀU: {symbol}

## PHẦN 1: ĐÁNH GIÁ SỨC KHỎE TÀI CHÍNH & CHẤT LƯỢNG DOANH NGHIỆP
- Thước đo Piotroski F-Score: {f_bar}
- Đánh giá chi tiết tăng trưởng doanh thu, lợi nhuận và chất lượng dòng tiền kinh doanh (CFO).
- Phân tích cơ cấu nợ vay, tỷ lệ đòn bẩy và sức chống chịu rủi ro.
- Nhận định ý nghĩa định giá P/E, P/B, ROE so với quy mô doanh nghiệp.

## PHẦN 2: XU HƯỚNG KỸ THUẬT & TƯƠNG QUAN THỊ TRƯỜNG
- Thước đo Rủi ro Mua đuổi (BUY_RISK): {buy_bar} ({buy_level})
- Thước đo Rủi ro Bán cạn cung (SELL_RISK): {sell_bar} ({sell_level})
- **Tương quan Xu hướng & Động lượng:** Phân tích độ nhạy (Beta kỹ thuật) và tính tương quan giữa biến động giá {symbol} so với xu hướng chung của thị trường (VN-Index).
- Phân tích các mã tín hiệu kỹ thuật thực tế:
  * Tín hiệu cảnh báo rủi ro Mua đuổi:
{buy_reasons_txt}
  * Tín hiệu rủi ro Bán cạn cung:
{sell_reasons_txt}

## PHẦN 3: KỊCH BẢN HÀNH ĐỘNG & KHUYẾN CÁO AN TOÀN
- Kịch bản tổng hợp chiến lược: "{scenario}"
- Đưa ra các mốc giá hỗ trợ/kháng cự then chốt cần quan sát.
- Hướng dẫn quản trị rủi ro danh mục dựa trên xác suất xu hướng (tuyệt đối không khuyên mua/bán).

---

DỮ LIỆU ĐẦU VÀO ĐỂ TỔNG HỢP:
### 1. Dữ liệu BCTC & Cơ bản:
{fundamental_txt}
{bctc_context_txt}

### 2. Dữ liệu Rủi ro Kỹ thuật & Tương quan:
- Điểm BUY_RISK: {buy_score}/100 ({buy_level})
- Điểm SELL_RISK: {sell_score}/100 ({sell_level})
- Kịch bản hệ thống gợi ý: {scenario}

Hãy xuất ra báo cáo hoàn chỉnh dưới định dạng Markdown, bố cục rõ ràng, lập luận chuyên nghiệp và kết thúc bằng TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM.
"""
    return await _call_gateway(prompt, task_type="finance_report")


async def chat_with_document_context(
    query: str,
    bctc_markdown: str,
    chat_history: Optional[list[dict[str, str]]] = None,
) -> dict[str, Any]:
    """
    Answer interactive user queries grounded strictly on parsed BCTC Markdown context.

    Args:
        query: User question.
        bctc_markdown: The parsed BCTC text from the current session.
        chat_history: Prior conversation turns.

    Returns:
        Dict with "answer" and "citations" list.
    """
    history_txt = ""
    if chat_history:
        history_txt = "\n".join(
            f"{turn.get('role', 'user').upper()}: {turn.get('content', '')}"
            for turn in chat_history[-4:]
        )

    # Slice relevant context if needed
    context = bctc_markdown[:16000]

    prompt = f"""Bạn là trợ lý phân tích Báo cáo tài chính (BCTC) thông minh.
NGUYÊN TẮC BẮT BUỘC:
1. Bạn CHỈ ĐƯỢC PHÉP trả lời dựa trên thông tin, số liệu có trong nội dung BCTC cung cấp bên dưới.
2. Nếu câu hỏi yêu cầu thông tin KHÔNG có trong BCTC, bạn phải trả lời rõ ràng:
   "Thông tin này không được đề cập trong báo cáo tài chính đã cung cấp."
   Tuyệt đối KHÔNG tự sáng tác số liệu (anti-hallucination).
3. Luôn nêu rõ số liệu lấy từ bảng nào (ví dụ: Bảng Cân đối kế toán - Chỉ số Nợ ngắn hạn, Báo cáo KQKD...).
4. Định dạng câu trả lời rõ ràng, súc tích.

LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ:
{history_txt or 'Chưa có lịch sử.'}

NỘI DUNG BÁO CÁO TÀI CHÍNH:
{context}

CÂU HỎI CỦA NGƯỜI DÙNG:
{query}
"""
    answer_text = await _call_gateway(prompt, task_type="finance_chat")

    # Extract likely citations from text heuristic
    citations = []
    found_sections = re.findall(
        r"(Bảng cân đối kế toán|Báo cáo kết quả hoạt động kinh doanh|Báo cáo lưu chuyển tiền tệ|Thuyết minh báo cáo tài chính|Mục \d+|Khoản mục [A-Z0-9\.]+)",
        answer_text,
        re.IGNORECASE,
    )
    if found_sections:
        citations = list(dict.fromkeys(found_sections))[:3]
    else:
        citations = ["Báo cáo tài chính phiên hiện tại"]

    return {
        "answer": answer_text,
        "citations": citations,
    }


# ---------------------------------------------------------------------------
# Internal gateway dispatch
# ---------------------------------------------------------------------------

async def _call_gateway(prompt: str, task_type: str) -> str:
    """
    Dispatch a prompt to the LLMGateway using task-configured fallback chains.

    Args:
        prompt:    Complete prompt string.
        task_type: Label for logging and task-chain routing.

    Returns:
        Raw LLM text response.
    """
    gw_settings: GatewaySettings = build_gateway_settings()

    # Route according to task fallback chain in gw_config if present
    chain = gw_settings.task_fallback_chains.get(task_type, FINANCE_ANALYSIS_CHAIN)

    try:
        async with LLMGateway(gw_settings) as gateway:
            result = await gateway.run(prompt, chain=chain)
            if result.error:
                logger.error("[AI Orchestrator] All models failed for task '%s': %s", task_type, result.error)
                return (
                    "⚠️ Hệ thống AI tạm thời không phản hồi. "
                    "Vui lòng xem số liệu thô hoặc thử lại sau.\n\n"
                    "_Phân tích trên mang tính tham khảo, không phải tư vấn đầu tư._"
                )
            logger.info(
                "[AI Orchestrator] task='%s' platform=%s model=%s attempts=%d",
                task_type, result.platform, result.model_name, result.attempts,
            )
            return result.content
    except Exception as e:
        logger.exception("[AI Orchestrator] Unexpected error for task '%s'", task_type)
        return f"⚠️ Lỗi kết nối AI: {e}\n\n_Phân tích trên mang tính tham khảo, không phải tư vấn đầu tư._"
