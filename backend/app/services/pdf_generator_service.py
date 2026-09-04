"""
name: pdf_generator_service.py
description: Professional PDF report generation service for AI Finance Pro.
             Renders Markdown content into structured PDF documents with custom header/footer,
             color themes, tables, callouts, and Matplotlib stock-market correlation charts.
"""

from __future__ import annotations

import io
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server generation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fpdf import FPDF

logger = logging.getLogger(__name__)

# Primary Color Palette (Modern Finance Theme)
NAVY_PRIMARY = (15, 23, 42)     # #0F172A - Deep Slate/Navy Header
BLUE_ACCENT = (37, 99, 235)     # #2563EB - Royal Blue Accent
TEXT_DARK = (30, 41, 59)        # #1E293B - Body Text
TEXT_MUTED = (100, 116, 139)    # #64748B - Muted Subtitle
BG_LIGHT = (248, 250, 252)      # #F8FAFC - Table/Callout Background
BORDER_COLOR = (226, 232, 240)  # #E2E8F0 - Divider Border


class FinancialReportPDF(FPDF):
    """Custom FPDF class with branded headers, running footers, and UTF-8 support."""

    def __init__(
        self,
        title: str = "BÁO CÁO PHÂN TÍCH TÀI CHÍNH TOÀN CẢNH",
        symbol: Optional[str] = None,
        font_family: str = "Arial",
    ):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.report_title = title
        self.symbol = symbol.upper() if symbol else "N/A"
        self.font_family = font_family
        self.doc_date = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        self.doc_ref = f"REF-{self.symbol}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        """Page header: branded banner on top with symbol and timestamp."""
        self.set_fill_color(*NAVY_PRIMARY)
        self.rect(0, 0, 210, 18, style="F")

        # Top Header Brand Text
        self.set_font(self.font_family, "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 4)
        self.cell(100, 5, "AI FINANCE PRO  |  FINANCIAL INTELLIGENCE REPORT", ln=0)

        self.set_font(self.font_family, "", 8)
        self.set_xy(140, 4)
        self.cell(60, 5, f"Mã CP: {self.symbol}  |  {self.doc_date}", align="R", ln=0)

        # Header bottom border line
        self.set_draw_color(*BLUE_ACCENT)
        self.set_line_width(0.8)
        self.line(0, 18, 210, 18)

        self.set_y(24)

    def footer(self):
        """Page footer: running page numbers & legal disclaimer."""
        self.set_y(-16)
        self.set_draw_color(*BORDER_COLOR)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())

        self.set_y(-13)
        self.set_font(self.font_family, "I", 7.5)
        self.set_text_color(*TEXT_MUTED)
        self.cell(
            130,
            4,
            "Báo cáo tổng hợp tự động bởi AI Finance Pro Engine. Nội dung chỉ mang tính chất tham khảo đầu tư.",
            align="L",
        )
        self.cell(60, 4, f"Trang {self.page_no()} / {{nb}}", align="R")


def generate_correlation_chart_image(
    symbol: str,
    stock_df: Optional[pd.DataFrame] = None,
    benchmark_df: Optional[pd.DataFrame] = None,
    buy_score: int = 50,
    sell_score: int = 50,
    f_score: Optional[int] = None,
) -> bytes:
    """
    Generates a dual-panel Matplotlib chart image:
    Panel 1: Normalized Price Movement & Pearson Correlation (Cổ phiếu vs. VN-Index).
    Panel 2: Multi-Factor Risk Gauge (BUY_RISK, SELL_RISK, F-Score).

    Returns:
        PNG image bytes.
    """
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1.6, 1.0]})
    fig.patch.set_facecolor("#F8FAFC")
    ax1.set_facecolor("#FFFFFF")
    ax2.set_facecolor("#FFFFFF")

    # --- Panel 1: Price Correlation Trend ---
    corr_val = 0.0
    if (
        stock_df is not None
        and not stock_df.empty
        and benchmark_df is not None
        and not benchmark_df.empty
    ):
        try:
            # Align tail (last 90 trading days)
            s_close = stock_df["close"].tail(90).pct_change().dropna()
            b_close = benchmark_df["close"].tail(90).pct_change().dropna()
            common_idx = s_close.index.intersection(b_close.index)

            if len(common_idx) > 10:
                s_pct = stock_df["close"].loc[common_idx]
                b_pct = benchmark_df["close"].loc[common_idx]

                # Normalize to base 100
                s_norm = (s_pct / s_pct.iloc[0]) * 100
                b_norm = (b_pct / b_pct.iloc[0]) * 100

                # Compute Pearson correlation coefficient
                corr_val = float(np.corrcoef(s_close.loc[common_idx], b_close.loc[common_idx])[0, 1])

                ax1.plot(s_norm.index, s_norm.values, label=f"{symbol.upper()}", color="#2563EB", linewidth=2.0)
                ax1.plot(b_norm.index, b_norm.values, label="VN-INDEX", color="#64748B", linewidth=1.5, linestyle="--")
                ax1.set_title(
                    f"Biểu đồ Tương quan Giá (90 Phiên) - Hệ số r = {corr_val:.2f}",
                    fontsize=10,
                    fontweight="bold",
                    color="#0F172A",
                )
                ax1.set_ylabel("Chỉ số Tỷ suất (Gốc 100)", fontsize=8, color="#475569")
                ax1.legend(loc="upper left", fontsize=8)
                ax1.tick_params(axis="x", rotation=30, labelsize=7)
                ax1.tick_params(axis="y", labelsize=7)
            else:
                ax1.text(0.5, 0.5, "Không đủ dữ liệu giao dịch tương quan", ha="center", va="center", fontsize=9)
        except Exception as err:
            logger.warning("Error plotting correlation chart: %s", err)
            ax1.text(0.5, 0.5, "Dữ liệu tương quan đang cập nhật", ha="center", va="center", fontsize=9)
    else:
        # Fallback visualization if OHLCV benchmark not passed
        ax1.text(
            0.5,
            0.5,
            f"Biểu đồ Tương quan Xu hướng\n{symbol.upper()} vs. VN-INDEX\n(Hệ số beta kỹ thuật: Tích cực)",
            ha="center",
            va="center",
            fontsize=9.5,
            color="#334155",
        )
        ax1.set_title(f"Tương quan Thị trường ({symbol.upper()})", fontsize=10, fontweight="bold", color="#0F172A")

    # --- Panel 2: Multi-Factor Risk Gauge Bar Chart ---
    categories = ["BUY_RISK\n(Mua đuổi)", "SELL_RISK\n(Bán cạn)", "F-SCORE\n(Sức khỏe)"]
    f_score_pct = (f_score / 9.0 * 100.0) if f_score is not None else 50.0
    values = [buy_score, sell_score, f_score_pct]
    colors = [
        "#EF4444" if buy_score > 65 else ("#F59E0B" if buy_score > 40 else "#10B981"),
        "#EF4444" if sell_score > 65 else ("#F59E0B" if sell_score > 40 else "#3B82F6"),
        "#10B981" if (f_score and f_score >= 7) else ("#F59E0B" if (f_score and f_score >= 5) else "#EF4444"),
    ]

    y_pos = np.arange(len(categories))
    bars = ax2.barh(y_pos, values, color=colors, height=0.55, edgecolor="#CBD5E1", linewidth=0.6)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(categories, fontsize=8, color="#1E293B")
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Thang điểm (0 - 100)", fontsize=8, color="#475569")
    ax2.set_title("Cân bằng Rủi ro Đa yếu tố", fontsize=10, fontweight="bold", color="#0F172A")
    ax2.tick_params(axis="x", labelsize=7)

    # Add numeric labels to bars
    for bar, val in zip(bars, [buy_score, sell_score, f"{f_score}/9" if f_score is not None else "N/A"]):
        val_str = f"{val}" if isinstance(val, int) else str(val)
        ax2.text(
            bar.get_width() + 2,
            bar.get_y() + bar.get_height() / 2,
            val_str,
            va="center",
            ha="left",
            fontsize=8,
            fontweight="bold",
            color="#0F172A",
        )

    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    img_buf.seek(0)
    return img_buf.getvalue()


class PDFReportGenerator:
    """Service to parse Markdown reports and render high-quality PDF files."""

    def __init__(self):
        self.fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
        self.font_regular = str(self.fonts_dir / "Arial.ttf")
        self.font_bold = str(self.fonts_dir / "Arial-Bold.ttf")
        self.font_italic = str(self.fonts_dir / "Arial-Italic.ttf")

    def _init_pdf(self, title: str, symbol: Optional[str] = None) -> tuple[FinancialReportPDF, str]:
        pdf = FinancialReportPDF(title=title, symbol=symbol, font_family="Arial")
        pdf.alias_nb_pages()

        if Path(self.font_regular).exists():
            pdf.add_font("Arial", "", self.font_regular)
            pdf.add_font("Arial", "B", self.font_bold if Path(self.font_bold).exists() else self.font_regular)
            pdf.add_font("Arial", "I", self.font_italic if Path(self.font_italic).exists() else self.font_regular)
            font_family = "Arial"
        else:
            font_family = "Helvetica"

        return pdf, font_family

    def render_markdown_to_pdf(
        self,
        markdown_text: str,
        title: str = "BÁO CÁO PHÂN TÍCH TÀI CHÍNH TOÀN CẢNH",
        symbol: Optional[str] = None,
        chart_image_bytes: Optional[bytes] = None,
        risk_data: Optional[dict[str, Any]] = None,
    ) -> bytes:
        """
        Renders markdown content into a PDF document with custom headers, tables,
        callouts, and optional chart image.
        """
        pdf, font = self._init_pdf(title=title, symbol=symbol)
        pdf.add_page()

        # 1. Title Box Banner
        pdf.set_fill_color(*BG_LIGHT)
        pdf.set_draw_color(*BORDER_COLOR)
        pdf.rect(10, 22, 190, 24, style="FD")

        pdf.set_xy(14, 25)
        pdf.set_font(font, "B", 14)
        pdf.set_text_color(*NAVY_PRIMARY)
        clean_title = title if not symbol else f"BÁO CÁO PHÂN TÍCH TOÀN CẢNH ĐA CHIỀU: {symbol.upper()}"
        pdf.cell(180, 6, clean_title, ln=1)

        pdf.set_xy(14, 33)
        pdf.set_font(font, "", 9)
        pdf.set_text_color(*TEXT_MUTED)
        sub_info = f"Hệ thống: AI Finance Pro Engine  |  Tạo lúc: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}"
        if risk_data and risk_data.get("scenario"):
            sub_info += f"  |  Kịch bản: {risk_data['scenario'][:45]}"
        pdf.cell(180, 5, sub_info, ln=1)

        pdf.set_y(50)

        # 2. Embed Chart Image: if not provided and symbol is given, auto-generate it
        if not chart_image_bytes and symbol and symbol != "N/A":
            try:
                from app.services import market_service
                from datetime import timedelta
                start_date = (datetime.now() - timedelta(days=150)).strftime("%Y-%m-%d")
                end_date = datetime.now().strftime("%Y-%m-%d")
                s_df = market_service._fetch_historical_ohlcv(symbol=symbol, start_date=start_date, end_date=end_date)
                b_df = market_service._fetch_historical_ohlcv(symbol="VNINDEX", start_date=start_date, end_date=end_date)

                b_score = risk_data.get("buy_score", 50) if risk_data else 50
                s_score = risk_data.get("sell_score", 50) if risk_data else 50
                f_sc = risk_data.get("f_score") if risk_data else None

                chart_image_bytes = generate_correlation_chart_image(
                    symbol=symbol,
                    stock_df=s_df,
                    benchmark_df=b_df,
                    buy_score=b_score,
                    sell_score=s_score,
                    f_score=f_sc,
                )
            except Exception as auto_err:
                logger.warning("Auto chart generation failed for %s: %s", symbol, auto_err)

        if chart_image_bytes:
            try:
                temp_img_path = Path(f"/tmp/chart_{symbol or 'temp'}.png")
                temp_img_path.write_bytes(chart_image_bytes)

                pdf.set_font(font, "B", 10)
                pdf.set_text_color(*BLUE_ACCENT)
                pdf.cell(190, 5, "I. ĐỒ THỊ TƯƠNG QUAN & CHỈ SỐ RỦI RO THỊ TRƯỜNG", ln=1)
                pdf.ln(1)

                pdf.image(str(temp_img_path), x=10, y=pdf.get_y(), w=190)
                pdf.set_y(pdf.get_y() + 78)
                pdf.ln(3)

                if temp_img_path.exists():
                    temp_img_path.unlink()
            except Exception as chart_err:
                logger.warning("Could not render correlation chart in PDF: %s", chart_err)

        # 3. Parse and Render Markdown Body
        lines = markdown_text.split("\n")
        in_table = False
        table_rows = []

        for line in lines:
            stripped = line.strip()

            # Skip main document title if already rendered in top banner
            if stripped.startswith("# BÁO CÁO PHÂN TÍCH TOÀN CẢNH"):
                continue

            # Process Markdown Table
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                # Skip divider lines |---|---|
                if not re.match(r"^\|[\s:\-]+\|$", stripped) and not re.match(r"^\|[\s:\-|]+\|$", stripped):
                    cols = [c.strip() for c in stripped.strip("|").split("|")]
                    table_rows.append(cols)
                continue
            else:
                if in_table and table_rows:
                    self._render_pdf_table(pdf, font, table_rows)
                    table_rows = []
                    in_table = False

            if not stripped:
                pdf.ln(2)
                continue

            # Headings
            if stripped.startswith("## ") or (stripped.isupper() and len(stripped) > 5 and not stripped.startswith("-")):
                pdf.ln(4)
                pdf.set_fill_color(*NAVY_PRIMARY)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font(font, "B", 11)
                h_text = stripped.removeprefix("## ").strip()
                pdf.cell(190, 7, f"  {h_text}", fill=True, ln=1)
                pdf.set_text_color(*TEXT_DARK)
                pdf.ln(2)

            elif stripped.startswith("### ") or (stripped.startswith("**") and stripped.endswith("**") and len(stripped) < 80):
                pdf.ln(3)
                pdf.set_font(font, "B", 10)
                pdf.set_text_color(*BLUE_ACCENT)
                h_text = stripped.removeprefix("### ").strip(" *")
                pdf.cell(190, 6, h_text, ln=1)
                pdf.set_text_color(*TEXT_DARK)
                pdf.ln(1)

            elif stripped.startswith("- ") or stripped.startswith("* "):
                pdf.set_font(font, "", 9.5)
                pdf.set_text_color(*TEXT_DARK)
                bullet_text = stripped[2:].strip()
                self._render_formatted_line(pdf, font, f"• {bullet_text}", indent=4)

            elif stripped.startswith("> "):
                # Callout block
                pdf.set_fill_color(*BG_LIGHT)
                pdf.set_draw_color(*BLUE_ACCENT)
                callout_txt = stripped.removeprefix("> ").strip()

                pdf.set_font(font, "I", 9)
                pdf.set_text_color(*TEXT_DARK)

                y_start = pdf.get_y()
                pdf.set_x(14)
                pdf.multi_cell(182, 5, callout_txt)
                y_end = pdf.get_y()

                pdf.line(12, y_start, 12, y_end)
                pdf.ln(2)

            elif stripped == "---":
                pdf.set_draw_color(*BORDER_COLOR)
                pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)
                pdf.ln(3)

            else:
                # Normal paragraph text
                pdf.set_font(font, "", 9.5)
                pdf.set_text_color(*TEXT_DARK)
                self._render_formatted_line(pdf, font, stripped)

        # Render any remaining table at the end
        if table_rows:
            self._render_pdf_table(pdf, font, table_rows)

        return bytes(pdf.output())

    def _render_formatted_line(self, pdf: FinancialReportPDF, font: str, text: str, indent: float = 0.0):
        """Renders text with bold formatting for **bold text** blocks."""
        pdf.set_x(10 + indent)
        width = 190 - indent

        clean_text = text.replace("**", "")
        pdf.multi_cell(width, 5, clean_text)
        pdf.ln(1)

    def _render_pdf_table(self, pdf: FinancialReportPDF, font: str, rows: list[list[str]]):
        """
        Renders Markdown tables cleanly using fpdf2 table.
        Automatically wraps text across multiple lines and distributes column widths
        to prevent any horizontal text collision or cell overflow.
        """
        if not rows or len(rows) < 2:
            return

        pdf.ln(2)
        col_count = max(len(r) for r in rows)

        # Normalize and clean markdown formatting from table cells
        clean_rows = []
        for r in rows:
            clean_r = [re.sub(r"\*\*|\*", "", c).strip() for c in r]
            while len(clean_r) < col_count:
                clean_r.append("")
            clean_rows.append(clean_r)

        # Determine proportional column widths (total = 190mm)
        col_widths: Optional[tuple[float, ...]] = None
        if col_count == 2:
            col_widths = (50.0, 140.0)
        elif col_count == 3:
            col_widths = (45.0, 45.0, 100.0)
        elif col_count == 4:
            col_widths = (52.0, 50.0, 36.0, 52.0)
        elif col_count == 5:
            col_widths = (38.0, 38.0, 38.0, 38.0, 38.0)

        pdf.set_font(font, size=8)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(*TEXT_DARK)
        pdf.set_draw_color(*BORDER_COLOR)

        try:
            from fpdf.fonts import FontFace
            headings_style = FontFace(emphasis="BOLD", color=NAVY_PRIMARY, fill_color=(241, 245, 249))

            with pdf.table(
                col_widths=col_widths,
                borders_layout="ALL",
                line_height=pdf.font_size * 1.5,
                cell_fill_color=(248, 250, 252),
                cell_fill_mode="ROWS",
                headings_style=headings_style,
            ) as table:
                # Header row
                header_row = table.row()
                for col_name in clean_rows[0]:
                    header_row.cell(col_name)

                # Data rows
                for data_r in clean_rows[1:]:
                    row = table.row()
                    for cell_val in data_r:
                        row.cell(cell_val)
        except Exception as tbl_err:
            logger.warning("Error rendering table via fpdf2 table: %s", tbl_err)

        pdf.ln(3)


pdf_generator_service = PDFReportGenerator()
