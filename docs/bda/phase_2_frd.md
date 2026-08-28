# Functional Requirements Document (FRD)

> Tài liệu mô tả chi tiết các tính năng (WHAT the system must DO) và các quy tắc nghiệp vụ đi kèm.

## 1. Functional Requirements List

### Module: Data Ingestion (Thu thập dữ liệu)

| FR ID | Requirement Description | Input | Output | Associated Business Rule | Priority |
|---|---|---|---|---|---|
| FR-DI-001 | Lấy dữ liệu chứng khoán qua `vnstock`: VNINDEX, HNXINDEX, UPINDEX; Top 10 tăng giá; Top 10 thanh khoản; và giá/khối lượng mã lẻ. | Mã CK, Tham số thị trường | Dữ liệu DataFrame / JSON | BR-001 | Must-have |
| FR-DI-002 | Lọc và Crawl tin tức mục tiêu theo lịch trình (Sáng, Trưa, Tối): (1) Tin vĩ mô/chung, (2) Tin cho danh mục Watchlist. | Nguồn RSS, Watchlist | Danh sách bài báo lưu vào DB/File | BR-002 | Must-have |

### Module: AI Agent Core (Phân tích AI)

| FR ID | Requirement Description | Input | Output | Associated Business Rule | Priority |
|---|---|---|---|---|---|
| FR-AI-001 | Sinh Báo cáo Tổng quan: Phân tích tin vĩ mô, tin mới thị trường và các giao dịch cổ phiếu nổi bật (Top 10). | JSON dữ liệu thị trường chung, Text tin vĩ mô | Báo cáo Markdown tổng quan thị trường | BR-003 | Must-have |
| FR-AI-002 | Sinh Báo cáo Chi tiết cho mã trong Watchlist: Đánh giá xác suất xu hướng (tỷ lệ %) dựa trên sentiment tin tức cụ thể và PTKT. | Dữ liệu giá mã CK, Tin tức mã CK | Đoạn text chứa tỷ lệ % và lý giải trung lập | BR-004 | Must-have |

### Module: Dashboard UI (Giao diện người dùng)

| FR ID | Requirement Description | Input | Output | Associated Business Rule | Priority |
|---|---|---|---|---|---|
| FR-UI-001 | Hiển thị Bố cục 3 phần: Left Navbar (có Watchlist), Center View, Right Agent Chat trên một trang SPA. | Hành động click | Cập nhật component (không reload trang) | - | Must-have |
| FR-UI-002 | Center View: Dashboard Tổng quan (hiển thị VNINDEX, HNXINDEX, UPINDEX, 2 bảng Top 10, tin vĩ mô). | Dữ liệu FR-DI-001 & AI-001 | Giao diện Dashboard Tổng quan | - | Must-have |
| FR-UI-003 | Center View: Biểu đồ chi tiết mã chứng khoán & Trình xem PDF. | Dữ liệu mã CK từ Watchlist | Biểu đồ nến / Giao diện đọc PDF | - | Must-have |
| FR-UI-004 | Right Panel: Giao diện chat với AI Agent để nhận báo cáo/giải đáp. | Text input từ người dùng | Khung chat streaming AI | - | Must-have |

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
