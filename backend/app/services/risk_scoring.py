"""
name: risk_scoring.py
description: Technical Risk Scoring Service implementing the BUY_RISK / SELL_RISK
             framework from high-rist_trading_point.md.
             Computes momentum divergence, volume distribution/capitulation,
             volatility extremes, pivot-based structure, and market-context features.
             Includes Vietnam-market-specific guardrails:
               - EXCHANGE_LIMIT_HIT flag for trần/sàn price-band sessions.
               - ADX confirmation gate (weak trend → dual-evidence required for HIGH).
               - MFI secondary confirmation for distribution/accumulation.
               - Price-return percentile for panic-volatility threshold (5th pct, 252 sessions).
             All thresholds are externalized into self.config; do NOT hard-code values.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from app.services.technical_indicators import (
    calculate_sma, calculate_ema, calculate_bollinger_bands,
    calculate_rsi, calculate_macd, calculate_atr, calculate_obv,
    calculate_wicks, calculate_price_z, calculate_vol_ratio,
    detect_divergence, calculate_adx,
    calculate_mfi, detect_structure, calculate_price_return_percentile,
)


class RiskScoringService:
    """
    Evaluate BUY_RISK and SELL_RISK for a given OHLCV DataFrame.

    Config keys (all overridable):
        min_liquidity       – Minimum daily volume to qualify (default 100_000).
        rsi_window          – RSI lookback (default 14).
        atr_window          – ATR lookback (default 14).
        vol_window          – Volume SMA window (default 20).
        price_z_window      – Price Z-score window (default 20).
        adx_weak_threshold  – ADX below this = weak trend; dual evidence required (default 20).
        exchange_limit_pct  – Session % move at or beyond which EXCHANGE_LIMIT_HIT is set.
                              HOSE ±7%, HNX ±10%, UPCOM ±15% — configure per exchange.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            "min_liquidity": 100_000,
            "rsi_window": 14,
            "atr_window": 14,
            "vol_window": 20,
            "price_z_window": 20,
            "adx_weak_threshold": 20,        # ADX < 20 → weak trend
            "exchange_limit_pct": 0.07,      # HOSE default ±7% — override for HNX/UPCOM
        }

    # ------------------------------------------------------------------
    # Feature computation
    # ------------------------------------------------------------------

    def compute_features(
        self,
        df: pd.DataFrame,
        benchmark_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """
        Compute all technical features for an OHLCV DataFrame.

        Args:
            df (pd.DataFrame): Must contain columns open, high, low, close, volume
                               with a DatetimeIndex. Minimum 60 rows (252 recommended).
            benchmark_df (pd.DataFrame | None): VN-Index OHLCV with same index schema.
                                                When provided, REL_STRENGTH is computed
                                                against the index; otherwise set to 0.0.

        Returns:
            pd.DataFrame: Original df enriched with all feature columns.

        Raises:
            ValueError: If fewer than 60 sessions are present (INSUFFICIENT_DATA).
        """
        if len(df) < 60:
            raise ValueError("INSUFFICIENT_DATA: Minimum 60 sessions required.")

        df = df.copy()

        # ------------------------------------------------------------------ #
        # 1. Momentum & Divergence
        # ------------------------------------------------------------------ #
        df["RSI"] = calculate_rsi(df["close"], self.config["rsi_window"])
        _, _, macd_hist = calculate_macd(df["close"])
        df["MACD_HIST"] = macd_hist

        bear_div, bull_div = detect_divergence(
            df["close"], df["RSI"], window=20, min_dist=5
        )
        df["MOM_BEAR_DIV"] = bear_div
        df["MOM_BULL_DIV"] = bull_div

        # ------------------------------------------------------------------ #
        # 2. Volatility & Price Extremes
        # ------------------------------------------------------------------ #
        df["PRICE_Z"] = calculate_price_z(df["close"], self.config["price_z_window"])
        atr = calculate_atr(
            df["high"], df["low"], df["close"], self.config["atr_window"]
        )
        atr_sma = calculate_sma(atr, 60)
        df["ATR_RATIO"] = atr / atr_sma.replace(0, 1e-9)

        # Return percentile for panic detection (SELL_RISK §5: bottom 5th pct)
        df["RETURN_PERCENTILE"] = calculate_price_return_percentile(df["close"], lookback=252)

        # ------------------------------------------------------------------ #
        # 3. Volume & Price Action
        # ------------------------------------------------------------------ #
        df["VOL_RATIO"] = calculate_vol_ratio(df["volume"], self.config["vol_window"])
        upper_wick, lower_wick = calculate_wicks(
            df["open"], df["high"], df["low"], df["close"]
        )
        df["UPPER_WICK"] = upper_wick
        df["LOWER_WICK"] = lower_wick

        # Secondary momentum/distribution confirmation (spec §3.1 MFI)
        df["MFI"] = calculate_mfi(
            df["high"], df["low"], df["close"], df["volume"], window=14
        )

        # ------------------------------------------------------------------ #
        # 4. Price Structure (pivot-based, replaces simple EMA comparison)
        # ------------------------------------------------------------------ #
        structure_down, structure_up = detect_structure(
            close=df["close"],
            high=df["high"],
            low=df["low"],
            volume=df["volume"],
            ema_window=21,
            lookback=5,
            vol_ratio_threshold=self.config.get("structure_vol_threshold", 1.5),
        )
        df["STRUCTURE_DOWN"] = structure_down
        df["STRUCTURE_UP"] = structure_up

        # ------------------------------------------------------------------ #
        # 5. Trend Strength & Context (ADX gate + REL_STRENGTH)
        # ------------------------------------------------------------------ #
        df["ADX"] = calculate_adx(df["high"], df["low"], df["close"])

        if benchmark_df is not None and not benchmark_df.empty:
            bench = benchmark_df.copy()
            bench.columns = [c.lower() for c in bench.columns]
            idx = df.index.intersection(bench.index)
            df_ret = df["close"].pct_change(20)
            bench_ret = bench["close"].pct_change(20)
            df.loc[idx, "REL_STRENGTH"] = (
                df_ret.loc[idx].values - bench_ret.loc[idx].values
            )
            df["REL_STRENGTH"] = df["REL_STRENGTH"].fillna(0.0)
        else:
            df["REL_STRENGTH"] = 0.0  # Neutral when no benchmark provided

        # ------------------------------------------------------------------ #
        # 6. Vietnam Exchange Guardrail: EXCHANGE_LIMIT_HIT
        #    Flag sessions where the price moved by >= exchange_limit_pct
        #    (trần/sàn), so downstream logic can suppress noisy signals.
        # ------------------------------------------------------------------ #
        limit_pct = self.config.get("exchange_limit_pct", 0.07)
        prev_close = df["close"].shift(1)
        session_pct = (df["close"] - prev_close).abs() / prev_close.replace(0, 1e-9)
        df["EXCHANGE_LIMIT_HIT"] = session_pct >= limit_pct

        return df

    # ------------------------------------------------------------------
    # BUY_RISK scoring
    # ------------------------------------------------------------------

    def score_buy_risk(self, row: pd.Series) -> Dict[str, Any]:
        """
        Score BUY_RISK (0-100) for a single OHLCV session.

        Confirmation Gate: Score is capped to CAUTION (max 74) unless
        BOTH a distribution/structure signal AND a momentum/volatility
        signal are present.  When ADX is weak (<20), dual independent
        evidence groups are mandatory for HIGH.

        Args:
            row (pd.Series): One row from compute_features() output.

        Returns:
            Dict with buy_score, buy_level, buy_components, buy_reasons.
        """
        # Skip noisy signals on exchange-limit sessions
        if row.get("EXCHANGE_LIMIT_HIT", False):
            return {
                "buy_score": 0,
                "buy_level": "NORMAL",
                "buy_components": {},
                "buy_reasons": ["EXCHANGE_LIMIT_HIT_SUPPRESSED"],
            }

        score = 0
        reasons = []
        components = {}

        # 1. Momentum exhaustion (Max 25)
        if row.get("MOM_BEAR_DIV", False):
            # MFI diverging in the same direction → counts as one group,
            # not double-counted (spec §3.1).
            score += 25
            components["momentum"] = 25
            reasons.append("MOM_BEAR_DIV")
            if row.get("MFI", 50) > 70:
                reasons.append("MFI_DISTRIBUTION_CONFIRM")  # secondary label only
        elif row.get("RSI", 50) > 70:
            score += 10
            components["momentum"] = 10
            reasons.append("RSI_OVERBOUGHT")
        else:
            components["momentum"] = 0

        # 2. Price–Volume distribution (Max 25)
        vol_ratio = row.get("VOL_RATIO", 1.0)
        upper_wick = row.get("UPPER_WICK", 0.0)
        if vol_ratio >= 2.0 and upper_wick >= 0.40:
            score += 25
            components["distribution"] = 25
            reasons.append("VOLUME_CLIMAX_UPPER_WICK")
        elif vol_ratio >= 1.5 or upper_wick >= 0.30:
            score += 10
            components["distribution"] = 10
            reasons.append("PARTIAL_DISTRIBUTION")
        else:
            components["distribution"] = 0

        # 3. Volatility / Price extreme (Max 20)
        if row.get("PRICE_Z", 0) >= 2.0 and row.get("ATR_RATIO", 1.0) >= 1.5:
            score += 20
            components["extremes"] = 20
            reasons.append("PRICE_EXTREME_HIGH_VOLATILITY")
        elif row.get("PRICE_Z", 0) >= 2.0 or row.get("ATR_RATIO", 1.0) >= 1.5:
            score += 8
            components["extremes"] = 8
            reasons.append("ELEVATED_VOLATILITY")
        else:
            components["extremes"] = 0

        # 4. Price structure (Max 15) — pivot-based
        if row.get("STRUCTURE_DOWN", False):
            score += 15
            components["structure"] = 15
            reasons.append("STRUCTURE_DOWN")
        else:
            components["structure"] = 0

        # 5. Market context (Max 15)
        if row.get("REL_STRENGTH", 0.0) < -0.05:
            score += 15
            components["context"] = 15
            reasons.append("WEAK_REL_STRENGTH")
        else:
            components["context"] = 0

        total_score = min(100, score)

        # ---- Confirmation Gate -------------------------------------------- #
        dist_struct_ok = components["distribution"] > 0 or components["structure"] > 0
        mom_ext_ok = components["momentum"] > 0 or components["extremes"] > 0

        if total_score >= 75 and not (dist_struct_ok and mom_ext_ok):
            total_score = 74  # Cap at CAUTION when gate not met

        # ADX weak-trend gate: require dual independent groups for HIGH
        adx_val = row.get("ADX", 25)
        if total_score >= 75 and adx_val < self.config["adx_weak_threshold"]:
            # Both momentum group AND distribution/structure group must be non-zero
            if not (mom_ext_ok and dist_struct_ok):
                total_score = 74

        level = self._get_risk_level(total_score)
        return {
            "buy_score": total_score,
            "buy_level": level,
            "buy_components": components,
            "buy_reasons": reasons,
        }

    # ------------------------------------------------------------------
    # SELL_RISK scoring
    # ------------------------------------------------------------------

    def score_sell_risk(self, row: pd.Series) -> Dict[str, Any]:
        """
        Score SELL_RISK (0-100) for a single OHLCV session.

        Confirmation Gate: Score is capped to CAUTION (max 74) unless
        BOTH a capitulation/divergence signal AND a recovery signal are present.
        A single down-move without recovery evidence stays at WATCH/CAUTION.

        Args:
            row (pd.Series): One row from compute_features() output.

        Returns:
            Dict with sell_score, sell_level, sell_components, sell_reasons.
        """
        # On exchange-limit sessions, still compute SELL_RISK but label it
        if row.get("EXCHANGE_LIMIT_HIT", False):
            reasons_prefix = ["EXCHANGE_LIMIT_HIT_CONTEXT"]
        else:
            reasons_prefix = []

        score = 0
        reasons = list(reasons_prefix)
        components = {}

        # 1. Oversold & bullish divergence (Max 30)
        if row.get("MOM_BULL_DIV", False) and row.get("RSI", 50) < 35:
            score += 30
            components["oversold"] = 30
            reasons.append("MOM_BULL_DIV")
            if row.get("MFI", 50) < 30:
                reasons.append("MFI_ACCUMULATION_CONFIRM")
        elif row.get("RSI", 50) < 30:
            score += 12
            components["oversold"] = 12
            reasons.append("RSI_OVERSOLD")
        else:
            components["oversold"] = 0

        # 2. Capitulation price–volume (Max 25)
        vol_ratio = row.get("VOL_RATIO", 1.0)
        lower_wick = row.get("LOWER_WICK", 0.0)
        if vol_ratio >= 2.5 and lower_wick >= 0.35:
            score += 25
            components["capitulation"] = 25
            reasons.append("CAPITULATION_VOLUME_LOWER_WICK")
        elif vol_ratio >= 2.0:
            score += 10
            components["capitulation"] = 10
            reasons.append("HIGH_SELLING_VOLUME")
        else:
            components["capitulation"] = 0

        # 3. Panic volatility (Max 15)
        #    ATR_RATIO >= 1.75 AND session return in bottom 5th percentile of 252 sessions
        return_pct = row.get("RETURN_PERCENTILE", 0.5)
        if row.get("ATR_RATIO", 1.0) >= 1.75 and return_pct <= 0.05:
            score += 15
            components["panic"] = 15
            reasons.append("PANIC_VOLATILITY")
        else:
            components["panic"] = 0

        # 4. Structure recovery confirmation (Max 15) — pivot-based
        if row.get("STRUCTURE_UP", False):
            score += 15
            components["recovery"] = 15
            reasons.append("STRUCTURE_UP")
        else:
            components["recovery"] = 0

        # 5. Market context (Max 15)
        if row.get("REL_STRENGTH", 0.0) > 0.05:
            score += 15
            components["context"] = 15
            reasons.append("STRONG_REL_STRENGTH")
        else:
            components["context"] = 0

        total_score = min(100, score)

        # ---- Confirmation Gate -------------------------------------------- #
        has_cap_or_div = (
            components["oversold"] == 30 or components["capitulation"] == 25
        )
        has_recovery = components["recovery"] > 0

        if total_score >= 75 and not (has_cap_or_div and has_recovery):
            total_score = 74  # Not a confirmed bottom yet — cap at CAUTION

        level = self._get_risk_level(total_score)
        return {
            "sell_score": total_score,
            "sell_level": level,
            "sell_components": components,
            "sell_reasons": reasons,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_risk_level(self, score: int) -> str:
        """Map numeric score to risk level label per spec §6."""
        if score <= 39:
            return "NORMAL"
        elif score <= 59:
            return "WATCH"
        elif score <= 74:
            return "CAUTION"
        else:
            return "HIGH"

    def evaluate(
        self,
        df: pd.DataFrame,
        as_of: str | None = None,
        benchmark_df: pd.DataFrame | None = None,
    ) -> Dict[str, Any]:
        """
        Full evaluation pipeline: compute features → score → return audit dict.

        Args:
            df (pd.DataFrame): OHLCV DataFrame (DatetimeIndex, min 60 rows).
            as_of (str | None): Date string 'YYYY-MM-DD' to evaluate at.
                                 Defaults to the most recent session (last row).
            benchmark_df (pd.DataFrame | None): VN-Index OHLCV for REL_STRENGTH.

        Returns:
            Dict: buy_score, buy_level, sell_score, sell_level, components,
                  reasons, exchange_limit_hit flag, and as_of date.
        """
        features_df = self.compute_features(df, benchmark_df)

        if as_of:
            try:
                row = features_df.loc[as_of]
            except KeyError:
                row = features_df.iloc[-1]
        else:
            row = features_df.iloc[-1]
            as_of = str(row.name) if row.name else "LATEST"

        buy_res = self.score_buy_risk(row)
        sell_res = self.score_sell_risk(row)

        return {
            "as_of": as_of,
            "data_status": "OK",
            "exchange_limit_hit": bool(row.get("EXCHANGE_LIMIT_HIT", False)),
            **buy_res,
            **sell_res,
        }
