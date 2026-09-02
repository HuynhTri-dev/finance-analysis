# Code Architecture Blueprint

## 1. System Level Architecture
Hệ thống áp dụng mô hình phân tán (Client-Server-Cloud) chuyên biệt cho việc tạo và phân phối báo cáo:
- **Frontend (Client):** Next.js (App Router) + Tailwind CSS. 
  - Đóng vai trò là Presentation Layer (Hiển thị 3 Panel). 
  - Hiển thị trực tiếp file báo cáo PDF từ URL do Cloudflare cung cấp qua component `react-pdf` (hoặc iframe).
- **Backend (Server):** Python (FastAPI). 
  - Đóng vai trò Data Processing, thao tác Database (PostgreSQL qua Neon) và AI Orchestration.
  - Generates (Sinh) nội dung Markdown, convert sang PDF và đảm nhiệm luồng upload lên Cloudflare.
- **Cloud Storage:** Cloudflare R2 (hoặc Cloudflare Pages/CDN).
  - Nơi lưu trữ tĩnh các báo cáo phân tích định dạng PDF/Markdown.
  - Phục vụ file tốc độ cao xuống Frontend qua mạng lưới Edge của Cloudflare, giảm tải việc phục vụ file tĩnh cho backend cục bộ.

## 2. Internal Layering (Backend - Clean Architecture)
Cấu trúc backend tuân thủ **Controller-Service-Repository**:
- **Routers (Controllers):** `routers/`. Nhận HTTP Request, validate dữ liệu (bằng Pydantic schemas), và phân phối lệnh xuống Services.
- **Services (Business Logic):** `services/`.
  - `MarketService`: Tương tác `vnstock` để lấy 3 chỉ số Index, Top 10 và dữ liệu OHLCV của mã lẻ.
  - `NewsService`: Chạy crawler định kỳ, lưu trữ, trích xuất và filter văn bản báo chí (Vĩ mô vs Watchlist).
  - `RiskScoringService`: Động cơ tính toán chỉ số kỹ thuật (RSI, MACD, Bollinger Bands) và chấm điểm rủi ro `BUY_RISK`, `SELL_RISK` dựa trên dữ liệu EOD.
  - `AIOrchestratorService`: Xây dựng system prompt, nhúng context (dữ liệu giá + tin tức) và gọi Ollama AI model.
  - `ReportGenerationService`: Chuyển đổi Markdown do AI sinh ra thành file PDF (dùng `pdfkit` hoặc thư viện tương đương) và quản lý tiến trình đẩy lên Cloudflare.
- **Repositories (Data Access):** `repositories/`. Giao tiếp với cơ sở dữ liệu PostgreSQL (Lưu trữ Serverless qua Neon) cho thông tin người dùng, danh mục theo dõi (watchlist) và lịch sử lưu trữ tin tức. Dùng SQLAlchemy hoặc SQLModel làm ORM.

## 3. Design Patterns Áp Dụng
- **Adapter Pattern (Tích hợp External API):** 
  - *Cloudflare Storage Adapter:* Bọc thư viện `boto3` để giao tiếp với Cloudflare R2 thông qua S3-compatible API, chuẩn hóa hàm `upload_file(file_bytes, filename)`.
  - *LLM Adapter:* Giao tiếp chuẩn hóa với Ollama cục bộ (`http://localhost:11434`). Nếu tương lai cần mở rộng dùng ChatGPT, hệ thống chỉ cần cắm thêm `OpenAIAdapter`.
  - *RSS Adapter:* Chuẩn hóa format (Title, Link, Summary, Date) bất chấp nguồn gốc cấp tin là CafeF hay VnEconomy.
- **Singleton Pattern:** 
  - Quản lý Database Connection Pool (SQLAlchemy Engine) kết nối tới PostgreSQL (Neon) để tối ưu hóa kết nối mạng, tránh cạn kiệt connection limit của Neon.
  - Tạo một instance duy nhất cho S3 Client (`boto3`) để upload file mà không tốn chi phí khởi tạo lại kết nối HTTPS.
- **Dependency Injection:** Sử dụng dependency `Depends()` của FastAPI để tiêm (inject) DB Session và Storage Client vào các endpoint một cách cô lập, dễ viết Unit Test.
- **Factory Pattern:** Khởi tạo các class Báo cáo (Report) tùy theo loại (Tổng quan hay Chi tiết mã CK).

## 4. Code Hygiene & Standards
- **Python:** Sử dụng `snake_case` cho biến/hàm, `PascalCase` cho Classes. Type hinting 100% cho function return và argument (sử dụng mạnh Pydantic models).
- **React/Next.js:** Dùng `PascalCase` cho Components, `camelCase` cho trạng thái (state). Phân tách rõ Server Components (lấy dữ liệu tĩnh) và Client Components (khung chat AI cần tính tương tác).
- **Error Handling:** Sử dụng Global Exception Handler trong FastAPI để chuẩn hóa mã lỗi trả về. Tránh để lộ traceback (ví dụ, thay vì crash do lỗi mạng Cloudflare, trả về mã 500 JSON `"Lỗi kết nối tới Cloudflare Storage"`).
