from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CoinSummary(BaseModel):
    coin: str
    signal: str
    score: int
    confidence: float
    trend_regime: str
    winrate_7d: float
    winrate_30d: float
    entry_price: Optional[float]
    tp_price: Optional[float]
    sl_price: Optional[float]
    top_features: list
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


class SignalOut(BaseModel):
    id: int
    coin: str
    timestamp: datetime
    signal: str
    confidence: float
    score: int
    entry_price: Optional[float]
    tp_price: Optional[float]
    sl_price: Optional[float]
    model_version: str
    lgbm_prob_long: float
    lgbm_prob_short: float
    lgbm_prob_flat: float
    lstm_prob_long: float
    lstm_prob_short: float
    lstm_prob_flat: float

    class Config:
        from_attributes = True


class TradeOut(BaseModel):
    id: int
    coin: str
    direction: str
    entry_price: float
    tp_price: float
    sl_price: float
    position_size_usdt: float
    entry_time: datetime
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    status: str
    result: Optional[str]
    pnl: Optional[float]
    pnl_pct: Optional[float]
    close_reason: Optional[str]
    model_version: str

    class Config:
        from_attributes = True


class PortfolioStats(BaseModel):
    virtual_balance: float
    total_pnl: float
    total_pnl_pct: float
    winrate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    open_trades: int
    best_trade: float
    worst_trade: float
    avg_rr: float


class ModelInfo(BaseModel):
    version: str
    path: str
    lgbm_ready: bool
    lstm_ready: bool
    is_active: bool
    description: str
    trained_at: str
    num_features: int
    coins: list[str]


class ActivateModelRequest(BaseModel):
    version: str
