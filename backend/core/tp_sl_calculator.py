"""
Dynamic TP/SL calculation using H4 Swing Points or ATR fallback.
"""

import pandas as pd
import numpy as np
from core.config import settings


def _swing_high(series: pd.Series, n: int) -> float:
    return float(series.rolling(n, center=True).max().dropna().iloc[-1])


def _swing_low(series: pd.Series, n: int) -> float:
    return float(series.rolling(n, center=True).min().dropna().iloc[-1])


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def compute_tp_sl(
    direction: str,          # "LONG" or "SHORT"
    h4_df: pd.DataFrame,     # columns: open, high, low, close, volume
    entry_price: float,
    lookback: int | None = None,
) -> tuple[float, float]:
    """
    Returns (tp_price, sl_price).

    Priority:
      1. H4 Swing High (TP for LONG) / Swing Low (SL for LONG)
      2. ATR-based fallback
    """
    if lookback is None:
        lookback = settings.SWING_LOOKBACK

    try:
        recent = h4_df.tail(lookback * 2 + 1)

        if direction == "LONG":
            tp = _swing_high(recent["high"], lookback)
            sl = _swing_low(recent["low"], lookback)
            # Safety: TP must be above entry, SL must be below
            if tp <= entry_price or sl >= entry_price:
                raise ValueError("Swing points invalid for LONG")
        else:  # SHORT
            sl = _swing_high(recent["high"], lookback)
            tp = _swing_low(recent["low"], lookback)
            if tp >= entry_price or sl <= entry_price:
                raise ValueError("Swing points invalid for SHORT")

    except Exception:
        # ATR fallback
        atr = _atr(h4_df)
        if direction == "LONG":
            tp = entry_price + atr * settings.ATR_TP_MULT
            sl = entry_price - atr * settings.ATR_SL_MULT
        else:
            tp = entry_price - atr * settings.ATR_TP_MULT
            sl = entry_price + atr * settings.ATR_SL_MULT

    return round(tp, 8), round(sl, 8)


def risk_reward_ratio(entry: float, tp: float, sl: float) -> float:
    reward = abs(tp - entry)
    risk = abs(entry - sl)
    return round(reward / risk, 2) if risk > 0 else 0.0
