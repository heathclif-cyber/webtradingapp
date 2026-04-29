"""
Paper trading logic: open/close simulated positions, calculate PnL.
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from db.models import PaperTrade, CoinMetric
import logging

logger = logging.getLogger(__name__)

INITIAL_BALANCE = 10_000.0   # USDT virtual balance
POSITION_SIZE_PCT = 0.05     # 5% of balance per trade


async def open_trade(db: AsyncSession, signal_id: int, coin: str,
                     direction: str, entry_price: float,
                     tp_price: float, sl_price: float,
                     model_version: str) -> PaperTrade:
    """Create a new paper trade from a signal."""

    # Check no duplicate open trade for same coin
    existing = await db.execute(
        select(PaperTrade).where(
            PaperTrade.coin == coin,
            PaperTrade.status == "OPEN"
        )
    )
    if existing.scalar_one_or_none():
        logger.info(f"Skipping open trade for {coin}: already has an open position")
        return None

    trade = PaperTrade(
        signal_id=signal_id,
        coin=coin,
        direction=direction,
        entry_price=entry_price,
        tp_price=tp_price,
        sl_price=sl_price,
        entry_time=datetime.now(timezone.utc),
        status="OPEN",
        model_version=model_version,
        position_size_usdt=INITIAL_BALANCE * POSITION_SIZE_PCT,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    logger.info(f"Opened paper trade: {direction} {coin} @ {entry_price}")
    return trade


async def close_trade(db: AsyncSession, trade: PaperTrade,
                      exit_price: float, reason: str = "TP/SL") -> PaperTrade:
    """Close a paper trade and calculate PnL."""

    if trade.direction == "LONG":
        pnl_pct = (exit_price - trade.entry_price) / trade.entry_price
    else:  # SHORT
        pnl_pct = (trade.entry_price - exit_price) / trade.entry_price

    pnl_usdt = trade.position_size_usdt * pnl_pct
    result = "WIN" if pnl_usdt > 0 else "LOSS"

    trade.exit_price = exit_price
    trade.exit_time = datetime.now(timezone.utc)
    trade.pnl = round(pnl_usdt, 4)
    trade.pnl_pct = round(pnl_pct * 100, 4)
    trade.result = result
    trade.status = "CLOSED"
    trade.close_reason = reason

    await db.commit()
    await db.refresh(trade)
    logger.info(f"Closed {trade.direction} {trade.coin}: PnL={pnl_usdt:+.2f} USDT ({result})")
    return trade


async def get_portfolio_stats(db: AsyncSession) -> dict:
    """Aggregate paper trading statistics."""
    from sqlalchemy import func

    result = await db.execute(select(PaperTrade))
    trades = result.scalars().all()

    closed = [t for t in trades if t.status == "CLOSED"]
    open_trades = [t for t in trades if t.status == "OPEN"]

    if not closed:
        return {
            "virtual_balance": INITIAL_BALANCE,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "winrate": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "open_trades": len(open_trades),
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "avg_rr": 0.0,
        }

    total_pnl = sum(t.pnl for t in closed)
    wins = [t for t in closed if t.result == "WIN"]
    losses = [t for t in closed if t.result == "LOSS"]
    winrate = len(wins) / len(closed) * 100 if closed else 0

    rr_values = [
        abs((t.tp_price - t.entry_price) / (t.entry_price - t.sl_price))
        for t in closed
        if t.sl_price and t.tp_price and (t.entry_price - t.sl_price) != 0
    ]

    return {
        "virtual_balance": round(INITIAL_BALANCE + total_pnl, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl / INITIAL_BALANCE * 100, 2),
        "winrate": round(winrate, 1),
        "total_trades": len(closed),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "open_trades": len(open_trades),
        "best_trade": round(max((t.pnl for t in closed), default=0), 2),
        "worst_trade": round(min((t.pnl for t in closed), default=0), 2),
        "avg_rr": round(sum(rr_values) / len(rr_values), 2) if rr_values else 0.0,
    }
