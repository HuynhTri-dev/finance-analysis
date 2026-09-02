import pandas as pd
import numpy as np
from typing import Dict, Any

from app.services.technical_indicators import (
    calculate_sma, calculate_ema, calculate_bollinger_bands,
    calculate_rsi, calculate_macd, calculate_atr, calculate_obv,
    calculate_wicks, calculate_price_z, calculate_vol_ratio,
    detect_divergence, calculate_adx
)

class RiskScoringService:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            'min_liquidity': 100000,
            'rsi_window': 14,
            'atr_window': 14,
            'vol_window': 20,
            'price_z_window': 20,
        }

    def compute_features(self, df: pd.DataFrame, benchmark_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Tính toán các đặc trưng (features) cho DataFrame OHLCV
        Yêu cầu df có các cột: open, high, low, close, volume
        """
        if len(df) < 60:
            raise ValueError("INSUFFICIENT_DATA: Tối thiểu 60 phiên dữ liệu")

        df = df.copy()
        
        # 1. Momentum & Divergence
        df['RSI'] = calculate_rsi(df['close'], self.config['rsi_window'])
        macd_line, sig_line, macd_hist = calculate_macd(df['close'])
        df['MACD_HIST'] = macd_hist
        
        # Tính phân kỳ giảm/tăng dựa trên RSI (min_dist=5)
        bear_div, bull_div = detect_divergence(df['close'], df['RSI'], window=20, min_dist=5)
        df['MOM_BEAR_DIV'] = bear_div
        df['MOM_BULL_DIV'] = bull_div

        # 2. Volatility & Extremes
        df['PRICE_Z'] = calculate_price_z(df['close'], self.config['price_z_window'])
        atr = calculate_atr(df['high'], df['low'], df['close'], self.config['atr_window'])
        atr_sma = calculate_sma(atr, 60)
        df['ATR_RATIO'] = atr / atr_sma.replace(0, 1e-9)

        # 3. Volume & Price Action
        df['VOL_RATIO'] = calculate_vol_ratio(df['volume'], self.config['vol_window'])
        upper_wick, lower_wick = calculate_wicks(df['open'], df['high'], df['low'], df['close'])
        df['UPPER_WICK'] = upper_wick
        df['LOWER_WICK'] = lower_wick
        
        # 4. Structure
        ema21 = calculate_ema(df['close'], 21)
        # Giả lập gãy cấu trúc đơn giản: Đóng cửa < EMA21 sau đỉnh và Vol cao (đây là bản đơn giản hoá)
        df['STRUCTURE_DOWN'] = (df['close'] < ema21) & (df['VOL_RATIO'] > 1.5)
        
        ema5 = calculate_ema(df['close'], 5)
        # Hồi phục cấu trúc: Đóng trên EMA5 sau chuỗi giảm
        df['STRUCTURE_UP'] = df['close'] > ema5
        
        # 5. Context
        df['ADX'] = calculate_adx(df['high'], df['low'], df['close'])
        
        # Nếu có benchmark (VNIndex), tính Relative Strength (20 phiên)
        if benchmark_df is not None and not benchmark_df.empty:
            # Sync dates
            idx = df.index.intersection(benchmark_df.index)
            df_ret = df['close'].pct_change(20)
            bench_ret = benchmark_df['close'].pct_change(20)
            df['REL_STRENGTH'] = df_ret.loc[idx] - bench_ret.loc[idx]
        else:
            df['REL_STRENGTH'] = 0.0  # Giả định neutral nếu không có dữ liệu

        return df

    def score_buy_risk(self, row: pd.Series) -> Dict[str, Any]:
        """Tính điểm BUY_RISK cho 1 dòng dữ liệu (1 phiên)"""
        score = 0
        reasons = []
        components = {}
        
        # 1. Động lượng suy kiệt (Max 25)
        if row.get('MOM_BEAR_DIV', False):
            score += 25
            components['momentum'] = 25
            reasons.append("MOM_BEAR_DIV")
        elif row.get('RSI', 50) > 70:
            score += 10
            components['momentum'] = 10
            reasons.append("RSI_OVERBOUGHT")
        else:
            components['momentum'] = 0

        # 2. Phân phối giá–khối lượng (Max 25)
        if row.get('VOL_RATIO', 1.0) >= 2.0 and row.get('UPPER_WICK', 0.0) >= 0.40:
            score += 25
            components['distribution'] = 25
            reasons.append("VOLUME_CLIMAX_UPPER_WICK")
        elif row.get('VOL_RATIO', 1.0) >= 1.5 or row.get('UPPER_WICK', 0.0) >= 0.30:
            score += 10
            components['distribution'] = 10
            reasons.append("PARTIAL_DISTRIBUTION")
        else:
             components['distribution'] = 0
            
        # 3. Biến động/cực trị giá (Max 20)
        if row.get('PRICE_Z', 0) >= 2.0 and row.get('ATR_RATIO', 1.0) >= 1.5:
            score += 20
            components['extremes'] = 20
            reasons.append("PRICE_EXTREME_HIGH_VOLATILITY")
        elif row.get('PRICE_Z', 0) >= 2.0 or row.get('ATR_RATIO', 1.0) >= 1.5:
            score += 8
            components['extremes'] = 8
            reasons.append("ELEVATED_VOLATILITY")
        else:
            components['extremes'] = 0

        # 4. Cấu trúc giá (Max 15)
        if row.get('STRUCTURE_DOWN', False):
            score += 15
            components['structure'] = 15
            reasons.append("STRUCTURE_DOWN")
        else:
            components['structure'] = 0

        # 5. Bối cảnh (Max 15)
        if row.get('REL_STRENGTH', 0.0) < -0.05: # Underperforming 5%
            score += 15
            components['context'] = 15
            reasons.append("WEAK_REL_STRENGTH")
        else:
            components['context'] = 0

        total_score = min(100, score)
        
        # Cổng xác nhận (Confirmation Gate)
        # Chỉ nâng HIGH nếu có cả phân phối/cấu trúc VÀ động lượng/biến động
        dist_struct_ok = (components['distribution'] > 0 or components['structure'] > 0)
        mom_ext_ok = (components['momentum'] > 0 or components['extremes'] > 0)
        
        if total_score >= 75 and not (dist_struct_ok and mom_ext_ok):
            total_score = 74 # Cap at CAUTION

        level = self._get_risk_level(total_score, is_buy=True)
        
        return {
            'buy_score': total_score,
            'buy_level': level,
            'buy_components': components,
            'buy_reasons': reasons
        }

    def score_sell_risk(self, row: pd.Series) -> Dict[str, Any]:
        """Tính điểm SELL_RISK cho 1 dòng dữ liệu (1 phiên)"""
        score = 0
        reasons = []
        components = {}
        
        # 1. Quá bán & Phân kỳ tăng (Max 30)
        if row.get('MOM_BULL_DIV', False) and row.get('RSI', 50) < 35:
            score += 30
            components['oversold'] = 30
            reasons.append("MOM_BULL_DIV")
        elif row.get('RSI', 50) < 30:
            score += 12
            components['oversold'] = 12
            reasons.append("RSI_OVERSOLD")
        else:
            components['oversold'] = 0

        # 2. Capitulation giá-khối lượng (Max 25)
        if row.get('VOL_RATIO', 1.0) >= 2.5 and row.get('LOWER_WICK', 0.0) >= 0.35:
            score += 25
            components['capitulation'] = 25
            reasons.append("CAPITULATION_VOLUME_LOWER_WICK")
        elif row.get('VOL_RATIO', 1.0) >= 2.0:
            score += 10
            components['capitulation'] = 10
            reasons.append("HIGH_SELLING_VOLUME")
        else:
            components['capitulation'] = 0

        # 3. Biến động hoảng loạn (Max 15)
        if row.get('ATR_RATIO', 1.0) >= 1.75 and row.get('PRICE_Z', 0) <= -2.0:
            score += 15
            components['panic'] = 15
            reasons.append("PANIC_VOLATILITY")
        else:
            components['panic'] = 0

        # 4. Xác nhận hồi phục (Max 15)
        if row.get('STRUCTURE_UP', False):
            score += 15
            components['recovery'] = 15
            reasons.append("STRUCTURE_UP")
        else:
            components['recovery'] = 0
            
        # 5. Bối cảnh (Max 15)
        if row.get('REL_STRENGTH', 0.0) > 0.05: # Outperforming
            score += 15
            components['context'] = 15
            reasons.append("STRONG_REL_STRENGTH")
        else:
            components['context'] = 0

        total_score = min(100, score)
        
        # Cổng xác nhận (Confirmation Gate)
        has_capitulation_or_div = (components['oversold'] == 30 or components['capitulation'] == 25)
        has_recovery = (components['recovery'] > 0)
        
        if total_score >= 75 and not (has_capitulation_or_div and has_recovery):
            total_score = 74 # Cap at CAUTION

        level = self._get_risk_level(total_score, is_buy=False)
        
        return {
            'sell_score': total_score,
            'sell_level': level,
            'sell_components': components,
            'sell_reasons': reasons
        }

    def _get_risk_level(self, score: int, is_buy: bool) -> str:
        if score <= 39:
            return 'NORMAL'
        elif score <= 59:
            return 'WATCH'
        elif score <= 74:
            return 'CAUTION'
        else:
            return 'HIGH'

    def evaluate(self, df: pd.DataFrame, as_of: str = None, benchmark_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Đánh giá toàn diện mã cổ phiếu tại thời điểm as_of (mặc định lấy dòng cuối cùng)
        """
        features_df = self.compute_features(df, benchmark_df)
        
        if as_of:
            if as_of not in features_df.index:
                 # Nếu truyền string YYYY-MM-DD
                 try:
                     row = features_df.loc[as_of]
                 except KeyError:
                     # Lấy gần nhất
                     row = features_df.iloc[-1]
            else:
                 row = features_df.loc[as_of]
        else:
            row = features_df.iloc[-1]
            as_of = str(row.name) if row.name else "LATEST"

        buy_res = self.score_buy_risk(row)
        sell_res = self.score_sell_risk(row)
        
        return {
            'as_of': as_of,
            'data_status': 'OK',
            **buy_res,
            **sell_res
        }
