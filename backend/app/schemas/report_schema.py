"""
name: report_schema.py
description: Pydantic schemas for PDF report generation, listing, and deletion.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReportResponse(BaseModel):
    """Response payload for generated quick PDF report."""
    status: str = Field(..., description="Status string: 'success' or 'error'.")
    pdf_url: str = Field(..., description="Publicly accessible URL to download the generated PDF report.")
    id: Optional[str] = Field(default=None, description="UUID identifier in Neon database.")
    title: Optional[str] = Field(default=None, description="Report title.")


class ReportItemResponse(BaseModel):
    """Metadata representing a single stored PDF report."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = Field(default=None, description="Unique UUID identifier.")
    title: Optional[str] = Field(default=None, description="Human-readable title.")
    report_type: Optional[str] = Field(default=None, description="Type: 'quick_symbol', 'ai_overview', 'ai_detail'.")
    symbol: Optional[str] = Field(default=None, description="Stock ticker if applicable.")
    filename: str = Field(..., description="File name of the generated PDF report.")
    url: str = Field(..., description="Download/view URL for the report.")
    size_kb: Optional[float] = Field(default=None, description="File size in kilobytes.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")


class ReportListResponse(BaseModel):
    """Response container for the list of available PDF reports."""
    reports: list[ReportItemResponse] = Field(
        default_factory=list,
        description="Collection of generated PDF report items.",
    )


class ReportDeleteResponse(BaseModel):
    """Response payload returned when a report is deleted."""
    status: str = Field(..., description="Status string: 'success' or 'error'.")
    message: str = Field(..., description="Confirmation message.")
    id: str = Field(..., description="ID or filename of the deleted report.")
