import axios from "axios";
import type {
  CoinSummary, Signal, Trade, PortfolioStats,
  ModelInfo, PnLPoint,
} from "./types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL + "/api",
  timeout: 15000,
});

export const fetchCoins = (): Promise<CoinSummary[]> =>
  api.get("/coins").then((r) => r.data);

export const fetchCoin = (symbol: string): Promise<CoinSummary> =>
  api.get(`/coins/${symbol}`).then((r) => r.data);

export const fetchCoinSignals = (symbol: string, limit = 50): Promise<Signal[]> =>
  api.get(`/coins/${symbol}/signals`, { params: { limit } }).then((r) => r.data);

export const fetchSignals = (params?: {
  coin?: string; signal_type?: string; limit?: number;
}): Promise<Signal[]> =>
  api.get("/signals", { params }).then((r) => r.data);

export const fetchPortfolio = (): Promise<PortfolioStats> =>
  api.get("/portfolio").then((r) => r.data);

export const fetchTrades = (status?: string, limit = 100): Promise<Trade[]> =>
  api.get("/trades", { params: { status, limit } }).then((r) => r.data);

export const fetchPnLHistory = (days = 30): Promise<PnLPoint[]> =>
  api.get("/trades/pnl-history", { params: { days } }).then((r) => r.data);

export const fetchModels = (): Promise<ModelInfo[]> =>
  api.get("/models").then((r) => r.data);

export const activateModel = (version: string): Promise<void> =>
  api.post("/models/activate", { version }).then((r) => r.data);

export const triggerInference = (): Promise<{ status: string; message: string }> =>
  api.post("/inference/trigger").then((r) => r.data);
