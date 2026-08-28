# API Integration & Cloud Architecture Design

## 1. RESTful API Endpoints (Backend FastAPI)

### 1.1 `GET /api/market/overview`
- **Purpose:** Trả về dữ liệu vĩ mô, 3 chỉ số chính và bảng Top 10 cổ phiếu nổi bật.
- **Response (200 OK):**
  ```json
  {
    "indexes": [
      {"symbol": "VNINDEX", "close": 1250.5, "change_pct": 1.2, "volume": 850000000},
      {"symbol": "HNXINDEX", "close": 240.1, "change_pct": -0.5, "volume": 120000000}
    ],
    "top_gainers": [{"symbol": "FPT", "change_pct": 5.4, "price": 135.0}],
    "top_volume": [{"symbol": "HPG", "volume": 15000000, "price": 28.5}]
  }
  ```

### 1.2 `GET /api/news`
- **Query Params:** `?type=macro` (tin chung) hoặc `?type=watchlist` (tin theo giỏ).
- **Purpose:** Frontend dùng để hiển thị News Feed bên dưới bảng điều khiển.
- **Response (200 OK):**
  ```json
  {
    "articles": [
      {
        "id": "uuid-123",
        "title": "Fed giảm lãi suất...",
        "summary": "Tóm tắt ngắn 150 chữ...",
        "published_at": "2026-08-28T08:00:00Z",
        "url": "https://cafef.vn/..."
      }
    ]
  }
  ```

### 1.3 `POST /api/analyze/overview`
- **Body:** Dữ liệu trống `{}` (Backend tự lấy dữ liệu mới nhất).
- **Purpose:** Kích hoạt Ollama tổng hợp thị trường chung. Chuyển kết quả thành PDF và đẩy lên Cloudflare.
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "report_id": "rep-456",
    "markdown_content": "Thị trường hôm nay tích cực...",
    "pdf_url": "https://cdn.yourdomain.com/reports/overview_20260828.pdf"
  }
  ```
  *(Frontend sẽ sử dụng `pdf_url` để đưa vào UI `<embed />` hoặc component react-pdf).*

### 1.4 `POST /api/analyze/detail`
- **Body:** `{"symbol": "FPT"}`
- **Purpose:** AI phân tích sâu PTKT và sentiment tin tức cho mã chứng khoán được yêu cầu. Sinh báo cáo PDF.
- **Response (200 OK):**
  ```json
  {
    "symbol": "FPT",
    "trend_probability": {"up": 65, "down": 35},
    "analysis_text": "Lý giải trung lập từ AI...",
    "pdf_url": "https://cdn.yourdomain.com/reports/detail_FPT_20260828.pdf"
  }
  ```

## 2. Integration with External Systems

### 2.1 Cloudflare R2 (PDF Storage & CDN)
- **Protocol:** Tương thích S3-compatible API (Sử dụng thư viện `boto3` trong Python).
- **Workflow tạo và lưu file:** 
  1. Backend FastAPI nhận markdown từ Ollama.
  2. Dùng thư viện (VD: `pdfkit` / `weasyprint`) chuyển Markdown thành PDF.
  3. Gắn `boto3.client` với `endpoint_url` của Cloudflare R2, truyền `Access Key` & `Secret Key`.
  4. Upload file PDF lên Bucket với quyền `public-read`.
  5. Trả URL tĩnh (hoặc qua custom domain của Cloudflare Pages) về cho Frontend hiển thị.
- **Lợi ích kiến trúc:** Nhờ lưu trên Cloudflare, Frontend load PDF cực nhanh từ Edge cache, không tiêu tốn băng thông hay tài nguyên của máy chủ Backend (Local/VPS).

### 2.2 Ollama API (AI Agent)
- Cổng kết nối: `http://localhost:11434/api/generate`
- **Circuit Breaker:** Đặt Timeout = 60s. Nếu quá hạn hoặc model nặng chưa được load kịp, Backend bắt exception và trả về JSON:
  `{"error": "AI Agent Timeout", "fallback_message": "Ollama chưa phản hồi. Vui lòng chỉ xem số liệu thô hoặc thử lại sau."}`

### 2.3 Vnstock Library (Data Source)
- Tích hợp nội bộ ngay trong FastAPI backend.
- **Caching:** Wrap các hàm lấy Top 10 và Index bằng `@functools.lru_cache` (TTL=300s). Mục đích để nếu người dùng reload Frontend liên tục, hệ thống sẽ không tạo spam requests xuống API của công ty chứng khoán, tránh bị rate limit (chặn IP).

### 2.4 RSS News Crawler
- Tích hợp chạy ngầm bằng Background Tasks hoặc cron job `APScheduler` (chạy cố định vào các giờ 08:00, 11:30, 16:30). Không cung cấp endpoint API ra ngoài mạng public để kích hoạt thủ công, nhằm đảm bảo hệ thống không bị tấn công (DDoS) bắt crawl liên tục.
