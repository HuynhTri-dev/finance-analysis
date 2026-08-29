"""
name: report_schema.py
description: Pydantic schemas for PDF report generation and listing existing reports.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ReportResponse(BaseModel):
    """Response payload for generated quick PDF report."""
    status: str = Field(..., description="Status string: 'success' or 'error'.")
    pdf_url: str = Field(..., description="Publicly accessible URL to download the generated PDF report.")


class ReportItemResponse(BaseModel):
    """Metadata representing a single stored PDF report."""
    filename: str = Field(..., description="File name of the generated PDF report.")
    url: str = Field(..., description="Download/view URL for the report.")
    size_kb: float = Field(..., description="File size in kilobytes.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")


class ReportListResponse(BaseModel):
    """Response container for the list of available PDF reports."""
    reports: list[ReportItemResponse] = Field(
        default_factory=list,
        description="Collection of generated PDF report items.",
    )
