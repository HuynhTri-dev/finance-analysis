# Phân tích Vấn đề & Giả thuyết Ban đầu (Phase 1 - Business Analysis)

Dựa trên những thông tin bạn cung cấp về dự án phân tích tài chính, tôi đã thực hiện một bước phân tích độc lập (Problem Analysis) để hình dung bức tranh tổng thể trước khi chúng ta đi vào chi tiết (BRD & Vision Scope). 

Dưới đây là các **giả thuyết (Hypotheses)** của tôi về dự án. Hãy xem qua và xác nhận hoặc điều chỉnh nếu tôi hiểu sai nhé:

## 1. Phân tích Hiện trạng (As-Is) & Tương lai (To-Be)
*   **As-Is (Hiện tại):** Việc phân tích một cổ phiếu đang có xu hướng (trending) đòi hỏi nhà đầu tư phải làm thủ công 2 việc: (1) Xem biểu đồ kỹ thuật, (2) Tìm đọc tin tức trên các trang (CafeF, Vietstock, FireAnt...) để hiểu lý do đằng sau xu hướng đó. Dữ liệu giá thì dễ lấy qua `vnstock`, nhưng dữ liệu tin tức thì phân mảnh, nhiễu và khó tổng hợp.
*   **To-Be (Kỳ vọng):** Một hệ thống tự động hoàn toàn: 
    *   Lấy dữ liệu giá/khối lượng từ `vnstock`.
    *   Thu thập và lọc tin tức liên quan đến các mã cổ phiếu đó.
    *   Đưa toàn bộ dữ liệu (Số liệu + Văn bản) vào một **AI Agent**.
    *   AI Agent sẽ đóng vai trò như một chuyên gia phân tích kỹ thuật và cơ bản, tự động đưa ra nhận định.
    *   Hệ thống tự động render ra một Dashboard trực quan và một file Báo cáo Markdown gọn gàng.

## 2. Giá trị cốt lõi (Business Value)
*   Tiết kiệm thời gian research cho nhà đầu tư/Trader.
*   Loại bỏ cảm xúc trong việc tổng hợp tin tức (AI sẽ tổng hợp khách quan hơn).
*   Kết hợp được cả **Định lượng** (Technical Analysis) và **Định tính** (News Sentiment) vào cùng một báo cáo.

## 3. Rủi ro kỹ thuật lớn nhất (Key Constraints & Risks)
*   Như bạn đã đề cập: **Xử lý tin tức**. Khó khăn nằm ở việc:
    *   Nguồn tin (Source): Lấy từ đâu để đảm bảo không bị chặn (block) và cập nhật nhanh.
    *   Trích xuất thực thể (Entity Extraction): Làm sao AI biết bài báo đó đang nói về cổ phiếu nào (ví dụ: bài báo nói về "Hòa Phát", hệ thống phải map được với mã "HPG").
    *   Nhiễu thông tin (Noise): Nhiều tin PR, tin rác không có giá trị phân tích.

---

## Các câu hỏi để làm rõ Yêu cầu (Elicitation)

Để hoàn thiện tài liệu **Vision & Scope** và **BRD**, tôi cần bạn làm rõ thêm 4 vấn đề sau (bạn có thể trả lời ngắn gọn theo số thứ tự):

1.  **Về nguồn tin tức:** Bạn dự định lấy tin tức từ đâu? (Cào dữ liệu từ web, dùng RSS feed của CafeF, hay có API trả phí nào không?). Tần suất cập nhật là Real-time (ngay lập tức) hay Batch (chạy một lần vào cuối ngày)?
2.  **Về AI Agent:** Bạn muốn Agent này đưa ra **khuyến nghị Mua/Bán (Actionable Advice)** rõ ràng, hay chỉ dừng ở mức **tổng hợp trung lập** (ví dụ: "RSI đang quá mua, tin tức đang tích cực")?
3.  **Về Dashboard:** "Xuất ra dashboard" ở đây là bạn muốn làm một Web App tương tác (như Streamlit, Gradio, React/Next.js) hay chỉ là một file báo cáo tĩnh?
4.  **Về Người dùng mục tiêu:** Công cụ này phục vụ cho cá nhân bạn dùng nội bộ, hay bạn định đóng gói thành sản phẩm (SaaS/Bot Telegram) cho nhiều người dùng khác?
