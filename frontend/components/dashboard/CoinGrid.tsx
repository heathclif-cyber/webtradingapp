import { useState } from "react";
import { ArrowUpDown } from "lucide-react";
import CoinCard from "./CoinCard";
import type { CoinSummary } from "@/lib/types";
import clsx from "clsx";

type SortKey = "score" | "confidence" | "coin" | "signal";

interface Props {
  coins: CoinSummary[];
}

const SIGNAL_ORDER = { LONG: 0, SHORT: 1, FLAT: 2 };

export default function CoinGrid({ coins }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [filterSignal, setFilterSignal] = useState<string>("ALL");

  const filtered = coins.filter((c) =>
    filterSignal === "ALL" ? true : c.signal === filterSignal
  );

  const sorted = [...filtered].sort((a, b) => {
    if (sortKey === "score") return b.score - a.score;
    if (sortKey === "confidence") return b.confidence - a.confidence;
    if (sortKey === "coin") return a.coin.localeCompare(b.coin);
    if (sortKey === "signal")
      return (SIGNAL_ORDER[a.signal] ?? 3) - (SIGNAL_ORDER[b.signal] ?? 3);
    return 0;
  });

  return (
    <div>
      {/* Controls */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        {/* Signal filter */}
        <div className="flex rounded-lg border border-bg-border overflow-hidden">
          {["ALL", "LONG", "SHORT", "FLAT"].map((s) => (
            <button
              key={s}
              onClick={() => setFilterSignal(s)}
              className={clsx(
                "px-3 py-1.5 text-xs font-mono transition-colors",
                filterSignal === s
                  ? s === "LONG"
                    ? "bg-accent-green/15 text-accent-green"
                    : s === "SHORT"
                    ? "bg-accent-red/15 text-accent-red"
                    : "bg-accent-purple/15 text-accent-purple"
                  : "text-text-muted hover:text-text-secondary hover:bg-bg-secondary"
              )}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Sort */}
        <div className="flex items-center gap-1.5">
          <ArrowUpDown className="w-3.5 h-3.5 text-text-muted" />
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
            className="bg-bg-card border border-bg-border rounded-lg px-2 py-1.5 text-xs text-text-secondary outline-none focus:border-accent-purple/40"
          >
            <option value="score">Sort: Score</option>
            <option value="confidence">Sort: Confidence</option>
            <option value="signal">Sort: Signal</option>
            <option value="coin">Sort: Name</option>
          </select>
        </div>

        <p className="text-xs text-text-muted ml-auto">
          {filtered.length} coins
        </p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {sorted.map((c) => (
          <CoinCard key={c.coin} coin={c} />
        ))}
      </div>
    </div>
  );
}
