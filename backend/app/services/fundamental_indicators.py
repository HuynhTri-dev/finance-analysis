import logging
from typing import Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class FundamentalService:
    def __init__(self):
        pass

    def calculate_f_score(self, symbol: str) -> Optional[int]:
        """
        Tính điểm Piotroski F-Score (0-9) dựa trên báo cáo tài chính.
        Do giới hạn của API vnstock trả về các chỉ số có sẵn, ta sẽ
        sử dụng `finance.ratio` hoặc `finance.report` để tính.
        Nếu thiếu data, trả về None.
        """
        try:
            # Trong thực tế với vnstock v4:
            # from vnstock import Company
            # df_ratio = Company().financial_ratio(symbol=symbol, period='year')
            # ...
            # Để demo luồng hoạt động mà không bị crash do API:
            logger.info(f"Đang tính F-Score cho {symbol}...")
            
            # TODO: Triển khai logic cào BCTC thật bằng vnstock
            # Tạm thời sinh F-Score giả định ngẫu nhiên dựa trên độ dài chuỗi để dễ test UI
            import hashlib
            hash_val = int(hashlib.md5(symbol.encode('utf-8')).hexdigest(), 16)
            mock_f_score = hash_val % 10  # 0 to 9
            
            return mock_f_score
            
        except Exception as e:
            logger.error(f"Lỗi khi tính F-Score cho {symbol}: {e}")
            return None

    def get_valuation_metrics(self, symbol: str) -> Dict[str, Any]:
        """Lấy các chỉ số định giá cơ bản (P/E, P/B, ROE...)"""
        try:
            # df = Company().financial_ratio(symbol=symbol)
            return {
                "pe": 15.2,
                "pb": 1.8,
                "roe": 18.5,
                "debt_to_equity": 0.6
            }
        except Exception as e:
            logger.error(f"Lỗi lấy định giá cho {symbol}: {e}")
            return {}

fundamental_service = FundamentalService()
