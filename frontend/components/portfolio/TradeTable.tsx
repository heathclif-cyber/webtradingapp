import { format, parseISO } from "date-fns";
import { TrendingUp, TrendingDown } from "lucide-react";
import clsx from "clsx";
import type { Trade } from "@/lib/types";

interface Props {
  trades: Trade[];
  title: string;
}

export default function TradeTable({ trades, title }: Props) {
  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-text-secondary">{title}</p>
        <span className="text-xs text-text-muted">{trades.length} trades</span>
      </div>

      {trades.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">No trades</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-text-muted border-b border-bg-border">
                <th className="text-left pb-2 pr-3">Pair</th>
                <th className="text-left pb-2 pr-3">Dir</th>
                <th className="text-right pb-2 pr-3">Entry</th>
                <th className="text-right pb-2 pr-3">TP</th>
                <th className="text-right pb-2 pr-3">SL</th>
                <th className="text-right pb-2 pr-3">Exit</th>
                <th className="text-right pb-2 pr-3">PnL</th>
                <th className="text-left pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => {
                const pnlPositive = (t.pnl ?? 0) >= 0;
                return (
                  <tr key={t.id} className="border-b border-bg-border/50 hover:bg-bg-secondary/30 transition-colors">
                    <td className="py-2 pr-3 text-text-primary font-semibold">
                      {t.coin.replace("USDT", "")}/USDT
                    </td>
                    <td className="py-2 pr-3">
                      {t.direction === "LONG" ? (
                        <span className="badge-long"><TrendingUp className="w-2.5 h-2.5 mr-0.5" />L</span>
                      ) : (
                        <span className="badge-short"><TrendingDown className="w-2.5 h-2.5 mr-0.5" />S</span>
                      )}
                    </td>
                    <td className="py-2 pr-3 text-right text-text-secondary">
                      ${t.entry_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}
                    </td>
                    <td className="py-2 pr-3 text-right text-accent-green">
                      ${t.tp_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}
                    </td>
                    <td className="py-2 pr-3 text-right text-accent-red">
                      ${t.sl_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}
                    </td>
                    <td className="py-2 pr-3 text-right text-text-muted">
                      {t.exit_price
                        ? `$${t.exit_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}`
                        : "—"}
                    </td>
                    <td className={clsx(
                      "py-2 pr-3 text-right font-semibold",
                      t.pnl === null ? "text-text-muted"
                        : pnlPositive ? "text-accent-green" : "text-accent-red"
                    )}>
                      {t.pnl !== null
                        ? `${pnlPositive ? "+" : ""}$${t.pnl.toFixed(2)}`
                        : "—"}
                    </td>
                    <td className="py-2">
                      {t.status === "OPEN" ? (
                        <span className="inline-flex items-center gap-1 text-accent-blue">
                          <span className="w-1.5 h-1.5 rounded-full bg-accent-blue animate-pulse" />
                          OPEN
                        </span>
                      ) : (
                        <span className={t.result === "WIN" ? "text-accent-green" : "text-accent-red"}>
                          {t.result ?? t.status}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
