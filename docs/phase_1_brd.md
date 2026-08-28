# Business Requirements Document (BRD)

## 1. Project Information
- **Project Name:** Personal AI Financial Analyst Dashboard
- **Document Date:** 2026-08-28
- **Requester / Sponsor:** User
- **Version:** 1.0

## 2. Business Context & Problem Statement
Hiện tại, việc tổng hợp thông tin để phân tích xu hướng của một cổ phiếu đòi hỏi nhà đầu tư phải tự thu thập dữ liệu kỹ thuật từ các nền tảng (như vnstock) và đọc/lọc tin tức thủ công từ nhiều nguồn báo chí khác nhau. Việc này tốn rất nhiều thời gian, dễ bỏ sót thông tin quan trọng và nhà đầu tư dễ bị ảnh hưởng bởi cảm xúc cá nhân khi xử lý quá nhiều luồng tin tức hỗn loạn trước và trong phiên giao dịch.

## 3. Business Objectives
- **Objective 1:** Tự động hóa quá trình thu thập dữ liệu giá chứng khoán (qua vnstock) và tin tức liên quan theo lịch trình cố định (sáng, trưa, tối) để phục vụ cho các phiên giao dịch gần nhất.
- **Objective 2:** Tiết kiệm đáng kể thời gian research thủ công bằng cách sử dụng AI Agent để tổng hợp, đọc hiểu văn bản báo chí và đánh giá tỷ lệ tác động (tăng/giảm) lên cổ phiếu một cách khách quan.
- **Objective 3:** Cung cấp một giao diện (Dashboard) tập trung duy nhất (Single-Page Application) để xem dữ liệu, tương tác với AI và đọc tài liệu PDF, giúp việc ra quyết định nhanh chóng và tinh gọn.

## 4. Stakeholders
| Role | Name / Department | Primary Need | Level of Influence |
|---|---|---|---|
| End-User (Investor) | User | Cần thông tin tổng hợp nhanh, chính xác, không thiên vị để hỗ trợ giao dịch cá nhân. Không cần AI khuyên mua/bán. | High |
| System Admin/Dev | User | Hệ thống dễ code, dễ bảo trì, crawl tin tức ổn định, chi phí vận hành thấp. | High |

## 5. Expected Benefits / ROI
- **Quantitative:** Tiết kiệm từ 1-2 giờ mỗi ngày cho việc đọc tin tức và đối chiếu số liệu.
- **Qualitative:** Cải thiện chất lượng quyết định đầu tư nhờ loại bỏ yếu tố cảm xúc (AI đánh giá trung lập); có góc nhìn đa chiều nhờ kết hợp cả PTKT và Phân tích tin tức (Sentiment Analysis).

## 6. High-Level Scope
Hệ thống là một ứng dụng Web (Single Page) cá nhân nội bộ, bao gồm:
- Module Data Ingestion (vnstock cho giá chứng khoán, Crawler/RSS cho tin tức theo lịch).
- Module AI Agent để phân tích tin tức và PTKT, đưa ra xác suất xu hướng (không đưa ra khuyến nghị mua bán).
- Giao diện người dùng gồm Sidebar (Navbar) bên trái, AI Agent bên phải, và Dashboard/PDF Viewer ở trung tâm.

## 7. Constraints & Assumptions
- **Constraints:** Dự án chạy nội bộ, ưu tiên tính năng nhanh gọn. Crawler chỉ chạy theo schedule (sáng, trưa, tối) không chạy Real-time để tránh bị chặn IP và tiết kiệm tài nguyên. AI phải bị cấm đưa ra lời khuyên Mua/Bán rõ ràng.
- **Assumptions:** Các nguồn tin tức không thay đổi cấu trúc quá thường xuyên (nếu dùng HTML scraper) hoặc hỗ trợ RSS ổn định; API vnstock hoạt động tốt; LLM đủ thông minh để hiểu ngữ cảnh tài chính Việt Nam.

## 8. High-Level Risks
| Risk | Likelihood | Impact | Preliminary Mitigation |
|---|---|---|---|
| Crawler bị chặn (IP Blocked) / Thay đổi cấu trúc | Medium | High | Chạy crawler theo lịch (schedule) với tần suất thấp, ưu tiên sử dụng RSS thay vì cào HTML thuần túy. |
| AI Agent bị ảo giác (Hallucination) hoặc khuyên bậy | Medium | High | Thiết lập System Prompt kỹ lưỡng, ép buộc Agent chỉ tổng hợp và phân tích dựa trên dữ liệu được cấp, tuyệt đối cấm đưa ra lời khuyên Mua/Bán (Guardrails). |

## 9. Approvals
| Role | Name | Date | Signature / Status |
|---|---|---|---|
| Product Owner | User | 2026-08-28 | Pending Approval |
