import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# Add backend directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.risk_scoring import RiskScoringService

def run_test():
    try:
        import vnstock
    except ImportError:
        print("Vnstock3 is not installed or available. Using dummy data.")
        # Create dummy data
        dates = pd.date_range(end=datetime.today(), periods=100)
        df = pd.DataFrame({
            'time': dates,
            'open': [100]*100,
            'high': [105]*100,
            'low': [95]*100,
            'close': [102]*100,
            'volume': [200000]*100
        })
        df.set_index('time', inplace=True)
    else:
        print("Fetching data from Vnstock (v4)...")
        try:
            from vnstock import Quote
            # Sử dụng Quote thay vì Vnstock()
            df = Quote().history(symbol='FPT', start='2023-01-01', end=datetime.today().strftime('%Y-%m-%d'))
            # Format columns
            df.rename(columns=str.lower, inplace=True)
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu: {e}")
            return

    print(f"Đã lấy {len(df)} dòng dữ liệu.")
    
    # Run engine
    engine = RiskScoringService()
    try:
        res = engine.evaluate(df)
        print("=== KẾT QUẢ ĐÁNH GIÁ RỦI RO ===")
        print(f"Ngày: {res['as_of']}")
        print(f"Trạng thái dữ liệu: {res['data_status']}")
        
        print(f"\n[MUA] BUY_RISK: {res['buy_score']} - Mức độ: {res['buy_level']}")
        print(f"Lý do cảnh báo mua: {res['buy_reasons']}")
        
        print(f"\n[BÁN] SELL_RISK: {res['sell_score']} - Mức độ: {res['sell_level']}")
        print(f"Lý do cảnh báo bán: {res['sell_reasons']}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
