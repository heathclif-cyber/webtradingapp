from datetime import datetime
from sqlalchemy import Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin: Mapped[str] = mapped_column(String(20), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    signal: Mapped[str] = mapped_column(String(10))           # LONG | SHORT | FLAT
    confidence: Mapped[float] = mapped_column(Float)
    score: Mapped[int] = mapped_column(Integer)

    # Raw probabilities
    lgbm_prob_long: Mapped[float] = mapped_column(Float, default=0)
    lgbm_prob_short: Mapped[float] = mapped_column(Float, default=0)
    lgbm_prob_flat: Mapped[float] = mapped_column(Float, default=0)
    lstm_prob_long: Mapped[float] = mapped_column(Float, default=0)
    lstm_prob_short: Mapped[float] = mapped_column(Float, default=0)
    lstm_prob_flat: Mapped[float] = mapped_column(Float, default=0)

    entry_price: Mapped[float] = mapped_column(Float, nullable=True)
    tp_price: Mapped[float] = mapped_column(Float, nullable=True)
    sl_price: Mapped[float] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(20), default="v1")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    paper_trades: Mapped[list["PaperTrade"]] = relationship(back_populates="signal")


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), nullable=True)
    coin: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(10))         # LONG | SHORT

    entry_price: Mapped[float] = mapped_column(Float)
    tp_price: Mapped[float] = mapped_column(Float)
    sl_price: Mapped[float] = mapped_column(Float)
    position_size_usdt: Mapped[float] = mapped_column(Float, default=500.0)

    entry_time: Mapped[datetime] = mapped_column(DateTime)
    exit_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    exit_price: Mapped[float] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String(10), default="OPEN", index=True)
    result: Mapped[str] = mapped_column(String(10), nullable=True)  # WIN | LOSS
    pnl: Mapped[float] = mapped_column(Float, nullable=True)
    pnl_pct: Mapped[float] = mapped_column(Float, nullable=True)
    close_reason: Mapped[str] = mapped_column(String(20), nullable=True)
    model_version: Mapped[str] = mapped_column(String(20), default="v1")

    signal: Mapped["Signal"] = relationship(back_populates="paper_trades")


class CoinMetric(Base):
    __tablename__ = "coin_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime)

    current_signal: Mapped[str] = mapped_column(String(10), default="FLAT")
    current_score: Mapped[int] = mapped_column(Integer, default=50)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    trend_regime: Mapped[str] = mapped_column(String(20), default="NEUTRAL")

    # Winrate stats
    winrate_7d: Mapped[float] = mapped_column(Float, default=0.0)
    winrate_30d: Mapped[float] = mapped_column(Float, default=0.0)
    total_signals_7d: Mapped[int] = mapped_column(Integer, default=0)
    avg_rr: Mapped[float] = mapped_column(Float, default=0.0)

    # SHAP top features (JSON list of {feature, importance})
    top_features: Mapped[dict] = mapped_column(JSON, default=list)

    entry_price: Mapped[float] = mapped_column(Float, nullable=True)
    tp_price: Mapped[float] = mapped_column(Float, nullable=True)
    sl_price: Mapped[float] = mapped_column(Float, nullable=True)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    path: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    trained_at: Mapped[str] = mapped_column(String(50), nullable=True)
    num_features: Mapped[int] = mapped_column(Integer, default=85)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
