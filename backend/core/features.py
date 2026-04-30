"""
Feature engineering: builds all 85 features from OHLCV + optional futures data.
Approximates SMC/Wyckoff/OFI features from price action where tick data is unavailable.
"""

import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator


def engineer_features(
    h1_df: pd.DataFrame,
    h4_df: pd.DataFrame,
    symbol: str = "",
    open_interest: float = 0.0,
    funding_rate: float = 0.0,
    long_short_ratio: float = 1.0,
) -> pd.DataFrame:
    """
    Build all 85 features from OHLCV data + optional futures data.
    Returns DataFrame with one row per H1 candle, columns matching feature_cols_v2.json.
    """
    df = h1_df.copy()
    close = df["close"]
    high  = df["high"]
    low   = df["low"]
    vol   = df["volume"]

    # ── Volume-derived ────────────────────────────────────────────────────────
    df["volume_delta"] = np.where(close >= df["open"], vol, -vol)
    df["cvd"]          = df["volume_delta"].cumsum()
    df["buy_volume"]   = np.where(close >= df["open"], vol, 0.0)
    df["sell_volume"]  = np.where(close < df["open"],  vol, 0.0)

    # ── EMAs H1 ───────────────────────────────────────────────────────────────
    df["ema_7_h1"]   = EMAIndicator(close, window=7).ema_indicator()
    df["ema_21_h1"]  = EMAIndicator(close, window=21).ema_indicator()
    df["ema_50_h1"]  = EMAIndicator(close, window=50).ema_indicator()
    df["ema_200_h1"] = EMAIndicator(close, window=200).ema_indicator()

    # ── EMAs / ATR / RSI from H4 (reindexed to H1) ───────────────────────────
    h4_indicators = pd.DataFrame({
        "ema_7_h4":   EMAIndicator(h4_df["close"], window=7).ema_indicator(),
        "ema_21_h4":  EMAIndicator(h4_df["close"], window=21).ema_indicator(),
        "ema_50_h4":  EMAIndicator(h4_df["close"], window=50).ema_indicator(),
        "ema_200_h4": EMAIndicator(h4_df["close"], window=200).ema_indicator(),
        "atr_14_h4":  AverageTrueRange(h4_df["high"], h4_df["low"], h4_df["close"], window=14).average_true_range(),
        "rsi_h4":     RSIIndicator(h4_df["close"], window=14).rsi(),
    }, index=h4_df.index)

    h4_reindexed = h4_indicators.reindex(
        h4_indicators.index.union(df.index)
    ).ffill().reindex(df.index)
    df = df.join(h4_reindexed, how="left")
    for col in h4_indicators.columns:
        df[col] = df[col].ffill()

    # ── ATR / RSI / StochRSI H1 ───────────────────────────────────────────────
    df["atr_14_h1"]  = AverageTrueRange(high, low, close, window=14).average_true_range()
    df["rsi_6"]      = RSIIndicator(close, window=6).rsi()
    srsi             = StochRSIIndicator(close, window=14, smooth1=3, smooth2=3)
    df["stochrsi_k"] = srsi.stochrsi_k()
    df["stochrsi_d"] = srsi.stochrsi_d()

    # ── Returns & vol ratio ───────────────────────────────────────────────────
    df["log_ret_1"]   = np.log(close / close.shift(1))
    df["log_ret_5"]   = np.log(close / close.shift(5))
    df["log_ret_20"]  = np.log(close / close.shift(20))
    vol_ma20          = vol.rolling(20).mean()
    df["vol_ratio_20"] = vol / vol_ma20.clip(lower=1e-10)

    # ── Time features ─────────────────────────────────────────────────────────
    idx = df.index
    df["hour_sin"]            = np.sin(2 * np.pi * idx.hour / 24)
    df["hour_cos"]            = np.cos(2 * np.pi * idx.hour / 24)
    df["dow_sin"]             = np.sin(2 * np.pi * idx.dayofweek / 7)
    df["dow_cos"]             = np.cos(2 * np.pi * idx.dayofweek / 7)
    df["time_to_funding_norm"] = ((8 - idx.hour % 8) % 8) / 8.0

    # market_session: 0=Asia 1=Europe 2=US 3=overlap
    h = idx.hour
    ms = np.zeros(len(df), dtype=int)
    ms[(h >= 7) & (h < 9)]   = 3
    ms[(h >= 9) & (h < 13)]  = 1
    ms[(h >= 13) & (h < 17)] = 3
    ms[(h >= 17) & (h < 22)] = 2
    df["market_session"] = ms

    # ── Previous Day / Week High-Low ──────────────────────────────────────────
    daily_high = h1_df["high"].resample("D").max().shift(1)
    daily_low  = h1_df["low"].resample("D").min().shift(1)
    df["PDH"]  = daily_high.reindex(df.index, method="ffill").ffill().fillna(high)
    df["PDL"]  = daily_low.reindex(df.index, method="ffill").ffill().fillna(low)

    weekly_high = h1_df["high"].resample("W").max().shift(1)
    weekly_low  = h1_df["low"].resample("W").min().shift(1)
    df["PWH"]   = weekly_high.reindex(df.index, method="ffill").ffill().fillna(high)
    df["PWL"]   = weekly_low.reindex(df.index, method="ffill").ffill().fillna(low)

    # ── Fibonacci (96-bar swing range) ────────────────────────────────────────
    swing_high_96 = high.rolling(96).max()
    swing_low_96  = low.rolling(96).min()
    fib_range     = swing_high_96 - swing_low_96
    df["Fib_618"] = swing_high_96 - 0.618 * fib_range
    df["Fib_786"] = swing_high_96 - 0.786 * fib_range

    # ── Volume Profile: POC / VAH / VAL (percentile approximation) ───────────
    vp_w = 96
    df["POC"] = close.rolling(vp_w).median()
    df["VAH"] = high.rolling(vp_w).quantile(0.70)
    df["VAL"] = low.rolling(vp_w).quantile(0.30)

    # ── Swing high/low (5-bar pivot) ──────────────────────────────────────────
    sw = 5
    pivot_high = high.rolling(sw * 2 + 1, center=True).max() == high
    pivot_low  = low.rolling(sw * 2 + 1, center=True).min() == low

    last_sh = high.where(pivot_high).ffill().fillna(high.cummax())
    last_sl = low.where(pivot_low).ffill().fillna(low.cummin())

    df["dist_swing_high"] = (last_sh - close) / close.clip(lower=1e-10)
    df["dist_swing_low"]  = (close - last_sl) / close.clip(lower=1e-10)
    sh_sl_range           = (last_sh - last_sl).clip(lower=1e-10)
    df["price_in_range"]  = (close - last_sl) / sh_sl_range
    df["swing_momentum"]  = close.diff(sw) / df["atr_14_h1"].clip(lower=1e-10)

    # ── SMC: BOS / CHoCH ─────────────────────────────────────────────────────
    bos = pd.Series(0, index=df.index)
    bos[close > last_sh.shift(1)] =  1
    bos[close < last_sl.shift(1)] = -1
    df["MSB_BOS"] = bos

    choch = pd.Series(0, index=df.index)
    choch[(bos == 1) & (bos.shift(1) <= 0)] =  1
    choch[(bos == -1) & (bos.shift(1) >= 0)] = -1
    df["CHoCH"] = choch

    bos_event    = bos != 0
    group_ids    = bos_event.cumsum()
    df["bars_since_BOS"] = df.groupby(group_ids).cumcount()

    # ── SMC: FVG (Fair Value Gap) ─────────────────────────────────────────────
    df["FVG_up"]   = ((low > high.shift(2)) & (close.shift(1) > high.shift(2))).astype(int)
    df["FVG_down"] = ((high < low.shift(2)) & (close.shift(1) < low.shift(2))).astype(int)

    # ── SMC: Liquidity levels ─────────────────────────────────────────────────
    df["Buy_Liq"]  = (high.rolling(20).max() == high).astype(int)
    df["Sell_Liq"] = (low.rolling(20).min() == low).astype(int)

    # ── SMC: SFP sweep (wick rejection) ──────────────────────────────────────
    df["SFP_sweep"] = (
        ((high > high.shift(1)) & (close < high.shift(1))) |
        ((low  < low.shift(1))  & (close > low.shift(1)))
    ).astype(int)

    # ── Futures data ──────────────────────────────────────────────────────────
    df["open_interest"]   = open_interest
    df["funding_rate"]    = funding_rate
    df["long_short_ratio"] = long_short_ratio

    # ── Macro approximations ──────────────────────────────────────────────────
    df["btc_dominance"] = 0.50   # neutral placeholder
    df["fear_greed"]    = 50.0   # neutral placeholder

    # ── Symbol encoding ───────────────────────────────────────────────────────
    df["symbol"] = abs(hash(symbol)) % 100

    # ── Trend features ────────────────────────────────────────────────────────
    df["h4_trend"]       = np.where(df["ema_50_h4"] > df["ema_200_h4"], 1, -1)
    df["trend_strength"] = (df["ema_7_h1"] - df["ema_200_h1"]).abs() / df["atr_14_h1"].clip(lower=1e-10)
    df["vol_regime"]     = np.where(df["vol_ratio_20"] > 1.5, 2,
                           np.where(df["vol_ratio_20"] > 1.0, 1, 0))

    # ── CVD H4 derivatives ────────────────────────────────────────────────────
    h4_vdelta = np.where(h4_df["close"] >= h4_df["open"], h4_df["volume"], -h4_df["volume"])
    h4_cvd    = pd.Series(h4_vdelta, index=h4_df.index).cumsum()
    h4_cvd_h1 = h4_cvd.reindex(
        h4_cvd.index.union(df.index)
    ).ffill().reindex(df.index).ffill()

    df["cvd_div_h4"]      = df["cvd"] - h4_cvd_h1
    df["cvd_slope_h4"]    = df["cvd"].diff(4)
    df["vol_efficiency"]  = df["log_ret_1"].abs() / df["vol_ratio_20"].clip(lower=1e-10)
    df["absorption_z"]    = (vol - vol_ma20) / vol.rolling(20).std().clip(lower=1e-10)
    df["funding_price_div"] = close.pct_change() - funding_rate

    # ── RSI divergence ────────────────────────────────────────────────────────
    rsi = df["rsi_6"]
    df["rsi_divergence"] = np.where(
        (close > close.shift(5)) & (rsi < rsi.shift(5)), -1,
        np.where((close < close.shift(5)) & (rsi > rsi.shift(5)), 1, 0)
    )
    df["hidden_divergence"] = np.where(
        (close > close.shift(5)) & (rsi > rsi.shift(5)), 1,
        np.where((close < close.shift(5)) & (rsi < rsi.shift(5)), -1, 0)
    )

    # ── Wyckoff approximation ─────────────────────────────────────────────────
    spread     = (high - low).clip(lower=1e-10)
    close_pos  = (close - low) / spread
    spread_ma  = spread.rolling(20).mean()

    accum = ((df["log_ret_1"] > 0) & (vol > vol_ma20) & (close_pos > 0.7)) | \
            ((df["log_ret_1"] < 0) & (vol < vol_ma20))
    dist  = ((df["log_ret_1"] < 0) & (vol > vol_ma20) & (close_pos < 0.3)) | \
            ((df["log_ret_1"] > 0) & (vol < vol_ma20))

    df["wyckoff_phase"]   = np.where(accum, 1, np.where(dist, -1, 0))
    df["spring_upthrust"] = np.where(
        (low < low.shift(1)) & (close > df["open"]) & (close_pos > 0.7), 1,
        np.where((high > high.shift(1)) & (close < df["open"]) & (close_pos < 0.3), -1, 0)
    )

    # ── OFI (Order Flow Imbalance) approximation ──────────────────────────────
    ofi_raw             = df["buy_volume"] - df["sell_volume"]
    df["ofi_raw"]       = ofi_raw
    df["ofi_acceleration"] = ofi_raw.diff()
    df["ofi_z_score"]   = (ofi_raw - ofi_raw.rolling(20).mean()) / ofi_raw.rolling(20).std().clip(lower=1e-10)
    df["ofi_h4_delta"]  = ofi_raw.rolling(4).sum().diff(4)

    # ── VWDP (Volume-Weighted Directional Pressure) ───────────────────────────
    df["vwdp"]        = (close - df["open"]) * vol / vol_ma20.clip(lower=1e-10)
    df["vwdp_smooth"] = df["vwdp"].rolling(5).mean()

    # ── Advanced signals ──────────────────────────────────────────────────────
    df["cvd_momentum_adv"]    = df["cvd"].diff(10)
    df["absorption_at_swing"] = df["absorption_z"] * (df["dist_swing_high"].abs() < 0.01).astype(float)
    df["spread_to_volume"]    = spread / vol.clip(lower=1e-10)
    df["ultra_high_vol"]      = (df["vol_ratio_20"] > 3.0).astype(int)
    df["no_demand"]           = (
        (close_pos > 0.5) & (vol < vol_ma20 * 0.5) & (spread < spread_ma * 0.5)
    ).astype(int)
    df["no_supply"] = (
        (close_pos < 0.5) & (vol < vol_ma20 * 0.5) & (spread < spread_ma * 0.5)
    ).astype(int)
    df["effort_vs_result"] = (spread / vol.clip(lower=1e-10)) / \
                             (spread_ma / vol_ma20.clip(lower=1e-10)).clip(lower=1e-10)

    return df.fillna(0)
