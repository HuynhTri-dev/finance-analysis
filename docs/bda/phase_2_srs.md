# Software Requirements Specification (SRS)

## 1. Introduction
### 1.1 Purpose
Tài liệu SRS này đặc tả các yêu cầu kỹ thuật và phi chức năng (Non-Functional Requirements) cho hệ thống Personal AI Financial Analyst Dashboard.
### 1.2 Product Scope
Hệ thống là một ứng dụng Web 1 trang (SPA) dành cho cá nhân, tự động thu thập giá chứng khoán (vnstock) và tin tức (Crawler), sau đó sử dụng AI Agent để phân tích tỷ lệ xu hướng cổ phiếu. 

## 2. Overall Description
### 2.1 Product Perspective
Hệ thống hoạt động độc lập (Standalone/Local). Backend viết bằng Python (FastAPI) để xử lý vnstock và AI, Frontend sử dụng công nghệ Web (React/Next.js hoặc Streamlit) để render giao diện SPA.
### 2.2 User Classes
| User Group | Characteristics | Access Rights |
|---|---|---|
| Admin/Investor (Single User) | Nhà đầu tư cá nhân, chạy app trên máy cá nhân hoặc VPS nhỏ. | Toàn quyền sử dụng hệ thống. |

## 3. Non-Functional Requirements (NFRs)

### 3.1 Performance
| ID | Description | Measurable Threshold |
|---|---|---|
| NFR-PRF-001 | Tốc độ phản hồi của AI Agent. | Phản hồi (hoặc bắt đầu streaming text) trong vòng < 5 giây, hoàn thành câu trả lời dưới 30 giây. |
| NFR-PRF-002 | Tốc độ lấy dữ liệu vnstock. | Trả về dữ liệu trong vòng < 2 giây cho một mã. |

### 3.2 Security
| ID | Description | Reference Standard |
|---|---|---|
| NFR-SEC-001 | Bảo mật API Key của LLM (OpenAI/Gemini). | API Key phải được lưu trong biến môi trường (`.env`), tuyệt đối không hardcode trên source code hoặc frontend. |

### 3.3 Availability / Reliability
| ID | Description | Threshold |
|---|---|---|
| NFR-REL-001 | Chống lỗi Crawler. | Nếu Crawler gặp lỗi kết nối (Timeout/404), hệ thống phải tự động retry 3 lần, mỗi lần cách nhau 10s. Nếu vẫn thất bại, ghi Log và bỏ qua, không làm sập toàn bộ hệ thống. |

### 3.4 Usability
| ID | Description | Threshold |
|---|---|---|
| NFR-USE-001 | Trải nghiệm SPA (Single Page Application). | Thao tác chuyển đổi giữa Chart View và PDF View không được làm tải lại (reload) trình duyệt. Cuộc trò chuyện với AI Agent ở panel bên phải không bị mất đi khi chuyển view ở phần trung tâm. |

### 3.5 Compatibility
- Ứng dụng phải hiển thị tốt và không vỡ layout trên trình duyệt Chrome và Safari (Desktop).
- Không yêu cầu tối ưu (Responsive) cho màn hình Mobile trong giai đoạn này vì tính chất phức tạp của biểu đồ và giao diện 3 panel.

## 4. External Interface Requirements
### 4.1 User Interface
Giao diện chia làm 3 phần:
1. **Left Navbar:** Rộng ~15-20% màn hình, chứa danh sách Mã CK yêu thích, Lịch sử chat, Nút cài đặt.
2. **Center View:** Rộng ~50-60% màn hình, hiển thị biểu đồ hoặc PDF viewer.
3. **Right Panel:** Rộng ~20-30% màn hình, giao diện chat với AI.

### 4.2 Software / Third-Party API Interface
- LLM API: Giao tiếp qua HTTP REST/SDK (Gemini/OpenAI).
- vnstock: Gọi trực tiếp qua thư viện Python cục bộ.
