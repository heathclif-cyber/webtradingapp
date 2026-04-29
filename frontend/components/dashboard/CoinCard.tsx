import Link from "next/link";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import clsx from "clsx";
import type { CoinSummary } from "@/lib/types";

interface Props {
  coin: CoinSummary;
}

const SIGNAL_CONFIG = {
  LONG:  { icon: TrendingUp,   badge: "badge-long",  bar: "bg-accent-green", label: "LONG" },
  SHORT: { icon: TrendingDown, badge: "badge-short", bar: "bg-accent-red",   label: "SHORT" },
  FLAT:  { icon: Minus,        badge: "badge-flat",  bar: "bg-bg-border",    label: "FLAT" },
};

function ScoreRing({ score, signal }: { score: number; signal: string }) {
  const color = signal === "LONG" ? "#00e676" : signal === "SHORT" ? "#ff3d71" : "#546e7a";
  const r = 20;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;

  return (
    <div className="relative w-14 h-14 shrink-0">
      <svg width="56" height="56" viewBox="0 0 56 56" className="-rotate-90">
        <circle cx="28" cy="28" r={r} fill="none" stroke="#1e1e30" strokeWidth="4" />
        <circle
          cx="28" cy="28" r={r} fill="none"
          stroke={color} strokeWidth="4"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center font-mono font-bold text-sm"
        style={{ color }}
      >
        {score}
      </span>
    </div>
  );
}

export default function CoinCard({ coin: c }: Props) {
  const cfg = SIGNAL_CONFIG[c.signal] ?? SIGNAL_CONFIG.FLAT;
  const Icon = cfg.icon;
  const confPct = Math.round(c.confidence * 100);

  return (
    <Link href={`/coin/${c.coin}`}>
      <div className="card cursor-pointer hover:border-bg-border/80 hover:bg-bg-secondary transition-all group">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="font-mono font-semibold text-text-primary text-sm group-hover:text-white transition-colors">
              {c.coin.replace("USDT", "")}
              <span className="text-text-muted font-normal">/USDT</span>
            </p>
            <p className="text-xs text-text-muted mt-0.5">{c.trend_regime}</p>
          </div>
          <ScoreRing score={c.score} signal={c.signal} />
        </div>

        {/* Signal badge */}
        <div className="flex items-center gap-2 mb-3">
          <span className={cfg.badge}>
            <Icon className="w-3 h-3 mr-1" />
            {cfg.label}
          </span>
          <span className="text-xs text-text-muted font-mono">{confPct}%</span>
        </div>

        {/* Confidence bar */}
        <div className="h-1 rounded-full bg-bg-border mb-3 overflow-hidden">
          <div
            className={clsx("h-full rounded-full transition-all", cfg.bar)}
            style={{ width: `${confPct}%`, opacity: 0.8 }}
          />
        </div>

        {/* TP / SL */}
        {c.signal !== "FLAT" && c.tp_price && c.sl_price && (
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div>
              <span className="text-text-muted block">TP</span>
              <span className="text-accent-green">${c.tp_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}</span>
            </div>
            <div>
              <span className="text-text-muted block">SL</span>
              <span className="text-accent-red">${c.sl_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}</span>
            </div>
          </div>
        )}

        {/* Winrate */}
        <div className="mt-2 flex items-center justify-between text-[11px] text-text-muted">
          <span>WR 7d: <span className="text-text-secondary">{c.winrate_7d.toFixed(0)}%</span></span>
          <span>WR 30d: <span className="text-text-secondary">{c.winrate_30d.toFixed(0)}%</span></span>
        </div>
      </div>
    </Link>
  );
}
