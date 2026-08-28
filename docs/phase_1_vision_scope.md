# Vision and Scope Document

## 1. Vision Statement
For nhà đầu tư cá nhân, who mất nhiều thời gian tổng hợp số liệu và tin tức chứng khoán mỗi ngày, Personal AI Financial Analyst là một Dashboard phân tích tự động that kết hợp dữ liệu kỹ thuật từ vnstock và phân tích tin tức bằng AI để đánh giá tỷ lệ xu hướng. Unlike việc phải mở hàng chục tab trình duyệt và đọc báo thủ công, product của chúng tôi gom toàn bộ insights trung lập, dữ liệu biểu đồ và tài liệu PDF vào một trang web duy nhất, tối ưu hóa quá trình ra quyết định nhanh gọn.

## 2. In-Scope
List the modules, features, and functions that will be built in this project:
- [x] **Data Ingestion:** Tích hợp `vnstock` để lấy dữ liệu chứng khoán.
- [x] **News Crawler:** Xây dựng script crawl tin tức theo lịch (Sáng, Trưa, Tối) từ các nguồn uy tín, sử dụng RSS hoặc BeautifulSoup.
- [x] **AI Agent Core:** Prompt engineering để Agent tổng hợp tin tức + PTKT, phân tích đánh giá tỷ lệ tăng/giảm, KHÔNG đưa ra khuyến nghị Mua/Bán.
- [x] **Dashboard UI:** Xây dựng giao diện Web 1 trang (Single Page Application). 
- [x] **Layout UI:** Bố cục 3 phần rõ ràng: Bên trái (Navbar), Ở giữa (Dashboard Chart hoặc PDF Viewer), Bên phải (AI Agent Chat/Panel).

## 3. Out-of-Scope
Explicitly list what will NOT be built in this phase (to prevent future disputes):
- [ ] Phục vụ nhiều người dùng (Multi-tenant SaaS) và hệ thống Login/Register.
- [ ] Crawl tin tức liên tục (Real-time Streaming).
- [ ] Tự động đặt lệnh giao dịch vào công ty chứng khoán (Auto-trading).
- [ ] Quản lý danh mục đầu tư (Portfolio Management / P&L Tracking).

## 4. System Boundary
- **Vnstock:** Thư viện Python để kéo dữ liệu chứng khoán công khai.
- **LLM Provider:** API của mô hình ngôn ngữ lớn (ví dụ: OpenAI, Gemini, Claude) dùng làm core cho AI Agent.
- **External News Websites:** (Ví dụ CafeF, Vietstock, VnEconomy) Hệ thống chỉ tương tác một chiều (đọc dữ liệu) thông qua Crawler/RSS.

## 5. Assumptions
- Dữ liệu lịch sử và giá realtime delay của `vnstock` là đủ đáp ứng nhu cầu phân tích nội bộ cá nhân.
- Trình xem PDF nhúng (PDF.js hoặc iframe) hoạt động tốt trong layout Web 1 trang.

## 6. Constraints
- **Technical:** Ứng dụng phải là Web 1 trang (SPA) để thao tác liền mạch, không reload trang khi xem PDF và chat với Agent.
- **Budget / Timeline:** Triển khai nhanh gọn, tập trung vào Core Feature, không tốn thời gian vào thiết kế màu mè không cần thiết. Chi phí API LLM phải được kiểm soát.
- **Legal / Compliance:** Không (Do chỉ sử dụng cá nhân nội bộ, không cung cấp khuyến nghị tài chính ra công chúng).

## 7. Project Success Criteria
- Hệ thống có thể tự động crawl tin tức đúng 3 khung giờ/ngày mà không crash.
- AI Agent trả lời đúng định dạng: Chỉ phân tích tỷ lệ, tổng hợp thông tin, tuyệt đối không chèn câu chữ khuyên mua hay bán.
- Giao diện SPA hiển thị được cùng lúc Dashboard (hoặc PDF) ở giữa và Agent ở bên phải mà không bị tràn màn hình.
