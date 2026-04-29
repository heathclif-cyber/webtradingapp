"""
Binance WebSocket price monitor.
Watches all coins with open paper trades and closes them when TP/SL is hit.
"""

import asyncio
import json
import logging
import websockets
from typing import Optional

from core.config import settings

logger = logging.getLogger(__name__)

WS_BASE = "wss://stream.binance.com:9443/stream"


class BinanceMonitor:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._prices: dict[str, float] = {}

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Binance price monitor started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Binance price monitor stopped")

    def get_price(self, symbol: str) -> Optional[float]:
        return self._prices.get(symbol.lower())

    async def _run(self):
        while self._running:
            try:
                await self._connect_and_monitor()
            except Exception as e:
                logger.warning(f"WS disconnected: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def _connect_and_monitor(self):
        streams = "/".join(f"{c.lower()}@miniTicker" for c in settings.COINS)
        url = f"{WS_BASE}?streams={streams}"

        async with websockets.connect(url, ping_interval=20) as ws:
            logger.info("Connected to Binance WebSocket")
            async for raw in ws:
                if not self._running:
                    break
                try:
                    msg = json.loads(raw)
                    data = msg.get("data", {})
                    symbol = data.get("s", "")
                    price = float(data.get("c", 0))
                    if symbol and price:
                        self._prices[symbol] = price
                        await self._check_tp_sl(symbol, price)
                except Exception as e:
                    logger.debug(f"WS parse error: {e}")

    async def _check_tp_sl(self, symbol: str, current_price: float):
        from db.database import AsyncSessionLocal
        from db.models import PaperTrade
        from sqlalchemy import select
        from core.paper_trader import close_trade
        from bot.telegram import send_trade_closed_alert

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(PaperTrade).where(
                    PaperTrade.coin == symbol,
                    PaperTrade.status == "OPEN"
                )
            )
            trades = result.scalars().all()

            for trade in trades:
                reason = None
                if trade.direction == "LONG":
                    if current_price >= trade.tp_price:
                        reason = "TP"
                    elif current_price <= trade.sl_price:
                        reason = "SL"
                else:  # SHORT
                    if current_price <= trade.tp_price:
                        reason = "TP"
                    elif current_price >= trade.sl_price:
                        reason = "SL"

                if reason:
                    closed = await close_trade(db, trade, current_price, reason)
                    await send_trade_closed_alert(closed, reason)
