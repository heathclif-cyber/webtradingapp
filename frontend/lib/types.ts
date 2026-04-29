export type SignalType = "LONG" | "SHORT" | "FLAT";
export type TradeStatus = "OPEN" | "CLOSED";
export type TradeResult = "WIN" | "LOSS";
export type Regime = "BULLISH" | "BEARISH" | "NEUTRAL";

export interface CoinSummary {
  coin: string;
  signal: SignalType;
  score: number;
  confidence: number;
  trend_regime: Regime;
  winrate_7d: number;
  winrate_30d: number;
  entry_price: number | null;
  tp_price: number | null;
  sl_price: number | null;
  top_features: ShapFeature[];
  last_updated: string | null;
}

export interface ShapFeature {
  feature: string;
  importance: number;
}

export interface Signal {
  id: number;
  coin: string;
  timestamp: string;
  signal: SignalType;
  confidence: number;
  score: number;
  entry_price: number | null;
  tp_price: number | null;
  sl_price: number | null;
  model_version: string;
  lgbm_prob_long: number;
  lgbm_prob_short: number;
  lgbm_prob_flat: number;
  lstm_prob_long: number;
  lstm_prob_short: number;
  lstm_prob_flat: number;
}

export interface Trade {
  id: number;
  coin: string;
  direction: SignalType;
  entry_price: number;
  tp_price: number;
  sl_price: number;
  position_size_usdt: number;
  entry_time: string;
  exit_time: string | null;
  exit_price: number | null;
  status: TradeStatus;
  result: TradeResult | null;
  pnl: number | null;
  pnl_pct: number | null;
  close_reason: string | null;
  model_version: string;
}

export interface PortfolioStats {
  virtual_balance: number;
  total_pnl: number;
  total_pnl_pct: number;
  winrate: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  open_trades: number;
  best_trade: number;
  worst_trade: number;
  avg_rr: number;
}

export interface ModelInfo {
  version: string;
  path: string;
  lgbm_ready: boolean;
  lstm_ready: boolean;
  is_active: boolean;
  description: string;
  trained_at: string;
  num_features: number;
  coins: string[];
}

export interface PnLPoint {
  date: string;
  cumulative_pnl: number;
}
