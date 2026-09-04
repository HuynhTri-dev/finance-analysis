"""
name: finance_analysis_schema.py
description: Pydantic request and response schemas for financial statement (BCTC)
             analysis, metric extraction, comprehensive multi-factor reporting,
             and grounded interactive Q&A.
"""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class FinancialMetricsExtracted(BaseModel):
    """
    Structured financial metrics extracted from financial statement (BCTC) tables.
    """
    symbol: Optional[str] = Field(None, description="Stock ticker symbol (e.g., FPT, VNM, HPG)")
    period: Optional[str] = Field(None, description="Reporting period (e.g., Q2/2026, FY2025)")
    net_revenue: Optional[float] = Field(None, description="Net revenue / Doanh thu thuần (VND)")
    gross_profit: Optional[float] = Field(None, description="Gross profit / Lợi nhuận gộp (VND)")
    net_profit_after_tax: Optional[float] = Field(None, description="Net profit after tax / LNST (VND)")
    operating_cash_flow: Optional[float] = Field(None, description="Cash flow from operating activities / CFO (VND)")
    total_assets: Optional[float] = Field(None, description="Total assets / Tổng tài sản (VND)")
    equity: Optional[float] = Field(None, description="Owner's equity / Vốn chủ sở hữu (VND)")
    short_term_debt: Optional[float] = Field(None, description="Short-term debt / Nợ vay ngắn hạn (VND)")
    long_term_debt: Optional[float] = Field(None, description="Long-term debt / Nợ vay dài hạn (VND)")
    eps: Optional[float] = Field(None, description="Earnings per share / Lãi cơ bản trên cổ phiếu (VND)")
    roa: Optional[float] = Field(None, description="Return on assets / Tỷ suất sinh lời trên tổng tài sản (%)")
    roe: Optional[float] = Field(None, description="Return on equity / Tỷ suất sinh lời trên vốn CSH (%)")
    notes: Optional[str] = Field(None, description="Additional context or caveats extracted from notes")


class BCTCUploadResponse(BaseModel):
    """
    Response schema for PDF BCTC document upload and parsing.
    """
    status: str = Field("success", description="Status string: success or error")
    doc_id: str = Field(..., description="Unique document session ID for subsequent operations")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    page_count: int = Field(..., description="Total pages in the parsed document")
    tables_found: int = Field(0, description="Total tabular elements recognized and preserved")
    extracted_metrics: Optional[FinancialMetricsExtracted] = Field(
        None, description="Extracted fundamental financial metrics"
    )
    summary_markdown: Optional[str] = Field(
        None, description="Clean Markdown representation of the financial statements"
    )
    markdown_url: Optional[str] = Field(
        None, description="Direct or presigned URL to view/download the parsed Markdown from Cloudflare R2 / Local"
    )
    storage_path: Optional[str] = Field(
        None, description="Storage key/path of the Markdown document in Cloudflare R2 or local static directory"
    )



class ComprehensiveReportRequest(BaseModel):
    """
    Request schema for generating a multi-dimensional analysis report.
    """
    symbol: str = Field(..., description="Target stock symbol (e.g. FPT, VNM, HPG)")
    doc_id: Optional[str] = Field(
        None, description="Optional doc_id from previously uploaded BCTC to merge fundamental context"
    )
    include_pdf_export: bool = Field(
        False, description="Whether to render and upload a PDF report artifact to Cloudflare R2 / Local"
    )


class ComprehensiveReportResponse(BaseModel):
    """
    Response schema containing the multi-factor 3-part financial report.
    """
    status: str = Field("success", description="Status of the report generation")
    symbol: str = Field(..., description="Target stock ticker symbol")
    report_markdown: str = Field(..., description="Standard 3-part Markdown analysis report")
    f_score: Optional[int] = Field(None, description="Piotroski F-Score (0-9)")
    buy_score: Optional[int] = Field(None, description="BUY_RISK score (0-100)")
    sell_score: Optional[int] = Field(None, description="SELL_RISK score (0-100)")
    buy_level: Optional[str] = Field(None, description="Risk level for BUY: NORMAL, WATCH, CAUTION, HIGH")
    sell_level: Optional[str] = Field(None, description="Risk level for SELL: NORMAL, WATCH, CAUTION, HIGH")
    scenario: Optional[str] = Field(None, description="Actionable scenario recommendation label")
    pdf_url: Optional[str] = Field(None, description="Downloadable URL of generated PDF artifact if requested")


class ChatDocumentRequest(BaseModel):
    """
    Request schema for asking questions about an uploaded BCTC document.
    """
    doc_id: str = Field(..., description="Document session ID associated with uploaded BCTC Markdown")
    query: str = Field(..., description="User question regarding financial numbers, debt, or footnotes")
    chat_history: List[dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation turns [{'role': 'user'|'assistant', 'content': '...'}]"
    )


class ChatDocumentResponse(BaseModel):
    """
    Response schema for document Q&A with grounded evidence citation.
    """
    status: str = Field("success", description="Status of the chat response")
    doc_id: str = Field(..., description="Referenced document session ID")
    answer: str = Field(..., description="Concise answer grounded strictly in BCTC content")
    citations: List[str] = Field(
        default_factory=list,
        description="References to tables or sections used to derive the answer"
    )
