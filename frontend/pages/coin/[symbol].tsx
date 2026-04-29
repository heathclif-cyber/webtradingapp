import { useRouter } from "next/router";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, TrendingUp, TrendingDown, Minus } from "lucide-react";
import Link from "next/link";
import { fetchCoin, fetchCoinSignals } from "@/lib/api";
import PriceChart from "@/components/coin/PriceChart";
import ShapChart from "@/components/coin/ShapChart";
import type { CoinSummary, Signal } from "@/lib/types";
import clsx from "clsx";

const SIGNAL_ICON = {
  LONG: TrendingUp,
  SHORT: TrendingDown,
  FLAT: Minus,
};
const SIGNAL_COLOR = {
  LONG: "text-accent-green",
  SHORT: "text-accent-red",
  FLAT: "text-text-muted",
};

function ProbBar({ label, lgbm, lstm }: { label: string; lgbm: number; lstm: number }) {
  const avg = (lgbm + lstm) / 2;
  const color = label === "LONG" ? "bg-accent-green" : label === "SHORT" ? "bg-accent-red" : "bg-bg-border";
  return (
    <div className="flex items-center gap-2 text-xs font-mono">
      <span className="w-10 text-text-muted">{label}</span>
      <div className="flex-1 h-2 bg-bg-border rounded-full overflow-hidden">
        <div className={clsx("h-full rounded-full", color)} style={{ width: `${avg * 100}%` }} />
      </div>
      <span className="w-10 text-right text-text-secondary">{(avg * 100).toFixed(0)}%</span>
    </div>
  );
}

export default function CoinDetail() {
  const { query } = useRouter();
  const symbol = (query.symbol as string)?.toUpperCase();

  const { data: coin, isLoading: coinLoading } = useQuery<CoinSummary>({
    queryKey: ["coin", symbol],
    queryFn: () => fetchCoin(symbol),
    enabled: !!symbol,
  });

  const { data: signals = [] } = useQuery<Signal[]>({
    queryKey: ["coin-signals", symbol],
    queryFn: () => fetchCoinSignals(symbol, 100),
    enabled: !!symbol,
  });

  const latest = signals[0];
  const Icon = coin ? (SIGNAL_ICON[coin.signal] ?? Minus) : Minus;
  const sigColor = coin ? (SIGNAL_COLOR[coin.signal] ?? "text-text-muted") : "text-text-muted";

  return (
    <div>
      {/* Back */}
      <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary mb-5 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </Link>

      {coinLoading || !coin ? (
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-bg-card rounded w-48" />
          <div className="h-52 bg-bg-card rounded" />
        </div>
      ) : (
        <>
          {/* Coin header */}
          <div className="flex flex-wrap items-start gap-4 mb-6">
            <div>
              <h1 className="text-2xl font-mono font-bold text-text-primary">
                {symbol?.replace("USDT", "")}
                <span className="text-text-muted font-normal text-lg">/USDT</span>
              </h1>
              <p className="text-sm text-text-muted mt-0.5">{coin.trend_regime} regime</p>
            </div>

            <div className="flex items-center gap-3 ml-auto flex-wrap">
              {/* Current signal badge */}
              <div className={clsx("flex items-center gap-2 px-4 py-2 rounded-xl border", {
                "bg-accent-green/10 border-accent-green/30": coin.signal === "LONG",
                "bg-accent-red/10 border-accent-red/30": coin.signal === "SHORT",
                "bg-bg-card border-bg-border": coin.signal === "FLAT",
              })}>
                <Icon className={clsx("w-5 h-5", sigColor)} />
                <span className={clsx("font-mono font-bold text-lg", sigColor)}>{coin.signal}</span>
                <span className="font-mono text-sm text-text-muted">
                  {Math.round(coin.confidence * 100)}%
                </span>
              </div>

              {/* Score */}
              <div className="px-4 py-2 rounded-xl bg-bg-card border border-bg-border text-center">
                <p className="text-xs text-text-muted">Score</p>
                <p className="font-mono font-bold text-xl text-accent-purple">{coin.score}</p>
              </div>
            </div>
          </div>

          {/* TP / SL / Price row */}
          {coin.signal !== "FLAT" && (
            <div className="grid grid-cols-3 gap-3 mb-5">
              {[
                { label: "Entry", val: coin.entry_price, color: "text-text-primary" },
                { label: "Take Profit", val: coin.tp_price, color: "text-accent-green" },
                { label: "Stop Loss", val: coin.sl_price, color: "text-accent-red" },
              ].map(({ label, val, color }) => (
                <div key={label} className="card text-center">
                  <p className="text-xs text-text-muted mb-1">{label}</p>
                  <p className={clsx("font-mono font-semibold", color)}>
                    {val ? `$${val.toLocaleString(undefined, { maximumFractionDigits: 4 })}` : "N/A"}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <PriceChart signals={signals} coin={coin} />

            {/* Model probabilities */}
            {latest && (
              <div className="card space-y-3">
                <p className="text-sm font-medium text-text-secondary mb-2">
                  Model Probabilities (latest)
                </p>
                <ProbBar label="LONG" lgbm={latest.lgbm_prob_long} lstm={latest.lstm_prob_long} />
                <ProbBar label="FLAT" lgbm={latest.lgbm_prob_flat} lstm={latest.lstm_prob_flat} />
                <ProbBar label="SHORT" lgbm={latest.lgbm_prob_short} lstm={latest.lstm_prob_short} />

                <div className="pt-2 border-t border-bg-border grid grid-cols-2 gap-2 text-xs font-mono">
                  <div>
                    <p className="text-text-muted">WR 7d</p>
                    <p className="text-text-primary">{coin.winrate_7d.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-text-muted">WR 30d</p>
                    <p className="text-text-primary">{coin.winrate_30d.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-text-muted">Model</p>
                    <p className="text-accent-purple">{latest.model_version}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* SHAP */}
          <ShapChart features={coin.top_features ?? []} signal={coin.signal} />
        </>
      )}
    </div>
  );
}
