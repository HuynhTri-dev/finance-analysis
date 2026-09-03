import pandas as pd
import numpy as np

def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()

def calculate_ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False, min_periods=1).mean()

def calculate_bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0):
    sma = calculate_sma(close, window)
    rolling_std = close.rolling(window=window, min_periods=1).std()
    upper = sma + (rolling_std * num_std)
    lower = sma - (rolling_std * num_std)
    
    # Avoid division by zero
    band_diff = upper - lower
    band_diff = band_diff.replace(0, 1e-9)
    
    pct_b = (close - lower) / band_diff
    bandwidth = band_diff / sma
    
    return sma, upper, lower, pct_b, bandwidth

def calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1/window, adjust=False, min_periods=1).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False, min_periods=1).mean()
    
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = calculate_ema(close, fast)
    ema_slow = calculate_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    macd_histogram = macd_line - signal_line
    return macd_line, signal_line, macd_histogram

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/window, adjust=False, min_periods=1).mean()
    return atr

def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff())
    direction = direction.fillna(0)
    return (direction * volume).cumsum()

def calculate_wicks(open_price: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series):
    eps = 1e-9
    candle_range = (high - low).replace(0, eps)
    
    real_body_top = pd.concat([open_price, close], axis=1).max(axis=1)
    real_body_bottom = pd.concat([open_price, close], axis=1).min(axis=1)
    
    upper_wick = (high - real_body_top) / candle_range
    lower_wick = (real_body_bottom - low) / candle_range
    
    return upper_wick, lower_wick

def calculate_price_z(close: pd.Series, window: int = 20) -> pd.Series:
    sma = calculate_sma(close, window)
    rolling_std = close.rolling(window=window, min_periods=1).std()
    z_score = (close - sma) / rolling_std.replace(0, 1e-9)
    return z_score

def calculate_vol_ratio(volume: pd.Series, window: int = 20) -> pd.Series:
    sma_vol = calculate_sma(volume, window)
    return volume / sma_vol.replace(0, 1e-9)

def detect_divergence(price: pd.Series, indicator: pd.Series, window: int = 20, min_dist: int = 5):
    """
    Hàm phát hiện phân kỳ đơn giản (để chứng minh ý tưởng).
    Trả về 2 chuỗi boolean: bear_div (phân kỳ giảm), bull_div (phân kỳ tăng).
    Trong thực tế cần dùng hàm tìm đỉnh/đáy (scipy.signal.find_peaks).
    """
    bear_div = pd.Series(False, index=price.index)
    bull_div = pd.Series(False, index=price.index)
    
    for i in range(window, len(price)):
        # Xét trong cửa sổ `window`
        p_window = price.iloc[i-window:i+1]
        i_window = indicator.iloc[i-window:i+1]
        
        # Tìm đỉnh
        p_max_idx = p_window.idxmax()
        i_max_idx = i_window.idxmax()
        
        # Phân kỳ giảm: Giá tạo đỉnh mới nhưng Indicator tạo đỉnh thấp hơn
        if p_max_idx == p_window.index[-1] and i_max_idx != i_window.index[-1]:
            # Đảm bảo khoảng cách
            if (p_window.index.get_loc(p_max_idx) - p_window.index.get_loc(i_max_idx)) >= min_dist:
                 bear_div.iloc[i] = True

        # Tìm đáy
        p_min_idx = p_window.idxmin()
        i_min_idx = i_window.idxmin()
        
        # Phân kỳ tăng: Giá tạo đáy mới nhưng Indicator tạo đáy cao hơn
        if p_min_idx == p_window.index[-1] and i_min_idx != i_window.index[-1]:
            if (p_window.index.get_loc(p_min_idx) - p_window.index.get_loc(i_min_idx)) >= min_dist:
                 bull_div.iloc[i] = True
                 
    return bear_div, bull_div

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    # A simplified version of ADX calculation
    up = high.diff()
    down = -low.diff()

    pos_dm = np.where((up > down) & (up > 0), up, 0)
    neg_dm = np.where((down > up) & (down > 0), down, 0)

    pos_dm_series = pd.Series(pos_dm, index=high.index)
    neg_dm_series = pd.Series(neg_dm, index=high.index)

    tr = calculate_atr(high, low, close, window=1)  # True range
    atr = tr.ewm(alpha=1/window, adjust=False).mean()

    pos_di = 100 * (pos_dm_series.ewm(alpha=1/window, adjust=False).mean() / atr.replace(0, 1e-9))
    neg_di = 100 * (neg_dm_series.ewm(alpha=1/window, adjust=False).mean() / atr.replace(0, 1e-9))

    dx = 100 * (abs(pos_di - neg_di) / (pos_di + neg_di).replace(0, 1e-9))
    adx = dx.ewm(alpha=1/window, adjust=False).mean()

    return adx


def calculate_mfi(high: pd.Series, low: pd.Series, close: pd.Series,
                  volume: pd.Series, window: int = 14) -> pd.Series:
    """
    Calculate Money Flow Index (MFI 0-100) as a secondary confirmation for
    momentum/distribution divergence (per high-risk spec §3.1 MFI rule).

    Args:
        high, low, close (pd.Series): OHLC price series.
        volume (pd.Series): Trading volume series.
        window (int): Rolling lookback period (default 14 sessions).

    Returns:
        pd.Series: MFI values in range [0, 100].
    """
    eps = 1e-9
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume

    direction = np.sign(typical_price.diff())
    pos_mf = raw_money_flow.where(direction > 0, 0.0)
    neg_mf = raw_money_flow.where(direction < 0, 0.0)

    pos_mf_sum = pos_mf.rolling(window=window, min_periods=1).sum()
    neg_mf_sum = neg_mf.rolling(window=window, min_periods=1).sum()

    money_ratio = pos_mf_sum / neg_mf_sum.replace(0, eps)
    mfi = 100 - (100 / (1 + money_ratio))
    return mfi


def detect_structure(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    ema_window: int = 21,
    lookback: int = 5,
    vol_ratio_threshold: float = 1.5,
) -> tuple[pd.Series, pd.Series]:
    """
    Detect price structure break (STRUCTURE_DOWN) and structure recovery (STRUCTURE_UP)
    using a pivot-based approach as specified in high-risk-trading-point.md §3.

    STRUCTURE_DOWN: close < EMA(21) after a recent local pivot high, OR
                    close breaks below the lowest low of the past `lookback` sessions
                    with elevated volume.
    STRUCTURE_UP:   close breaks above the high of the most recent strong bearish candle
                    (i.e. a close below its own midpoint) seen in the past `lookback` sessions.

    Args:
        close, high, low, volume (pd.Series): OHLCV series.
        ema_window (int): EMA period for structural baseline (default 21).
        lookback (int): Number of sessions to look back for pivot confirmation.
        vol_ratio_threshold (float): Minimum vol ratio to qualify a breakout.

    Returns:
        Tuple[pd.Series, pd.Series]: (structure_down, structure_up) boolean series.
    """
    ema21 = calculate_ema(close, ema_window)
    vol_ratio = calculate_vol_ratio(volume, 20)

    # ---- STRUCTURE_DOWN -------------------------------------------------------
    # Rolling pivot high: highest high in past `lookback` sessions (confirmed)
    recent_pivot_high = high.rolling(window=lookback, min_periods=lookback).max().shift(1)
    # Break: close is below EMA21 after price was at a local high, OR
    #        closes below 5-session low support with high volume.
    below_ema = close < ema21
    at_recent_pivot = close.shift(lookback) >= recent_pivot_high  # was near pivot
    low_5 = low.rolling(window=lookback, min_periods=lookback).min().shift(1)
    breaks_support = (close < low_5) & (vol_ratio >= vol_ratio_threshold)

    structure_down = below_ema & (at_recent_pivot | breaks_support)

    # ---- STRUCTURE_UP ---------------------------------------------------------
    # The most recent strong bearish candle: close in lower half of its own range
    candle_range = (high - low).replace(0, 1e-9)
    close_in_lower_half = close < (low + candle_range / 2)
    # High of the most recent bearish candle within lookback
    bearish_candle_high = high.where(close_in_lower_half).rolling(
        window=lookback, min_periods=1
    ).max().shift(1)
    # Recovery: current close breaks above that bearish candle's high
    structure_up = close > bearish_candle_high.fillna(method="ffill")

    return structure_down.fillna(False), structure_up.fillna(False)


def calculate_price_return_percentile(close: pd.Series, lookback: int = 252) -> pd.Series:
    """
    Calculate the rolling percentile rank of the single-session return
    against the past `lookback` sessions.  Used to flag panic volatility
    when the session return falls in the bottom 5th percentile (per spec §5).

    Args:
        close (pd.Series): Adjusted closing price.
        lookback (int): Rolling window (default 252 sessions = ~1 year).

    Returns:
        pd.Series: Percentile rank [0, 1] of each session's return.
    """
    returns = close.pct_change()

    def _rank(window_arr: np.ndarray) -> float:
        if len(window_arr) < 2:
            return 0.5
        current = window_arr[-1]
        pct = (window_arr[:-1] < current).sum() / (len(window_arr) - 1)
        return float(pct)

    return returns.rolling(window=lookback, min_periods=60).apply(_rank, raw=True)
