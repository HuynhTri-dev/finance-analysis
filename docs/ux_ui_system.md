# UX/UI Analysis & Design System

## 1. Design Principles (C.R.A.P)
- **Contrast (Tương phản):** Sử dụng giao diện Dark Mode làm chủ đạo (nền Xanh Đen) để làm nổi bật các con số tài chính. Màu xanh lá (Tăng) và Đỏ (Giảm) phải đạt chuẩn WCAG (đủ độ sáng trên nền tối).
- **Repetition (Lặp lại):** Các thẻ Widget (Top 10, Thông tin Index) dùng chung một kiểu dáng Thẻ (Card) bo góc mượt, viền mỏng (border-gray-800).
- **Alignment (Căn chỉnh):** Bố cục 3 Panel (Left, Center, Right) có thanh ngăn cách (Divider) tinh tế. Align left cho Text, Align right cho số liệu tiền tệ/phần trăm.
- **Proximity (Gần gũi):** Nhóm các thông tin liên quan sát nhau (VD: Nút phân tích AI nằm ngay dưới biểu đồ để tiện thao tác).

## 2. Color Palette (Tailwind CSS Tokens)
- **Background:** `bg-slate-950` (Nền chính), `bg-slate-900` (Nền Card/Panel).
- **Text:** `text-slate-200` (Chữ chính), `text-slate-400` (Chữ phụ/Ghi chú).
- **Semantic Colors:**
  - Up/Gain: `text-emerald-400` / `bg-emerald-400/10`
  - Down/Loss: `text-rose-500` / `bg-rose-500/10`
- **Primary Accent (AI Elements):** `text-cyan-400` để đại diện cho sự hiện diện của công nghệ AI.

## 3. Layout Structure (SPA)
**1. Left Sidebar (w-64):**
- Tiêu đề "AI Financial Analyst".
- Navigation: Tổng quan, Cài đặt.
- Danh sách Watchlist (Có thể thêm/xóa mã CK).

**2. Center Dashboard (flex-1):**
- Layout lưới (Grid) hiển thị thẻ Tóm tắt (VNINDEX, HNX...).
- Bảng Top 10 Tăng giá (Trái) & Bảng Top 10 Khối lượng (Phải).
- Nếu người dùng bấm vào mã HPG ở cột Watchlist, Center Dashboard sẽ đổi thành: Biểu đồ nến HPG (TradingView/Recharts) + Các thông số cơ bản.

**3. Right AI Panel (w-96):**
- Giao diện như ChatGPT.
- Hiển thị tin nhắn dạng Bubble.
- Hỗ trợ render Markdown (để hiển thị bảng tỷ lệ % và in đậm từ khóa).

## 4. Typography
- Sử dụng **Inter** (mặc định của Tailwind) cho độ dễ đọc tối đa của các con số.
- Sử dụng Font Mono (VD: JetBrains Mono hoặc Roboto Mono) riêng cho các cột hiển thị Số liệu (Giá, Khối lượng) để căn lề đẹp hơn.
