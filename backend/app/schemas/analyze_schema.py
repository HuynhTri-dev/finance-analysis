"""
name: analyze_schema.py
description: Pydantic schemas for AI analysis request payloads and response outputs.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class DetailAnalysisRequest(BaseModel):
    """Request payload for requesting AI detail analysis of a specific symbol."""
    symbol: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Target stock ticker symbol (e.g. FPT, VNM, HPG).",
        examples=["FPT"],
    )


class AnalysisResponse(BaseModel):
    """Response payload containing generated AI markdown report and PDF artifact link."""
    status: str = Field(..., description="Execution status: 'success' or 'error'.")
    markdown_content: str = Field(..., description="Markdown-formatted AI analysis report.")
    pdf_url: Optional[str] = Field(
        default=None,
        description="Public URL to the exported PDF report on Cloudflare R2 or local static store.",
    )
    error: Optional[str] = Field(default=None, description="Error details if execution failed.")
