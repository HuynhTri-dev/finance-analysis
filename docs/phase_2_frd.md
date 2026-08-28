# Functional Requirements Document (FRD)

> Tài liệu mô tả chi tiết các tính năng (WHAT the system must DO) và các quy tắc nghiệp vụ đi kèm.

## 1. Functional Requirements List

### Module: Data Ingestion (Thu thập dữ liệu)

| FR ID | Requirement Description | Input | Output | Associated Business Rule | Priority |
|---|---|---|---|---|---|
| FR-DI-001 | Lấy dữ liệu lịch sử giá và khối lượng chứng khoán qua thư viện `vnstock`. | Mã CK, Từ ngày, Đến ngày, Khung giờ | Dữ liệu DataFrame / JSON chứa OHLCV | BR-001 | Must-have |
| FR-DI-002 | Crawl tin tức tài chính theo lịch trình (Sáng, Trưa, Tối). | Danh sách URL (RSS/Web), Bộ lọc từ khóa (Mã CK) | Danh sách bài báo (Tiêu đề, Nội dung, Thời gian, Nguồn) lưu vào Local DB/File | BR-002 | Must-have |

### Module: AI Agent Core (Phân tích AI)

| FR ID | Requirement Description | Input | Output | Associated Business Rule | Priority |
|---|---|---|---|---|---|
| FR-AI-001 | Tổng hợp thông tin từ dữ liệu giá (FR-DI-001) và tin tức (FR-DI-002). | JSON dữ liệu giá, Text tin tức, Prompt | Báo cáo tóm tắt tình hình thị trường của mã CK | BR-003 | Must-have |
| FR-AI-002 | Đánh giá xác suất (tỷ lệ %) xu hướng tăng/giảm dựa trên sentiment tin tức và chỉ báo kỹ thuật. | Báo cáo tổng hợp từ FR-AI-001 | Đoạn text chứa tỷ lệ % và lý giải trung lập | BR-004 | Must-have |

### Module: Dashboard UI (Giao diện người dùng)

| FR ID | Requirement Description | Input | Output | Associated Business Rule | Priority |
|---|---|---|---|---|---|
| FR-UI-001 | Hiển thị Bố cục 3 phần: Left Navbar, Center View, Right Agent Chat trên một trang duy nhất (SPA). | Hành động click của người dùng | Cập nhật component (không reload trang) | - | Must-have |
| FR-UI-002 | Hiển thị biểu đồ chứng khoán tại Center View. | Dữ liệu JSON từ FR-DI-001 | Biểu đồ nến tương tác (TradingView / ECharts) | - | Must-have |
| FR-UI-003 | Trình xem PDF nhúng tại Center View. | File PDF tải lên hoặc chọn từ danh sách | Giao diện đọc PDF (Scroll, Zoom) | - | Should-have |
| FR-UI-004 | Giao diện chat với AI Agent tại Right Panel. | Text input từ người dùng | Khung chat streaming câu trả lời từ AI | - | Must-have |

---

## 2. Business Rules

| BR ID | Rule Description | Applies to FR |
|---|---|---|
| BR-001 | Hệ thống tự động thay thế các giá trị NaN/NaT bằng Null trước khi trả về JSON để tránh lỗi Parse ở frontend. | FR-DI-001 |
| BR-002 | Lịch trình crawl phải được kích hoạt vào 3 thời điểm: 08:00, 11:30, 16:30 hàng ngày để phù hợp với phiên giao dịch. | FR-DI-002 |
| BR-003 | Báo cáo tổng hợp của AI chỉ được sử dụng dữ liệu trong khoảng 48h gần nhất đối với tin tức, và 3 tháng đối với PTKT. | FR-AI-001 |
| BR-004 | **Quan trọng:** Cấm AI Agent sử dụng các từ ngữ mang tính xúi giục giao dịch như "Hãy mua", "Nên bán", "All-in". Chỉ cung cấp đánh giá trung lập dạng "Tỷ lệ tăng: 60%, Tỷ lệ giảm: 40%". | FR-AI-002 |

---

## 3. Data Structure

### Entity: StockData
| Field | Data Type | Required | Constraints |
|---|---|---|---|
| symbol | String | Yes | Phải là mã 3 chữ cái (VD: FPT, HPG) |
| time | Date/String | Yes | Định dạng YYYY-MM-DD |
| open, high, low, close | Float | Yes | > 0 |
| volume | Integer | Yes | >= 0 |

### Entity: NewsArticle
| Field | Data Type | Required | Constraints |
|---|---|---|---|
| id | UUID | Yes | Unique |
| title | String | Yes | |
| content_summary | Text | Yes | Rút gọn < 1000 từ |
| source | String | Yes | CafeF, Vietstock... |
| published_at | DateTime | Yes | |
| related_symbols | Array[String] | Yes | Danh sách mã CK nhắc tới |

---

## 4. Pre/Post-Conditions

### FR-AI-002 (Đánh giá xác suất xu hướng)
- **Pre-condition:** Crawler đã lấy thành công tin tức mới nhất, api vnstock đã trả về dữ liệu giá hợp lệ. Người dùng đã nhập mã cổ phiếu cần phân tích.
- **Post-condition:** Giao diện Right Panel hiển thị kết quả phân tích của AI bao gồm Tỷ lệ % và lý giải.
- **Exception / Error case:** Nếu LLM API timeout hoặc lỗi, trả về thông báo: "Hệ thống AI đang gián đoạn, vui lòng chỉ xem dữ liệu thô."
