"""
name: pdf_processor.py
description: Document processor engine converting PDF financial statements (BCTC)
             into structured Markdown while strictly preserving tabular layout,
             section hierarchy, and financial statement integrity.
"""

from __future__ import annotations

import io
import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class BCTCDocumentProcessor:
    """
    Processor for parsing corporate financial statements (BCTC) from PDF format
    into clean, structured Markdown preserving tabular data (CĐKT, KQKD, LCTT).
    """

    MAX_FILE_SIZE_MB = 50
    MAX_PAGES = 100

    def validate_pdf(
        self, file_bytes: bytes, max_size_mb: int = MAX_FILE_SIZE_MB, max_pages: int = MAX_PAGES
    ) -> Tuple[bool, str | None, int]:
        """
        Validate incoming PDF bytes against size, format, and page limits.

        Args:
            file_bytes: Raw bytes of the uploaded PDF file.
            max_size_mb: Maximum allowed file size in megabytes.
            max_pages: Maximum allowed page count.

        Returns:
            Tuple of (is_valid, error_message, detected_page_count).
        """
        # 1. Check Magic Bytes
        if not file_bytes.startswith(b"%PDF-"):
            return False, "File không đúng định dạng PDF chuẩn (thiếu header %PDF-).", 0

        # 2. Check Size limit
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            return (
                False,
                f"Kích thước file ({size_mb:.1f}MB) vượt quá giới hạn cho phép ({max_size_mb}MB).",
                0,
            )

        # 3. Check Page Count
        page_count = 0
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            page_count = len(reader.pages)
        except Exception as e:
            # Fallback estimation via regex if pypdf reader fails initially
            matches = re.findall(rb"/Type\s*/Page[^s]", file_bytes)
            page_count = len(matches) if matches else 1
            logger.warning("pypdf error during page check (%s), fallback count: %d", e, page_count)

        if page_count > max_pages:
            return (
                False,
                f"Số lượng trang ({page_count} trang) vượt quá giới hạn cho phép ({max_pages} trang/phiên).",
                page_count,
            )

        return True, None, page_count

    def parse_pdf_to_markdown(self, file_bytes: bytes, filename: str) -> dict[str, Any]:
        """
        Convert financial statement PDF to Markdown preserving table relationships.

        Tries Docling engine first if available; falls back to an intelligent
        multi-column tabular reconstructor via pypdf.

        Args:
            file_bytes: Raw bytes of the PDF file.
            filename: Name of the original file.

        Returns:
            Dictionary containing doc_id, filename, markdown, page_count, tables_found.

        Raises:
            ValueError: If the PDF is empty, scanned without OCR text, or unparseable.
        """
        is_valid, err_msg, page_count = self.validate_pdf(file_bytes)
        if not is_valid:
            raise ValueError(err_msg)

        doc_id = str(uuid4())
        markdown_content = ""
        tables_found = 0

        # Attempt 1: Try Docling DocumentConverter if installed
        try:
            from docling.document_converter import DocumentConverter

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_path = tmp_file.name

            try:
                converter = DocumentConverter()
                result = converter.convert(tmp_path)
                markdown_content = result.document.export_to_markdown()
                tables_found = len(result.document.tables) if hasattr(result.document, "tables") else 0
                logger.info("[PDF Processor] Parsed with Docling engine successfully: %s", filename)
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        except (ImportError, Exception) as docling_err:
            logger.info("[PDF Processor] Docling unavailable or skipped (%s), using resilient parser", docling_err)

        # Attempt 2: Resilient parser with financial table reconstruction
        if not markdown_content:
            markdown_content, page_count, tables_found = self._parse_with_table_reconstruction(file_bytes)

        # Validate minimum text layer presence (Anti-scan / Anti-corrupt check)
        clean_text = re.sub(r"\s+", "", markdown_content)
        if len(clean_text) < 60:
            raise ValueError(
                "Không thể nhận diện văn bản trong PDF, vui lòng kiểm tra chất lượng file scan hoặc sử dụng file PDF điện tử có text layer."
            )

        return {
            "doc_id": doc_id,
            "filename": filename,
            "markdown": markdown_content,
            "page_count": page_count,
            "tables_found": tables_found,
            "char_count": len(markdown_content),
        }

    def _parse_with_table_reconstruction(self, file_bytes: bytes) -> tuple[str, int, int]:
        """
        Extract text page by page and reconstruct tabular rows into Markdown tables.

        Args:
            file_bytes: Raw bytes of the PDF.

        Returns:
            Tuple of (markdown_string, page_count, tables_found_count).
        """
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        total_pages = len(reader.pages)
        markdown_sections: list[str] = []
        total_tables = 0

        financial_header_pattern = re.compile(
            r"(BẢNG CÂN ĐỐI KẾ TOÁN|BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH|BÁO CÁO LƯU CHUYỂN TIỀN TỆ|"
            r"THUYẾT MINH BÁO CÁO TÀI CHÍNH|TỔNG TÀI SẢN|NỢ PHẢI TRẢ|VỐN CHỦ SỞ HỮU)",
            re.IGNORECASE,
        )

        for page_idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if not lines:
                continue

            page_md_lines: list[str] = [f"\n### --- Trang {page_idx} / {total_pages} ---\n"]
            in_table = False
            table_buffer: list[list[str]] = []

            for line in lines:
                # Check for major financial headings
                if financial_header_pattern.search(line):
                    if in_table and table_buffer:
                        rendered_table = self._render_markdown_table(table_buffer)
                        if rendered_table:
                            page_md_lines.append(rendered_table)
                            total_tables += 1
                        table_buffer = []
                        in_table = False
                    page_md_lines.append(f"\n#### {line}\n")
                    continue

                # Heuristic: Match financial table rows containing a descriptive name + numbers
                # e.g., "1. Doanh thu bán hàng và cung cấp dịch vụ 01 1.250.000.000 1.100.000.000"
                row_parts = self._split_financial_row(line)
                if len(row_parts) >= 3:
                    in_table = True
                    table_buffer.append(row_parts)
                else:
                    if in_table and table_buffer:
                        rendered_table = self._render_markdown_table(table_buffer)
                        if rendered_table:
                            page_md_lines.append(rendered_table)
                            total_tables += 1
                        table_buffer = []
                        in_table = False
                    page_md_lines.append(line)

            # Flush any pending table at end of page
            if in_table and table_buffer:
                rendered_table = self._render_markdown_table(table_buffer)
                if rendered_table:
                    page_md_lines.append(rendered_table)
                    total_tables += 1

            markdown_sections.append("\n".join(page_md_lines))

        full_markdown = "\n\n".join(markdown_sections)
        return full_markdown, total_pages, total_tables

    def _split_financial_row(self, line: str) -> list[str]:
        """
        Split a single line into columns if it matches a tabular row pattern.
        """
        # Split tokens by 2 or more spaces or tab
        parts = [p.strip() for p in re.split(r"\s{2,}|\t", line) if p.strip()]
        if len(parts) >= 3:
            return parts

        # Regex to split item name from trailing financial numbers (positive or in brackets for negative)
        match = re.match(r"^(.*?)(?:\s+([\(\-]?\d[\d\.\,]*\)?))(?:\s+([\(\-]?\d[\d\.\,]*\)?))+$", line)
        if match:
            # Extract numbers from the tail
            tokens = re.findall(r"[\(\-]?\d[\d\.\,]*\)?", line)
            if tokens:
                label = line[: line.find(tokens[0])].strip()
                if label:
                    return [label] + tokens

        return [line]

    def _render_markdown_table(self, rows: list[list[str]]) -> str:
        """
        Format 2D list of cells into a well-aligned GitHub Flavored Markdown table.
        """
        if not rows:
            return ""

        max_cols = max(len(r) for r in rows)
        if max_cols < 2:
            return "\n".join(" ".join(r) for r in rows)

        # Normalize row lengths
        normalized_rows = [r + [""] * (max_cols - len(r)) for r in rows]

        # Use first row as header if it looks like column titles, otherwise synthetic header
        header = normalized_rows[0]
        data_rows = normalized_rows[1:]

        # Header row
        header_line = "| " + " | ".join(header) + " |"
        separator_line = "| " + " | ".join(["---"] * max_cols) + " |"
        body_lines = ["| " + " | ".join(row) + " |" for row in data_rows]

        return "\n" + "\n".join([header_line, separator_line] + body_lines) + "\n"


# Global singleton instance
bctc_document_processor = BCTCDocumentProcessor()
