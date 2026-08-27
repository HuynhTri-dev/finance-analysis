from fastapi import FastAPI, HTTPException
from vnstock.api.quote import Quote
import pandas as pd
from datetime import datetime, timedelta

app = FastAPI(
    title="Vnstock API Sample", 
    description="Sample REST API using FastAPI and Vnstock",
    version="1.0.0"
)

# Danh sách một vài mã cổ phiếu mẫu (VN30)
SAMPLE_TICKERS = ["FPT", "ACB", "TCB", "VCB", "VNM", "HPG", "VIC", "SSI"]

@app.get("/")
def read_root():
    return {"message": "Welcome to Vnstock API Sample. Truy cập /docs để xem Swagger UI."}

@app.get("/api/stocks", tags=["Stocks"])
def get_stocks_list():
    """
    Lấy danh sách các mã cổ phiếu mẫu.
    """
    return {
        "total": len(SAMPLE_TICKERS),
        "data": [{"symbol": ticker} for ticker in SAMPLE_TICKERS]
    }

@app.get("/api/stocks/{symbol}", tags=["Stocks"])
def get_stock_detail(
    symbol: str, 
    start: str = None, 
    end: str = None, 
    interval: str = "1D"
):
    """
    Lấy dữ liệu lịch sử giá của 1 mã cổ phiếu (mặc định lấy 30 ngày gần nhất nếu không truyền tham số).
    
    - **symbol**: Mã cổ phiếu (VD: FPT, ACB)
    - **start**: Ngày bắt đầu định dạng YYYY-MM-DD
    - **end**: Ngày kết thúc định dạng YYYY-MM-DD
    - **interval**: Khung thời gian (VD: 1D, 1W, 1M)
    """
    symbol = symbol.upper()
    
    # Thiết lập ngày mặc định nếu không có
    if not end:
        end = datetime.now().strftime("%Y-%m-%d")
    if not start:
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        # Khởi tạo đối tượng Quote theo API chuẩn mới của vnstock
        quote = Quote(symbol=symbol, source='VCI')
        df = quote.history(start=start, end=end, interval=interval)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho mã {symbol} trong khoảng thời gian {start} đến {end}")
            
        # Xử lý dữ liệu DataFrame: thay NaN/NaT bằng None để có thể parse sang JSON hợp lệ
        df = df.where(pd.notnull(df), None)
        
        # Chuyển đổi một số cột datetime về dạng chuỗi nếu cần thiết
        if 'time' in df.columns:
            df['time'] = df['time'].astype(str)
            
        records = df.to_dict(orient="records")
        
        return {
            "symbol": symbol,
            "start": start,
            "end": end,
            "interval": interval,
            "total_records": len(records),
            "data": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
