"""
APScheduler: runs inference every H1 candle close (top of each hour).
Pipeline: fetch OHLCV → engineer features → predict → save signal → Telegram alert.
"""

import logging
from datetime import datetime, timezone

import ccxt.async_support as ccxt
import pandas as pd

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config import settings, LABEL_MAP
from core.inference import ModelManager
from core.scorer import compute_score
from core.tp_sl_calculator import compute_tp_sl, risk_reward_ratio
from db.database import AsyncSessionLocal
from db.models import Signal, CoinMetric
from bot.telegram import send_signal_alert

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")

_exchange = ccxt.binance({
    "apiKey": settings.BINANCE_API_KEY,
    "secret": settings.BINANCE_SECRET,
    "enableRateLimit": True,
})


# ── Feature Engineering stub ──────────────────────────────────────────────────
# Replace with your actual 03_engineer.py logic or import it directly.

def engineer_features(ohlcv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder: apply the same 85-feature engineering from your training pipeline.
    Import your actual engineer functions here and call them on ohlcv_df.
    Returns a DataFrame where each row = one candle with all 85 features.
    """
    # TODO: replace with: from pipeline.engineer import build_features
    # return build_features(ohlcv_df)
    raise NotImplementedError(
        "Plug in your 03_engineer.py feature engineering here. "
        "The function must accept an OHLCV DataFrame and return a "
        "DataFrame with all 85 feature columns."
    )


# ── Fetch helpers ─────────────────────────────────────────────────────────────

async def fetch_ohlcv(symbol: str, timeframe: str = "1h", limit: int = 200) -> pd.DataFrame:
    ohlcv = await _exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df.set_index("timestamp")


async def fetch_current_price(symbol: str) -> float:
    ticker = await _exchange.fetch_ticker(symbol)
    return float(ticker["last"])


# ── Core cycle ────────────────────────────────────────────────────────────────

async def run_inference_cycle():
    """Run inference for all configured coins and persist results."""
    logger.info("Starting inference cycle")
    manager = ModelManager.get()

    async with AsyncSessionLocal() as db:
        for coin in settings.COINS:
            try:
                await _process_coin(db, manager, coin)
            except NotImplementedError:
                logger.warning(f"Feature engineering not implemented — skipping {coin}")
                break
            except Exception as e:
                logger.error(f"Error processing {coin}: {e}")

    logger.info("Inference cycle complete")


async def _process_coin(db, manager: ModelManager, coin: str):
    h1_df = await fetch_ohlcv(coin, "1h", limit=200)
    h4_df = await fetch_ohlcv(coin, "4h", limit=100)
    current_price = float(h1_df["close"].iloc[-1])

    # Feature engineering (replace with real implementation)
    features_df = engineer_features(h1_df)

    # Predict
    pred = manager.predict(features_df)
    direction = LABEL_MAP[pred["predicted_class"]]
    confidence = pred["confidence"]

    # Score
    trend_strength = _estimate_trend_strength(h1_df)
    regime = _estimate_regime(h1_df)
    score = compute_score(pred["ensemble_probs"], pred["predicted_class"],
                          trend_strength, regime)

    # TP/SL
    tp, sl = (None, None)
    if direction != "FLAT":
        try:
            tp, sl = compute_tp_sl(direction, h4_df, current_price)
        except Exception:
            pass

    # Previous signal for change detection
    from sqlalchemy import select, desc
    prev = (await db.execute(
        select(Signal).where(Signal.coin == coin).order_by(desc(Signal.id)).limit(1)
    )).scalar_one_or_none()
    prev_signal = prev.signal if prev else "FLAT"

    # Save signal
    sig = Signal(
        coin=coin,
        timestamp=datetime.now(timezone.utc),
        signal=direction,
        confidence=confidence,
        score=score,
        entry_price=current_price,
        tp_price=tp,
        sl_price=sl,
        model_version=pred["model_version"],
        lgbm_prob_long=pred["lgbm_probs"]["LONG"],
        lgbm_prob_short=pred["lgbm_probs"]["SHORT"],
        lgbm_prob_flat=pred["lgbm_probs"]["FLAT"],
        lstm_prob_long=pred["lstm_probs"]["LONG"],
        lstm_prob_short=pred["lstm_probs"]["SHORT"],
        lstm_prob_flat=pred["lstm_probs"]["FLAT"],
    )
    db.add(sig)
    await db.flush()

    # SHAP top features for this coin
    top_features = manager.get_shap_for_coin(coin)

    # Upsert CoinMetric
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    await db.execute(
        pg_insert(CoinMetric).values(
            coin=coin,
            last_updated=datetime.now(timezone.utc),
            current_signal=direction,
            current_score=score,
            confidence=confidence,
            trend_regime=regime,
            entry_price=current_price,
            tp_price=tp,
            sl_price=sl,
            top_features=top_features,
        ).on_conflict_do_update(
            index_elements=["coin"],
            set_={
                "last_updated": datetime.now(timezone.utc),
                "current_signal": direction,
                "current_score": score,
                "confidence": confidence,
                "trend_regime": regime,
                "entry_price": current_price,
                "tp_price": tp,
                "sl_price": sl,
                "top_features": top_features,
            }
        )
    )
    await db.commit()

    # Open paper trade if signal changed and strong enough
    if direction != "FLAT" and prev_signal != direction and confidence >= settings.CONFIDENCE_THRESHOLD:
        from core.paper_trader import open_trade
        await open_trade(db, sig.id, coin, direction, current_price,
                         tp or 0, sl or 0, pred["model_version"])

    # Telegram alert on signal change with high confidence
    if direction != "FLAT" and prev_signal != direction and confidence >= settings.CONFIDENCE_FULL:
        rr = risk_reward_ratio(current_price, tp or current_price, sl or current_price)
        await send_signal_alert(coin, direction, confidence, score,
                                current_price, tp, sl, rr)


def _estimate_trend_strength(df: pd.DataFrame) -> float:
    """Simple EMA-crossover trend strength proxy (0.0 = strong bear, 1.0 = strong bull)."""
    close = df["close"]
    ema20 = close.ewm(span=20).mean().iloc[-1]
    ema50 = close.ewm(span=50).mean().iloc[-1]
    ema200 = close.ewm(span=200).mean().iloc[-1]
    price = close.iloc[-1]
    bull_signals = sum([price > ema20, ema20 > ema50, ema50 > ema200])
    return bull_signals / 3.0


def _estimate_regime(df: pd.DataFrame) -> str:
    ts = _estimate_trend_strength(df)
    if ts >= 0.67:
        return "BULLISH"
    if ts <= 0.33:
        return "BEARISH"
    return "NEUTRAL"


# ── Scheduler control ─────────────────────────────────────────────────────────

def start_scheduler():
    scheduler.add_job(run_inference_cycle, "cron", minute=1, id="h1_inference",
                      replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started (H1 inference @ :01 each hour)")


def stop_scheduler():
    scheduler.shutdown(wait=False)
