# User Stories & Acceptance Criteria

> Sử dụng chuẩn INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable) và cấu trúc Gherkin (Given-When-Then) cho Acceptance Criteria.

## Epic 1: Thu thập Dữ liệu (Data Ingestion)

### US-001: Lấy dữ liệu giá chứng khoán
**As an** Investor, 
**I want to** hệ thống tự động kéo dữ liệu giá chứng khoán từ vnstock,
**So that** tôi có sẵn biểu đồ kỹ thuật cập nhật mà không phải mở công cụ khác.

**Acceptance Criteria:**
- **Scenario:** Lấy dữ liệu thành công.
  - **Given** người dùng chọn mã "FPT" trên giao diện,
  - **When** frontend gửi yêu cầu lấy dữ liệu lịch sử 3 tháng,
  - **Then** backend lấy dữ liệu qua vnstock thành công và trả về định dạng JSON, thay thế các giá trị NaN bằng Null.

### US-002: Tự động tổng hợp tin tức
**As an** Investor, 
**I want to** hệ thống tự động lấy các tin tức mới nhất về cổ phiếu 3 lần 1 ngày,
**So that** tôi luôn nắm bắt được các thông tin có thể ảnh hưởng đến thị trường trước giờ giao dịch.

**Acceptance Criteria:**
- **Scenario:** Lịch trình chạy đúng giờ.
  - **Given** hệ thống đang chạy ngầm,
  - **When** đồng hồ điểm 08:00, 11:30 hoặc 16:30,
  - **Then** module Crawler tự động kích hoạt và tải về các bản tin RSS/HTML mới nhất.

## Epic 2: Phân tích AI Agent

### US-003: Phân tích và đưa ra xác suất xu hướng trung lập
**As an** Investor, 
**I want to** AI Agent tổng hợp tin tức và số liệu để đưa ra tỷ lệ % tăng/giảm,
**So that** tôi có một góc nhìn khách quan mà không bị cảm xúc chi phối.

**Acceptance Criteria:**
- **Scenario:** Phân tích một mã cổ phiếu với tin tức tích cực.
  - **Given** AI Agent được cung cấp dữ liệu giá đang trong xu hướng tăng (Uptrend) và 3 bài báo có nội dung lợi nhuận vượt kế hoạch,
  - **When** người dùng yêu cầu phân tích mã chứng khoán này,
  - **Then** Agent phải phản hồi tỷ lệ % (ví dụ: Tăng 70%, Giảm 30%) kèm lý giải,
  - **And** Agent tuyệt đối KHÔNG chứa từ khóa khuyên mua hay bán trực tiếp.

## Epic 3: Trải nghiệm Giao diện (Dashboard SPA)

### US-004: Giao diện làm việc tập trung (SPA Layout)
**As an** Investor, 
**I want to** xem biểu đồ ở giữa màn hình và chat với AI ở cạnh bên phải,
**So that** tôi có thể vừa nhìn biểu đồ vừa đọc lý giải của AI mà không phải chuyển tab.

**Acceptance Criteria:**
- **Scenario:** Chuyển đổi công năng ở Center View.
  - **Given** người dùng đang xem biểu đồ giá ở Center View và đang chat với AI ở Right Panel,
  - **When** người dùng click vào chức năng "Đọc PDF báo cáo",
  - **Then** Center View chuyển sang trình xem PDF,
  - **And** Right Panel (AI Agent) vẫn giữ nguyên nội dung chat hiện tại mà không bị làm mới (reload).
