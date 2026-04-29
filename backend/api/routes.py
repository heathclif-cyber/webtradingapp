import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from db.database import get_db
from db.models import Signal, PaperTrade, CoinMetric, ModelRegistry
from api.schemas import (
    CoinSummary, SignalOut, TradeOut, PortfolioStats,
    ModelInfo, ActivateModelRequest,
)
from core.inference import ModelManager
from core.paper_trader import get_portfolio_stats
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ── WebSocket connections hub ─────────────────────────────────────────────────

active_ws: list[WebSocket] = []


async def broadcast(data: dict):
    dead = []
    for ws in active_ws:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        active_ws.remove(ws)


@router.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    await websocket.accept()
    active_ws.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_ws.remove(websocket)


# ── Coins ─────────────────────────────────────────────────────────────────────

@router.get("/coins", response_model=list[CoinSummary])
async def get_coins(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoinMetric))
    metrics = result.scalars().all()
    # Return all configured coins, fill missing with defaults
    existing = {m.coin: m for m in metrics}
    output = []
    for coin in settings.COINS:
        if coin in existing:
            output.append(existing[coin])
        else:
            output.append(CoinSummary(
                coin=coin, signal="FLAT", score=50, confidence=0.0,
                trend_regime="NEUTRAL", winrate_7d=0.0, winrate_30d=0.0,
                entry_price=None, tp_price=None, sl_price=None,
                top_features=[], last_updated=None,
            ))
    return output


@router.get("/coins/{symbol}", response_model=CoinSummary)
async def get_coin(symbol: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CoinMetric).where(CoinMetric.coin == symbol.upper())
    )
    metric = result.scalar_one_or_none()
    if not metric:
        raise HTTPException(404, f"No data for {symbol}")
    return metric


@router.get("/coins/{symbol}/signals", response_model=list[SignalOut])
async def get_coin_signals(symbol: str, limit: int = 50,
                           db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Signal)
        .where(Signal.coin == symbol.upper())
        .order_by(desc(Signal.timestamp))
        .limit(limit)
    )
    return result.scalars().all()


# ── Signals ───────────────────────────────────────────────────────────────────

@router.get("/signals", response_model=list[SignalOut])
async def get_signals(coin: Optional[str] = None, signal_type: Optional[str] = None,
                      limit: int = 100, db: AsyncSession = Depends(get_db)):
    q = select(Signal).order_by(desc(Signal.timestamp)).limit(limit)
    if coin:
        q = q.where(Signal.coin == coin.upper())
    if signal_type:
        q = q.where(Signal.signal == signal_type.upper())
    result = await db.execute(q)
    return result.scalars().all()


# ── Portfolio / Trades ────────────────────────────────────────────────────────

@router.get("/portfolio", response_model=PortfolioStats)
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    return await get_portfolio_stats(db)


@router.get("/trades", response_model=list[TradeOut])
async def get_trades(status: Optional[str] = None, limit: int = 100,
                     db: AsyncSession = Depends(get_db)):
    q = select(PaperTrade).order_by(desc(PaperTrade.entry_time)).limit(limit)
    if status:
        q = q.where(PaperTrade.status == status.upper())
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/trades/pnl-history")
async def pnl_history(days: int = 30, db: AsyncSession = Depends(get_db)):
    """Cumulative PnL over time for charting."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(PaperTrade)
        .where(PaperTrade.status == "CLOSED", PaperTrade.exit_time >= since)
        .order_by(PaperTrade.exit_time)
    )
    trades = result.scalars().all()
    cumulative = 0.0
    history = []
    for t in trades:
        cumulative += t.pnl or 0
        history.append({"date": t.exit_time.isoformat(), "cumulative_pnl": round(cumulative, 2)})
    return history


# ── Models ────────────────────────────────────────────────────────────────────

@router.get("/models", response_model=list[ModelInfo])
async def list_models():
    manager = ModelManager.get()
    return manager.list_available()


@router.post("/models/activate")
async def activate_model(body: ActivateModelRequest):
    manager = ModelManager.get()
    try:
        manager.set_active(body.version)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    return {"status": "ok", "active_version": body.version}


# ── Manual inference trigger ──────────────────────────────────────────────────

@router.post("/inference/trigger")
async def trigger_inference():
    """Manually kick off one inference cycle (for testing)."""
    from scheduler.cron import run_inference_cycle
    try:
        await run_inference_cycle()
        return {"status": "ok", "message": "Inference cycle complete"}
    except Exception as e:
        logger.exception("Manual inference failed")
        raise HTTPException(500, str(e))
