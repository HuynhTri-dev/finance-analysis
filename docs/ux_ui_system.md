# Hệ Thống Thiết Kế UX/UI (Dark Mode Only & Premium Aesthetics)

Dự án phân tích tài chính cá nhân nhắm đến sự sang trọng, hiện đại, và chuyên nghiệp. Giao diện được thiết kế **100% Dark Mode** (không có chế độ sáng), sử dụng kỹ thuật Glassmorphism (hiệu ứng kính mờ), màu sắc tương phản mạnh mẽ (vibrant accents), và các chuyển động vi mô (micro-animations) để mang lại trải nghiệm phần mềm cao cấp (premium).

---

## 1. Nguyên Tắc Thiết Kế Cốt Lõi (Core Principles)

- **Dark Mode Cơ Bản (Clean Dark):** Sử dụng các tông màu tối mờ (như xám than, đen mờ) làm nền tảng. Sự đơn giản là ưu tiên hàng đầu để người dùng dễ đọc báo cáo dài và tập trung vào biểu đồ số liệu mà không bị mỏi mắt.
- **Bo Góc Nhẹ (Subtle Rounded):** Các thẻ (Cards), Sidebar, và nút bấm sử dụng độ bo góc vừa phải (`rounded-md` hoặc `rounded-lg`) để tạo cảm giác mềm mại, hiện đại nhưng không quá lố.
- **Bóng Đổ Trong (Inner Shadow):** Loại bỏ hoàn toàn các hiệu ứng phát sáng (glow) hay kính mờ (glassmorphism). Thay vào đó, tạo điểm nhấn (độ sâu) cho các **nút bấm (buttons)** và các khối thông tin quan trọng bằng hiệu ứng bóng đổ trong (`shadow-inner`).
- **Màu Sắc Nhẹ Nhàng (Muted Semantics):** Các chỉ báo tăng/giảm dùng màu xanh/đỏ dịu (muted green/red) để phân biệt rõ ràng nhưng không gây chói mắt.

---

## 2. Bảng Màu & Hiệu Ứng (Color Palette & Effects)

Để đảm bảo tính thanh lịch, dễ đọc, cấu hình sau đây sẽ được dùng trong `tailwind.config.js`:

### A. Nền (Backgrounds & Surfaces)
- **App Background:** `bg-[#121212]` (Đen mờ cơ bản, giúp giảm mỏi mắt).
- **Surface (Cards/Panels):** `bg-[#1E1E1E]` (Xám than, phân tách rõ ràng với nền).
- **Surface Hover/Active:** `bg-[#2A2A2A]` (Sáng hơn một chút khi hover).
- **Borders:** `border-gray-800` (Viền mỏng, tối màu để định hình khối mà không gây nhiễu).

### B. Văn bản (Typography Colors)
- **Primary Text:** `text-gray-100` (Trắng xám, đủ độ tương phản nhưng không gắt như trắng tinh).
- **Secondary Text:** `text-gray-400` (Xám nhạt, dùng cho nhãn, phụ đề, thời gian).
- **Muted Text:** `text-gray-500` (Dùng cho thông tin bổ sung).

### C. Màu Ngữ Nghĩa (Muted Semantic Colors)
- **Tăng Giá (Bullish):** `text-green-400` (Màu xanh lá dịu). 
  - Background nhẹ (Badge): `bg-green-900/30`
- **Giảm Giá (Bearish):** `text-red-400` (Màu đỏ dịu).
  - Background nhẹ (Badge): `bg-red-900/30`
- **Đi Ngang (Neutral):** `text-yellow-400` (Vàng dịu).

### D. Điểm Nhấn Nút Bấm (Button Accents & Inner Shadows)
- Thay vì màu nổi, sử dụng độ sâu để nhấn mạnh nút hành động (Ví dụ: Nút phân tích AI).
- **Nút Primary:** `bg-gray-800` với `shadow-inner` (bóng đổ trong `shadow-[inset_0_2px_4px_rgba(0,0,0,0.4)]`).
- **Nút Primary Hover:** Chuyển sang `bg-gray-700` hoặc làm sâu thêm `shadow-inner`.
- **Chỉ Dấu AI:** `text-blue-400` (Màu xanh dương nhạt, nhẹ nhàng, biểu thị AI).

---

## 3. Kiểu Chữ (Typography)

Sử dụng 2 font chữ hiện đại từ Google Fonts để tạo sự tương phản giữa nội dung đọc và dữ liệu số:
1. **Font Chính (UI & Văn bản):** `font-sans` - **Outfit** hoặc **Inter**. Mang lại cảm giác công nghệ, sạch sẽ, bo cong nhẹ nhàng thân thiện.
2. **Font Dữ Liệu Số (Numbers & Tickers):** `font-mono` - **JetBrains Mono** hoặc **Space Mono**. Font chữ có độ rộng cố định (monospaced) giúp căn lề hoàn hảo các con số, giá trị cổ phiếu, và tỷ lệ %.

---

## 4. Bố Cục 3-Panel Layout (SPA)

Trang web là một Ứng Dụng Đơn Trang (SPA) toàn màn hình (`h-screen overflow-hidden`), được chia làm 3 cột chính:

### Cột 1: Left Navigation & Watchlist (Rộng: `w-72` - ~288px)
- **Chức năng:** Điều hướng và quản lý danh mục theo dõi (Watchlist).
- **UI Element:**
  - Logo/Tên ứng dụng (Sử dụng gradient text: AI Finance).
  - Khối Nhập mã chứng khoán (Search/Add to Watchlist) có icon Kính lúp tinh tế.
  - Danh sách các mã cổ phiếu đang theo dõi. Mỗi item hiển thị Mã (FPT) + Giá thu nhỏ + % Thay đổi.
  - Hover vào mỗi item sẽ có hiệu ứng trượt nhẹ `translate-x-1`.

### Cột 2: Center Dashboard (Fluid - `flex-1`)
- **Chức năng:** Không gian phân tích chính (Overview hoặc Detail). Có chức năng cuộn dọc mượt mà.
- **Giao diện Overview (Tổng quan):**
  - Khối 3 thẻ bọc kính (Glass Cards) hiển thị: VNINDEX, HNXINDEX, UPCOMINDEX. Chứa đường mini-sparkline (biểu đồ đường line siêu nhỏ).
  - Grid 2 cột: Bảng Top 10 Tăng Giá (Trái) và Top 10 Khối Lượng (Phải). Bảng không có viền kẻ cứng nhắc, các hàng (rows) phân cách bằng `border-b border-white/5` và hover nổi bật.
- **Giao diện Detail (Chi tiết một mã CK):**
  - Biểu đồ giá (Nến hoặc Line chart) chiếm 60% chiều cao trên cùng.
  - Bảng thống kê giao dịch và tin tức liệt kê bên dưới.
  - **Nút Hành Động:** Nút bấm "Tạo Báo Cáo AI" phát sáng nhẹ, đặt nổi bật dưới biểu đồ.

### Cột 3: Right AI Panel & PDF Viewer (Rộng: `w-[400px]`)
- **Chức năng:** Vùng giao tiếp với Agent AI và đọc báo cáo.
- **UI Element:**
  - Sidebar độc lập, tách biệt bởi border mờ (`border-l border-white/10`).
  - Giao diện dạng hội thoại (Chat-like) nhưng thiên về hiển thị luồng báo cáo phân tích Markdown.
  - Khi người dùng nhấn "Tạo Báo Cáo AI" ở cột giữa, khu vực này sẽ hiển thị hiệu ứng Loading skeleton (sóng quét nhấp nháy), sau đó stream từng dòng kết quả (Markdown).
  - Có tab/nút để chuyển sang chế độ "Xem PDF gốc" (Render file PDF load từ Cloudflare R2).

---

## 5. Hiệu Ứng & Phản Hồi (Subtle Feedback)

- **Trạng Thái Đang Tải (Loading):** Dùng hiệu ứng khung xương (Skeleton loading) dạng khối xám đơn giản mờ dần (`animate-pulse`), không cần hiệu ứng lấp lánh cầu kỳ.
- **Hover Transitions:** Thêm `transition-colors duration-200` vào nút bấm và hàng trong bảng để thay đổi màu mượt mà.
- **Nút Action Chính:** Thay vì phóng to hay phát sáng, việc hover vào nút sẽ làm màu nền sáng lên nhẹ (ví dụ từ `bg-gray-800` sang `bg-gray-700`) và giữ nguyên bóng đổ trong (`shadow-inner`) để tạo cảm giác vật lý, chân thực khi bấm.
