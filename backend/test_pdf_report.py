"""
name: test_pdf_report.py
description: End-to-end test script to verify PDF generation with custom headers/footers,
             Vietnamese text formatting, and Matplotlib stock-market correlation charts.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import pandas as pd
import numpy as np
from app.services.pdf_generator_service import pdf_generator_service, generate_correlation_chart_image

def main():
    print("[Test] Starting PDF Generator Verification...")

    # 1. Generate Mock OHLCV Data for Stock & VN-Index
    dates = pd.date_range(end="2026-09-04", periods=90, freq="D")
    stock_prices = 24000 + np.cumsum(np.random.normal(50, 200, 90))
    vnindex_prices = 1250 + np.cumsum(np.random.normal(2, 10, 90))

    stock_df = pd.DataFrame({"close": stock_prices}, index=dates)
    benchmark_df = pd.DataFrame({"close": vnindex_prices}, index=dates)

    # 2. Generate Chart Bytes
    chart_bytes = generate_correlation_chart_image(
        symbol="CMG",
        stock_df=stock_df,
        benchmark_df=benchmark_df,
        buy_score=38,
        sell_score=25,
        f_score=6,
    )
    print(f"[Test] Generated Correlation Chart PNG Image Bytes: {len(chart_bytes)} bytes")

    # 3. Create Sample Markdown Report
    sample_markdown = """# BÁO CÁO PHÂN TÍCH TOÀN CẢNH ĐA CHIỀU: CMG

## PHẦN 1: ĐÁNH GIÁ SỨC KHỎE TÀI CHÍNH & CHẤT LƯỢNG DOANH NGHIỆP
- Thước đo Piotroski F-Score: `[██████░░░░] 6/9`
- Tăng trưởng lợi nhuận và doanh thu duy trì mức ổn định trong 4 quý gần nhất.
- Tỷ lệ đòn bẩy tài chính ở mức an toàn, nợ vay dài hạn chiếm tỷ trọng thấp.

| Chỉ số | Giá trị | Nhận định |
|---|---|---|
| Piotroski F-Score | 6/9 | Điểm khá, sức khỏe tài chính lành mạnh |
| P/E | 18.15 | Phù hợp mặt bằng cổ phiếu công nghệ |
| P/B | 1.84 | Định giá hợp lý |
| ROE | 10.64% | Hiệu suất sinh lời mức khá |

## PHẦN 2: XU HƯỚNG KỸ THUẬT & TƯƠNG QUAN THỊ TRƯỜNG
- Thước đo Rủi ro Mua đuổi (BUY_RISK): `[███░░░░░░░] 38/100` (NORMAL)
- Thước đo Rủi ro Bán cạn cung (SELL_RISK): `[██░░░░░░░░] 25/100` (NORMAL)
- **Tương quan Xu hướng:** Cổ phiếu CMG có hệ số r tương quan cao với chỉ số VN-Index, thể hiện vận động đồng điệu cùng thị trường chung.

> Cảnh báo rủi ro: Chỉ số RSI tiệm cận vùng 38.81. Đường xu hướng MA20 hiện nằm dưới MA50.

## PHẦN 3: KỊCH BẢN HÀNH ĐỘNG & KHUYẾN CÁO AN TOÀN
- Kịch bản tổng hợp chiến lược: "TIẾP TỤC NẮM GIỮ (Cơ bản ổn định, rủi ro mua đuổi thấp)"
- Vùng hỗ trợ kỹ thuật: 22,350 VND. Vùng kháng cự ngắn hạn: 25,650 VND.

---
*Tuyên bố miễn trừ trách nhiệm: Báo cáo được lập tự động từ dữ liệu thị trường và mô hình AI.*
"""

    # 4. Render PDF
    pdf_bytes = pdf_generator_service.render_markdown_to_pdf(
        markdown_text=sample_markdown,
        title="BÁO CÁO PHÂN TÍCH TOÀN CẢNH ĐA CHIỀU: CMG",
        symbol="CMG",
        chart_image_bytes=chart_bytes,
        risk_data={"scenario": "TIẾP TỤC NẮM GIỮ (PORTFOLIO)"},
    )

    out_file = backend_dir / "test_output_report.pdf"
    out_file.write_bytes(pdf_bytes)

    print(f"[SUCCESS] PDF successfully generated: {out_file} (Size: {round(len(pdf_bytes)/1024, 1)} KB)")

if __name__ == "__main__":
    main()
