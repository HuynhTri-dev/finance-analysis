# User Stories & Acceptance Criteria

> Sử dụng chuẩn INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable) và cấu trúc Gherkin (Given-When-Then) cho Acceptance Criteria.

## Epic 1: Thu thập Dữ liệu (Data Ingestion)

### US-001: Lấy dữ liệu tổng quan và chi tiết
**As an** Investor, 
**I want to** hệ thống tự động kéo các chỉ số VNINDEX/HNX/UPCOM, bảng Top 10 cổ phiếu nổi bật và dữ liệu mã cụ thể từ vnstock,
**So that** tôi có một góc nhìn từ vĩ mô đến vi mô nhanh chóng.

**Acceptance Criteria:**
- **Scenario:** Lấy dữ liệu thành công.
  - **Given** người dùng mở ứng dụng,
  - **When** frontend gửi yêu cầu lấy dữ liệu thị trường chung,
  - **Then** backend lấy các Index và Top 10 qua vnstock thành công và trả về JSON hợp lệ.

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

### US-003: Phân tích 2 lớp (Tổng quan và Chi tiết)
**As an** Investor, 
**I want to** AI Agent sinh ra 2 loại báo cáo (Tổng quan thị trường và Chi tiết theo mã trong Watchlist),
**So that** tôi vừa nắm được dòng tiền chung vừa đánh giá được tỷ lệ rủi ro của danh mục cá nhân.

**Acceptance Criteria:**
- **Scenario:** Phân tích báo cáo tổng quan.
  - **Given** hệ thống đã lấy được dữ liệu Top 10 và tin tức vĩ mô,
  - **When** người dùng yêu cầu nhận định thị trường chung,
  - **Then** Agent sinh ra báo cáo markdown tổng quan chung.
- **Scenario:** Phân tích mã cụ thể trong Watchlist.
  - **Given** người dùng chọn 1 mã cụ thể trong Watchlist,
  - **When** yêu cầu phân tích,
  - **Then** Agent trả về tỷ lệ % tăng/giảm kèm lý giải,
  - **And** Agent tuyệt đối KHÔNG chứa từ khóa khuyên mua hay bán trực tiếp.

## Epic 3: Trải nghiệm Giao diện (Dashboard SPA)

### US-004: Giao diện Dashboard Tổng quan và Chi tiết
**As an** Investor, 
**I want to** Center View hiển thị ngay 3 chỉ số chính và 2 bảng Top 10 khi mở app, và có thể chuyển sang biểu đồ chi tiết của mã lẻ trong Watchlist,
**So that** tôi có luồng trải nghiệm đi từ Overview đến Detail mà không phải chuyển tab trình duyệt.

**Acceptance Criteria:**
- **Scenario:** Chuyển đổi công năng ở Center View.
  - **Given** người dùng đang xem biểu đồ giá ở Center View và đang chat với AI ở Right Panel,
  - **When** người dùng click vào chức năng "Đọc PDF báo cáo",
  - **Then** Center View chuyển sang trình xem PDF,
  - **And** Right Panel (AI Agent) vẫn giữ nguyên nội dung chat hiện tại mà không bị làm mới (reload).
