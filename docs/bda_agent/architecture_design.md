# THIẾT KẾ KIẾN TRÚC & WORKFLOW: FINANCE ANALYSIS

*(Tài liệu Thiết kế Kiến trúc & Giải pháp theo Kỹ thuật BDA / Solution Architecture Blueprint)*

---

## 1. Tổng quan Kiến trúc Hệ thống (System Architecture)

Hệ thống **Finance Analysis** được thiết kế theo mô hình **Modular Service-Oriented Architecture** trên nền tảng FastAPI (Python Backend), nhằm phân tách rõ ràng 3 trục xử lý:

1. **Xử lý tài liệu phi cấu trúc:** Chuyển đổi PDF BCTC sang Markdown thông qua `Docling`.
2. **Tính toán định lượng:** Thu thập OHLCV qua `vnstock`, tính toán F-Score và Risk Scores (`BUY_RISK`, `SELL_RISK`) lưu vào `RiskAnalysisCache`.
3. **Điều phối mô hình AI:** Sử dụng `Ollama` (local `llama3.1` / `qwen2.5`) để phân tích ngữ cảnh và tổng hợp báo cáo.

```mermaid
flowchart TD
    %% Khai báo các node
    Client([Client / Frontend UI])
    
    subgraph Backend [FastAPI Backend - Finance Analysis]
        API[API Router / Controller]
        
        subgraph CoreServices [Core Analysis Services]
            DocProcessor[Document Processor  Docling Engine]
            LLMOrchestrator[LLM Orchestrator  Ollama Client]
            RiskEngine[Risk Scoring Engine  Technical Indicators]
            DataFetcher[Market Data Fetcher  vnstock]
        end
    end
    
    subgraph DataStorage [Data & Cache Storage]
        DB[(PostgreSQL / SQLite)]
        Cache[(RiskAnalysisCache Table)]
    end
    
    subgraph External [External Services]
        Ollama[Ollama Local API  llama3.1 / qwen2.5]
        Market[Thị trường Chứng khoán / vnstock]
    end

    %% Luồng kết nối
    Client -->|1. Upload PDF / Tra cứu / Chat| API
    API --> DocProcessor
    API --> LLMOrchestrator
    API --> RiskEngine
    
    DocProcessor -->|2. Parse PDF to Markdown| LLMOrchestrator
    
    RiskEngine -->|Tra cứu Cache EOD| Cache
    Cache -.->|Cache Miss| DataFetcher
    DataFetcher -->|Pull OHLCV| Market
    DataFetcher -->|Dataframe 252 phiên| RiskEngine
    RiskEngine -->|Lưu kết quả| Cache
    
    LLMOrchestrator -->|3. Prompt + Markdown Context| Ollama
    Ollama -->|Markdown Report / Chat Q&A| LLMOrchestrator
    LLMOrchestrator -->|4. Phản hồi kết quả| API
    API --> Client
```

---

## 2. Thiết kế Luồng Dữ liệu (Workflows & Sequence Diagrams)

### 2.1. Workflow 1: Bóc tách Báo cáo Tài chính (Fundamental Flow)

Xử lý trích xuất văn bản và bảng biểu từ file PDF người dùng tải lên.

```mermaid
sequenceDiagram
    actor User as Nhà đầu tư
    participant API as FastAPI Router
    participant Docling as DocProcessor (Docling)
    participant Ollama as Ollama API
    
    User->>API: POST /api/finance/upload-bctc (File PDF)
    API->>Docling: Parse layout & bảng biểu BCTC
    Note over Docling: Giữ nguyên cấu trúc Bảng CĐKT, KQKD, LCTT
    Docling-->>API: Trả về chuỗi Markdown cấu trúc
    API->>Ollama: Gửi Markdown trích xuất các chỉ số cốt lõi
    Ollama-->>API: Trả về JSON (Doanh thu, LNST, EPS, ROA, CFO...)
    API-->>User: Hiển thị bảng tổng hợp số liệu BCTC
```

### 2.2. Workflow 2: Phân tích Rủi ro Kỹ thuật & Caching (Technical Flow)

Xử lý tính toán điểm rủi ro và tận dụng cơ chế bộ nhớ đệm `RiskAnalysisCache`.

```mermaid
sequenceDiagram
    participant API as FastAPI Router
    participant Cache as RiskAnalysisCache DB
    participant Fetcher as Market Data Fetcher (vnstock)
    participant Engine as Risk Scoring Engine
    
    API->>Cache: SELECT * FROM risk_analysis_cache WHERE symbol = :symbol AND as_of_date = Today
    alt Có trong Cache (Cache Hit)
        Cache-->>API: Trả về buy_score, sell_score, f_score, scenario
    else Chưa có hoặc force_refresh (Cache Miss)
        API->>Fetcher: Kéo dữ liệu OHLCV (tối thiểu 252 phiên gần nhất)
        Fetcher-->>Engine: Trả về DataFrame nến ngày
        Engine->>Engine: Tính toán Indicators (RSI, MACD phân kỳ, ATR, Vol Ratio)<br/>Định lượng BUY_RISK & SELL_RISK (0-100)
        Engine->>Cache: Lưu kết quả vào bảng risk_analysis_cache
        Cache-->>API: Trả về kết quả mới cập nhật
    end
```

### 2.3. Workflow 3: Sinh Báo cáo Đa chiều Tổng hợp (Multi-Dimensional Report)

Kết hợp cả 2 trục Fundamental và Technical để Ollama sinh báo cáo toàn cảnh.

```mermaid
flowchart LR
    A[Yêu cầu Phân tích Mã XYZ] --> B{Kiểm tra dữ liệu}
    B -->|Đã có PDF MD| C[Trích xuất Fundamental Summary]
    B -->|Chưa có PDF| D[Sử dụng chỉ số định lượng cơ bản có sẵn]
    
    C --> E[Đọc điểm Risk từ Cache DB]
    D --> E
    
    E --> F[Ghép System Prompt + Context]
    
    F -->|System Prompt| G["Đóng vai Chuyên viên Phân tích...<br/>- Dữ liệu Kỹ thuật: BUY_RISK, SELL_RISK<br/>- Dữ liệu BCTC: [Markdown]<br/>Xuất báo cáo 3 phần chuẩn hóa."]
    
    G --> H((Ollama Engine))
    H --> I[Báo cáo Toàn diện cho Nhà đầu tư]
```

---

## 3. Bản đồ Thành phần & Module Kỹ thuật Cần Phát triển

| Module | Đường dẫn file | Công nghệ / Thư viện | Trách nhiệm chính | Trạng thái hiện tại |
| --- | --- | --- | --- | :---: |
| **Technical Risk Engine** | `backend/app/services/risk_scoring.py`<br>`backend/app/services/technical_indicators.py` | `numpy`, `pandas` | Tính RSI, MACD, phân kỳ, Price Z, Volume ratio, chấm điểm `BUY_RISK` / `SELL_RISK` | **Đã hoàn thiện (90%)** |
| **Risk Cache Model** | `backend/app/models.py` (`RiskAnalysisCache`) | `SQLAlchemy` | Bảng lưu trữ kết quả phân tích theo mã và ngày | **Đã hoàn thiện (100%)** |
| **Fundamental Service** | `backend/app/services/fundamental_indicators.py` | `python`, `vnstock` | Tính toán Piotroski F-Score (0-9) | **Đã hoàn thiện (90%)** |
| **Document Processor** | `backend/app/services/pdf_processor.py` *(Mới)* | `docling` | Parse PDF BCTC sang chuỗi Markdown bảo toàn bảng biểu | **Chưa triển khai (0%)** |
| **LLM Orchestrator** | `backend/app/services/ai_orchestrator_service.py` | `ollama`, `LLMGateway` | Tích hợp prompt đọc Markdown BCTC và prompt tổng hợp báo cáo | **Đã có khung (75%)** |
| **Finance Analysis Router** | `backend/app/routers/finance_analysis_router.py` *(Mới)* | `FastAPI`, `Pydantic` | Cung cấp endpoints: `/upload-bctc`, `/risk/{symbol}`, `/report`, `/chat` | **Chưa triển khai (0%)** |
