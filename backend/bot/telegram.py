"""
Telegram notification bot.
Sends signal alerts and trade closed notifications.
"""

import logging
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

DIRECTION_EMOJI = {"LONG": "🟢 BUY (LONG)", "SHORT": "🔴 SELL (SHORT)"}
RESULT_EMOJI = {"WIN": "✅", "LOSS": "❌"}


def _api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/{method}"


async def _send(text: str):
    if not settings.TELEGRAM_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.debug("Telegram not configured — skipping notification")
        return
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(_api_url("sendMessage"), json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
            }, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Telegram send failed: {e}")


async def send_signal_alert(coin: str, direction: str, confidence: float,
                            score: int, entry: float, tp: float | None,
                            sl: float | None, rr: float):
    label = DIRECTION_EMOJI.get(direction, direction)
    tp_str = f"${tp:,.4f}" if tp else "N/A"
    sl_str = f"${sl:,.4f}" if sl else "N/A"
    conf_pct = round(confidence * 100, 1)
    text = (
        f"🚨 <b>SIGNAL {label}: {coin}</b>\n"
        f"\n"
        f"🧠 <b>Confidence:</b> {conf_pct}% | <b>Score:</b> {score}/100\n"
        f"🎯 <b>Entry Target:</b> ${entry:,.4f}\n"
        f"✅ <b>TP:</b> {tp_str} (H4 Swing)\n"
        f"🛑 <b>SL:</b> {sl_str} (H4 Swing)\n"
        f"📊 <b>R:R:</b> {rr}\n"
        f"\n"
        f"📝 <i>AI Smart Money signal — FVG & Wyckoff analysis</i>"
    )
    await _send(text)


async def send_trade_closed_alert(trade, reason: str):
    emoji = RESULT_EMOJI.get(trade.result, "")
    direction_label = DIRECTION_EMOJI.get(trade.direction, trade.direction)
    pnl_str = f"{trade.pnl:+.2f}" if trade.pnl is not None else "0.00"
    pnl_pct_str = f"{trade.pnl_pct:+.2f}" if trade.pnl_pct is not None else "0.00"
    text = (
        f"{emoji} <b>TRADE CLOSED — {trade.coin}</b>\n"
        f"\n"
        f"📌 <b>Direction:</b> {direction_label}\n"
        f"💰 <b>PnL:</b> {pnl_str} USDT ({pnl_pct_str}%)\n"
        f"🏁 <b>Reason:</b> {reason} hit\n"
        f"📈 <b>Entry:</b> ${trade.entry_price:,.4f} → <b>Exit:</b> ${trade.exit_price:,.4f}"
    )
    await _send(text)
