"""
name: test_finance_analysis.py
description: Comprehensive test suite for the Finance Analysis BDA Agent.
             Tests PDF processor, document table reconstruction, scanned/empty detection,
             AI orchestrator prompts & guardrails, document session cache, and FastAPI endpoints.
"""

from __future__ import annotations

import asyncio
import io
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.infra.l1_cache import L1Cache, doc_session_cache
from app.main import app
from app.schemas.finance_analysis_schema import (
    BCTCUploadResponse,
    ChatDocumentRequest,
    ComprehensiveReportRequest,
    FinancialMetricsExtracted,
)
from app.services import ai_orchestrator_service
from app.services.pdf_processor import BCTCDocumentProcessor, bctc_document_processor


# ---------------------------------------------------------------------------
# Helper: Generate synthetic PDFs in-memory for testing
# ---------------------------------------------------------------------------

def create_sample_bctc_pdf() -> bytes:
    """
    Creates an in-memory PDF containing realistic financial statement text and tables.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    pdf.cell(0, 10, "CONG TY CO PHAN TAP DOAN FPT", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "BAO CAO TAI CHINH HOP NHAT QUY 2 NAM 2026", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Section 1: Balance Sheet
    pdf.set_font("Helvetica", "B", size=12)
    pdf.cell(0, 10, "BANG CAN DOI KE TOAN", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, "Khoan muc   Ma so   So cuoi ky   So dau nam", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "1. Tien va tuong duong tien   110   12.500.000.000   10.200.000.000", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "2. Tong tai san   270   65.000.000.000   58.000.000.000", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "3. No phai tra   300   28.000.000.000   25.000.000.000", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "4. Von chu so huu   400   37.000.000.000   33.000.000.000", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Section 2: Income Statement
    pdf.set_font("Helvetica", "B", size=12)
    pdf.cell(0, 10, "BAO CAO KET QUA HOAT DONG KINH DOANH", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, "Chi tieu   Ma so   Ky nay   Ky truoc", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "1. Doanh thu ban hang   01   32.000.000.000   28.000.000.000", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "2. Loi nhuan gop   20   12.800.000.000   11.200.000.000", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "3. Loi nhuan sau thue   60   4.500.000.000   3.800.000.000", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Section 3: Cash Flow Statement
    pdf.set_font("Helvetica", "B", size=12)
    pdf.cell(0, 10, "BAO CAO LUU CHUYEN TIEN TE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 8, "1. Luu chuyen tien tu HDKD   20   5.100.000.000   4.200.000.000", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


def create_blank_scanned_pdf() -> bytes:
    """
    Creates an empty PDF with no text layer (simulating a scanned image without OCR).
    """
    pdf = FPDF()
    pdf.add_page()
    # Add nothing or only 1 blank character
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 10, " ")
    return bytes(pdf.output())


# ===========================================================================
# 1. PDF Processor Tests (FR-001, BR-001, BR-002, AC1.1, AC1.2)
# ===========================================================================

class TestPDFProcessor:
    """Test suite for BCTCDocumentProcessor."""

    def test_pdf_validation_magic_bytes(self):
        """Reject non-PDF files that lack the %PDF- header."""
        processor = BCTCDocumentProcessor()
        invalid_bytes = b"This is a text file, not a PDF document."
        is_valid, err_msg, _ = processor.validate_pdf(invalid_bytes)
        assert not is_valid
        assert "không đúng định dạng PDF" in err_msg

    def test_pdf_validation_size_limit(self):
        """Reject files exceeding the 50MB size limit (BR-002)."""
        processor = BCTCDocumentProcessor()
        # Mock 51MB byte string
        oversized_bytes = b"%PDF-1.4 " + (b"0" * (51 * 1024 * 1024))
        is_valid, err_msg, _ = processor.validate_pdf(oversized_bytes, max_size_mb=50)
        assert not is_valid
        assert "vượt quá giới hạn cho phép" in err_msg

    def test_pdf_validation_page_limit(self):
        """Reject files exceeding the 100-page limit (BR-002)."""
        processor = BCTCDocumentProcessor()
        # Create a 3-page PDF and validate against max_pages=2
        pdf = FPDF()
        for _ in range(3):
            pdf.add_page()
            pdf.set_font("Helvetica", size=10)
            pdf.cell(0, 10, "Content")
        pdf_bytes = bytes(pdf.output())

        is_valid, err_msg, pages = processor.validate_pdf(pdf_bytes, max_pages=2)
        assert not is_valid
        assert pages == 3
        assert "Số lượng trang" in err_msg

    def test_pdf_table_reconstruction_and_markdown(self):
        """Parse valid BCTC PDF into structured Markdown preserving tables (BR-001, AC1.1)."""
        processor = BCTCDocumentProcessor()
        pdf_bytes = create_sample_bctc_pdf()

        result = processor.parse_pdf_to_markdown(pdf_bytes, filename="bctc_fpt_q2.pdf")

        assert result["doc_id"] is not None
        assert result["filename"] == "bctc_fpt_q2.pdf"
        assert result["page_count"] >= 1
        assert result["tables_found"] >= 1

        md = result["markdown"]
        # Must retain financial headers
        assert "BANG CAN DOI KE TOAN" in md
        assert "BAO CAO KET QUA HOAT DONG KINH DOANH" in md
        # Must format tables with Markdown pipe delimiters
        assert "|" in md
        assert "Tong tai san" in md
        assert "Von chu so huu" in md
        assert "Loi nhuan sau thue" in md

    def test_pdf_scanned_blank_detection(self):
        """Detect scanned image / blank PDFs with missing text layer (AC1.2)."""
        processor = BCTCDocumentProcessor()
        blank_pdf = create_blank_scanned_pdf()

        with pytest.raises(ValueError) as exc_info:
            processor.parse_pdf_to_markdown(blank_pdf, filename="scanned_blank.pdf")

        assert "Không thể nhận diện văn bản trong PDF" in str(exc_info.value)
        assert "file scan" in str(exc_info.value)


# ===========================================================================
# 2. Document Session Cache Tests
# ===========================================================================

class TestDocumentSessionCache:
    """Test suite for in-memory session caching with TTL."""

    def test_session_store_and_retrieve(self):
        cache = L1Cache(default_ttl=10.0)
        doc_id = "test-doc-123"
        payload = {"filename": "test.pdf", "markdown": "# BCTC Content"}

        cache.set(doc_id, payload)
        retrieved = cache.get(doc_id)

        assert retrieved is not None
        assert retrieved["filename"] == "test.pdf"
        assert retrieved["markdown"] == "# BCTC Content"

    def test_session_expiry(self):
        # 0.05 second TTL
        cache = L1Cache(default_ttl=0.05)
        doc_id = "test-expired"
        cache.set(doc_id, {"data": 123})

        import time
        time.sleep(0.06)
        assert cache.get(doc_id) is None


# ===========================================================================
# 3. AI Orchestrator Service Tests (Prompts & Guardrails)
# ===========================================================================

class TestAIOrchestrator:
    """Test suite for AI prompts, JSON extraction, and guardrails."""

    @pytest.mark.asyncio
    async def test_extract_financial_metrics_json_parsing(self):
        """Verify metric extraction parses LLM JSON cleanly into Pydantic schema."""
        mock_llm_json = """
        Here is the extracted JSON:
        ```json
        {
          "symbol": "FPT",
          "period": "Q2/2026",
          "net_revenue": 32000000000,
          "gross_profit": 12800000000,
          "net_profit_after_tax": 4500000000,
          "operating_cash_flow": 5100000000,
          "total_assets": 65000000000,
          "equity": 37000000000,
          "short_term_debt": 15000000000,
          "long_term_debt": 5000000000,
          "eps": 3250.0,
          "roa": 7.5,
          "roe": 18.2,
          "notes": "Tăng trưởng doanh thu 14% so cùng kỳ"
        }
        ```
        """
        with patch.object(ai_orchestrator_service, "_call_gateway", new=AsyncMock(return_value=mock_llm_json)):
            metrics = await ai_orchestrator_service.extract_financial_metrics_from_bctc(
                bctc_markdown="mock markdown text",
                symbol="FPT",
            )

            assert isinstance(metrics, FinancialMetricsExtracted)
            assert metrics.symbol == "FPT"
            assert metrics.net_revenue == 32000000000
            assert metrics.net_profit_after_tax == 4500000000
            assert metrics.equity == 37000000000
            assert metrics.roe == 18.2

    @pytest.mark.asyncio
    async def test_generate_comprehensive_report_3_sections_and_disclaimer(self):
        """Verify comprehensive report adheres to 3-part layout and includes disclaimer."""
        mock_report_response = """
# BÁO CÁO PHÂN TÍCH TOÀN CẢNH ĐA CHIỀU: FPT

## PHẦN 1: ĐÁNH GIÁ SỨC KHỎE TÀI CHÍNH & CHẤT LƯỢNG DOANH NGHIỆP
Doanh nghiệp có cơ cấu tài chính vững mạnh, F-Score đạt 8/9.

## PHẦN 2: XU HƯỚNG KỸ THUẬT & VÙNG RỦI RO THỊ TRƯỜNG
Điểm BUY_RISK ở mức 30 (NORMAL), áp lực bán suy kiệt.

## PHẦN 3: KỊCH BẢN HÀNH ĐỘNG & KHUYẾN CÁO AN TOÀN
Kịch bản: CÂN NHẮC TÍCH LŨY / MỞ MUA AN TOÀN. Vùng quan sát 128 - 132.

---
TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM: Báo cáo phân tích trên dựa trên số liệu định lượng khách quan và xác suất xu hướng thị trường, mang tính chất tham khảo học thuật, không phải lời khuyên đầu tư tài chính.
        """
        risk_cache_sample = {
            "buy_score": 30,
            "sell_score": 25,
            "buy_level": "NORMAL",
            "sell_level": "NORMAL",
            "scenario": "CÂN NHẮC TÍCH LŨY / MỞ MUA AN TOÀN",
            "f_score": 8,
            "valuation": {"pe": 18.5, "pb": 3.2, "roe": 22.0},
            "details": {
                "buy_reasons_detail": [{"code": "STRUCTURE_UP", "title": "Hồi phục cấu trúc"}],
                "sell_reasons_detail": [],
            },
        }

        with patch.object(ai_orchestrator_service, "_call_gateway", new=AsyncMock(return_value=mock_report_response)):
            report = await ai_orchestrator_service.generate_comprehensive_analysis_report(
                symbol="FPT",
                risk_cache=risk_cache_sample,
            )

            assert "PHẦN 1: ĐÁNH GIÁ SỨC KHỎE TÀI CHÍNH" in report
            assert "PHẦN 2: XU HƯỚNG KỸ THUẬT & VÙNG RỦI RO THỊ TRƯỜNG" in report
            assert "PHẦN 3: KỊCH BẢN HÀNH ĐỘNG & KHUYẾN CÁO AN TOÀN" in report
            assert "TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM" in report

    @pytest.mark.asyncio
    async def test_chat_grounded_citations(self):
        """Verify chat Q&A extracts citations and answers based on document content."""
        mock_chat_response = (
            "Theo Bảng cân đối kế toán, Nợ ngắn hạn của doanh nghiệp là 15.000 tỷ VND, "
            "tăng nhẹ 8% so với đầu năm."
        )
        with patch.object(ai_orchestrator_service, "_call_gateway", new=AsyncMock(return_value=mock_chat_response)):
            result = await ai_orchestrator_service.chat_with_document_context(
                query="Nợ ngắn hạn kỳ này là bao nhiêu?",
                bctc_markdown="Bảng cân đối kế toán: Nợ ngắn hạn 15.000.000.000.000 VND",
            )

            assert "15.000 tỷ VND" in result["answer"]
            assert len(result["citations"]) >= 1


# ===========================================================================
# 4. FastAPI Endpoints Integration Tests (Phase 4)
# ===========================================================================

class TestFinanceAnalysisAPI:
    """Integration test suite for the /api/finance router."""

    @pytest.fixture(autouse=True)
    def override_db(self):
        class DummySession:
            async def execute(self, stmt):
                class DummyResult:
                    def scalar_one_or_none(self):
                        return None
                return DummyResult()
            def add(self, obj):
                pass
            async def commit(self):
                pass
            async def rollback(self):
                pass

        async def _dummy_get_db():
            yield DummySession()

        from app.routers.finance_analysis_router import get_db
        app.dependency_overrides[get_db] = _dummy_get_db
        yield
        app.dependency_overrides.pop(get_db, None)

    @pytest.fixture
    def client(self):
        return TestClient(app)


    def test_upload_bctc_invalid_extension(self, client):
        """Upload of a non-PDF file (.txt) should return HTTP 400."""
        file_content = b"Some plain text data"
        files = {"file": ("statement.txt", io.BytesIO(file_content), "text/plain")}

        response = client.post("/api/finance/upload-bctc", files=files)
        assert response.status_code == 400
        assert "chỉ chấp nhận file định dạng PDF" in response.json()["detail"]

    def test_upload_bctc_success(self, client):
        """Upload valid PDF returns 200 OK, session doc_id, and parsed metadata."""
        pdf_bytes = create_sample_bctc_pdf()
        files = {"file": ("bctc_fpt.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

        mock_metrics = FinancialMetricsExtracted(
            symbol="FPT",
            period="Q2/2026",
            net_revenue=32000000000,
            net_profit_after_tax=4500000000,
            total_assets=65000000000,
        )

        with patch.object(
            ai_orchestrator_service,
            "extract_financial_metrics_from_bctc",
            new=AsyncMock(return_value=mock_metrics),
        ):
            response = client.post("/api/finance/upload-bctc", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "doc_id" in data
        assert data["filename"] == "bctc_fpt.pdf"
        assert data["page_count"] >= 1
        assert data["extracted_metrics"]["symbol"] == "FPT"
        assert "markdown_url" in data
        assert data["markdown_url"] is not None
        assert "storage_path" in data

        # Verify session is preserved in doc_session_cache
        cached_doc = doc_session_cache.get(data["doc_id"])
        assert cached_doc is not None
        assert cached_doc["filename"] == "bctc_fpt.pdf"

    def test_chat_re_read_from_storage_on_cache_miss(self, client):
        """When doc_session_cache is evicted, chat re-reads markdown from storage."""
        test_doc_id = "test-doc-re-read-123"
        # Simulate doc is in storage but NOT in memory cache
        doc_session_cache.delete(test_doc_id)

        mock_stored_md = "# BCTC FPT ĐƯỢC ĐỌC TỪ CLOUDFLARE R2: Lợi nhuận 4.500 tỷ VND"

        mock_chat_result = {
            "answer": "Theo tài liệu lưu trên Cloudflare R2, lợi nhuận là 4.500 tỷ VND.",
            "citations": ["Báo cáo kết quả hoạt động kinh doanh"],
        }

        with patch("app.routers.finance_analysis_router._load_markdown_from_storage", new=AsyncMock(return_value=mock_stored_md)), \
             patch.object(ai_orchestrator_service, "chat_with_document_context", new=AsyncMock(return_value=mock_chat_result)):

            chat_req = {"doc_id": test_doc_id, "query": "Lợi nhuận là bao nhiêu?"}
            res = client.post("/api/finance/chat", json=chat_req)

            assert res.status_code == 200
            chat_data = res.json()
            assert chat_data["status"] == "success"
            assert "4.500 tỷ" in chat_data["answer"]

            # Confirm L1 cache was re-populated for subsequent fast turns
            re_cached = doc_session_cache.get(test_doc_id)
            assert re_cached is not None
            assert re_cached["markdown"] == mock_stored_md

    def test_chat_with_valid_and_expired_session(self, client):
        """Chat returns 200 for active doc_id, and 404 for expired/non-existent doc_id."""
        # 1. Non-existent doc_id and not in storage -> 404
        bad_req = {"doc_id": "non-existent-uuid", "query": "Doanh thu bao nhiêu?"}
        with patch("app.routers.finance_analysis_router._load_markdown_from_storage", new=AsyncMock(return_value=None)):
            res_404 = client.post("/api/finance/chat", json=bad_req)
            assert res_404.status_code == 404
            assert "không tồn tại" in res_404.json()["detail"] or "hết hạn" in res_404.json()["detail"]

        # 2. Valid doc_id in session cache -> 200
        test_doc_id = "test-active-session"
        doc_session_cache.set(test_doc_id, {"markdown": "# BCTC FPT: Doanh thu 32.000 ty VND"})

        mock_chat_result = {
            "answer": "Doanh thu thuần đạt 32.000 tỷ VND.",
            "citations": ["Báo cáo kết quả hoạt động kinh doanh"],
        }
        with patch.object(
            ai_orchestrator_service,
            "chat_with_document_context",
            new=AsyncMock(return_value=mock_chat_result),
        ):
            chat_req = {"doc_id": test_doc_id, "query": "Doanh thu đạt bao nhiêu?"}
            res_200 = client.post("/api/finance/chat", json=chat_req)

            assert res_200.status_code == 200
            chat_data = res_200.json()
            assert chat_data["status"] == "success"
            assert "32.000 tỷ" in chat_data["answer"]
            assert len(chat_data["citations"]) >= 1


    def test_comprehensive_report_endpoint(self, client):
        """POST /api/finance/comprehensive-report returns 200 with 3-part Markdown analysis."""
        mock_risk = {
            "symbol": "FPT",
            "f_score": 8,
            "buy_score": 30,
            "sell_score": 20,
            "buy_level": "NORMAL",
            "sell_level": "NORMAL",
            "scenario": "CÂN NHẮC TÍCH LŨY / MỞ MUA AN TOÀN",
        }
        mock_report_md = (
            "# BÁO CÁO PHÂN TÍCH TOÀN CẢNH ĐA CHIỀU: FPT\n\n"
            "## PHẦN 1: ĐÁNH GIÁ SỨC KHỎE TÀI CHÍNH\n\n"
            "## PHẦN 2: XU HƯỚNG KỸ THUẬT & VÙNG RỦI RO THỊ TRƯỜNG\n\n"
            "## PHẦN 3: KỊCH BẢN HÀNH ĐỘNG & KHUYẾN CÁO AN TOÀN\n\n"
            "TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM..."
        )

        with patch("app.routers.finance_analysis_router.get_risk_analysis", new=AsyncMock(return_value=mock_risk)), \
             patch.object(ai_orchestrator_service, "generate_comprehensive_analysis_report", new=AsyncMock(return_value=mock_report_md)):

            payload = {
                "symbol": "FPT",
                "include_pdf_export": False,
            }
            res = client.post("/api/finance/comprehensive-report", json=payload)

            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "success"
            assert data["symbol"] == "FPT"
            assert data["f_score"] == 8
            assert data["buy_score"] == 30
            assert "PHẦN 1" in data["report_markdown"]
            assert "PHẦN 2" in data["report_markdown"]
            assert "PHẦN 3" in data["report_markdown"]


# ===========================================================================
# Script execution entry point
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
