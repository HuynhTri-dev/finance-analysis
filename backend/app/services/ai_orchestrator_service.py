"""
name: ai_orchestrator_service.py
description: AI analysis service that orchestrates market data + news into
             structured reports via the existing LLMGateway infrastructure.
             Uses the Ollama adapter (local) as primary, with Gemini fallback.
             Strictly enforces the no-advice constraint (FR-AI-002):
             AI outputs trend probability analysis ONLY — no buy/sell recommendations.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.infra.gateway.core import LLMGateway
from app.infra.gateway.types import GatewaySettings, ModelConfig, Platform
from app.infra.gw_config import build_gateway_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Finance-specific task chain: Ollama local → Gemini fallback
# ---------------------------------------------------------------------------
FINANCE_ANALYSIS_CHAIN: list[ModelConfig] = [
    ModelConfig(
        platform=Platform.OLLAMA,
        model_name="llama3",          # override per your local Ollama setup
        timeout_seconds=90,
        thinking_disabled=True,       # suppress <think> tokens for speed
    ),
    ModelConfig(
        platform=Platform.GEMINI,
        model_name="gemini-1.5-flash",
        timeout_seconds=60,
    ),
]

# ---------------------------------------------------------------------------
# System prompt — strict no-advice guardrail
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Bạn là một hệ thống phân tích dữ liệu tài chính khách quan.
NGUYÊN TẮC BẮT BUỘC:
1. Chỉ đưa ra nhận định về xu hướng thị trường dựa HOÀN TOÀN vào dữ liệu và tin tức được cung cấp.
2. Trình bày tỷ lệ % khả năng tăng/giảm/đi ngang dựa trên phân tích kỹ thuật và tin tức.
3. TUYỆT ĐỐI KHÔNG đưa ra khuyến nghị mua, bán, hoặc nắm giữ bất kỳ loại cổ phiếu nào.
4. Trình bày kết quả dưới dạng Markdown, có bảng tóm tắt xu hướng.
5. Luôn kết thúc bằng tuyên bố: "Phân tích trên mang tính tham khảo, không phải tư vấn đầu tư."
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

    Combines index data, top 10 tables, and macro news headlines into
    a structured prompt and dispatches to the LLM gateway.

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
    return await _call_gateway(prompt, task_type="finance_overview")


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
    return await _call_gateway(prompt, task_type="finance_detail")


# ---------------------------------------------------------------------------
# Internal gateway dispatch
# ---------------------------------------------------------------------------

async def _call_gateway(prompt: str, task_type: str) -> str:
    """
    Dispatch a prompt to the LLMGateway using the finance analysis chain.

    Args:
        prompt:    Complete prompt string.
        task_type: Label for logging purposes.

    Returns:
        Raw LLM text response.
    """
    gw_settings: GatewaySettings = build_gateway_settings()

    try:
        async with LLMGateway(gw_settings) as gateway:
            result = await gateway.run(prompt, chain=FINANCE_ANALYSIS_CHAIN)
            if result.error:
                logger.error("[AI Orchestrator] All models failed for task '%s': %s", task_type, result.error)
                return (
                    "⚠️ Hệ thống AI tạm thời không phản hồi. "
                    "Vui lòng xem số liệu thô bên trên.\n\n"
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
