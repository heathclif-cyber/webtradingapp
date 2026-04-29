import { TrendingUp, TrendingDown, Target, Activity, Award, AlertTriangle } from "lucide-react";
import clsx from "clsx";
import type { PortfolioStats } from "@/lib/types";

interface Props {
  stats: PortfolioStats;
}

export default function PortfolioStatsPanel({ stats: s }: Props) {
  const balanceColor = s.total_pnl >= 0 ? "text-accent-green" : "text-accent-red";
  const pnlPositive = s.total_pnl >= 0;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      <StatCard
        label="Virtual Balance"
        value={`$${s.virtual_balance.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
        sub={
          <span className={balanceColor}>
            {pnlPositive ? "+" : ""}{s.total_pnl_pct.toFixed(2)}%
          </span>
        }
        icon={<Activity className="w-4 h-4 text-accent-blue" />}
        highlight
      />

      <StatCard
        label="Total PnL"
        value={`${pnlPositive ? "+" : ""}$${s.total_pnl.toFixed(2)}`}
        valueClass={pnlPositive ? "text-accent-green" : "text-accent-red"}
        icon={pnlPositive
          ? <TrendingUp className="w-4 h-4 text-accent-green" />
          : <TrendingDown className="w-4 h-4 text-accent-red" />}
      />

      <StatCard
        label="Win Rate"
        value={`${s.winrate.toFixed(1)}%`}
        sub={`${s.winning_trades}W / ${s.losing_trades}L`}
        icon={<Target className="w-4 h-4 text-accent-purple" />}
        valueClass={s.winrate >= 55 ? "text-accent-green" : s.winrate >= 45 ? "text-accent-yellow" : "text-accent-red"}
      />

      <StatCard
        label="Total Trades"
        value={String(s.total_trades)}
        sub={`${s.open_trades} open`}
        icon={<Activity className="w-4 h-4 text-text-muted" />}
      />

      <StatCard
        label="Best Trade"
        value={`+$${s.best_trade.toFixed(2)}`}
        valueClass="text-accent-green"
        icon={<Award className="w-4 h-4 text-accent-green" />}
      />

      <StatCard
        label="Avg R:R"
        value={`${s.avg_rr}x`}
        icon={<AlertTriangle className="w-4 h-4 text-accent-yellow" />}
        valueClass={s.avg_rr >= 2 ? "text-accent-green" : "text-accent-yellow"}
      />
    </div>
  );
}

function StatCard({
  label, value, sub, icon, valueClass = "text-text-primary", highlight = false,
}: {
  label: string;
  value: string;
  sub?: React.ReactNode;
  icon?: React.ReactNode;
  valueClass?: string;
  highlight?: boolean;
}) {
  return (
    <div className={clsx(
      "card flex flex-col gap-1",
      highlight && "border-accent-purple/20 bg-accent-purple/5"
    )}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted">{label}</span>
        {icon}
      </div>
      <span className={clsx("font-mono font-bold text-lg", valueClass)}>{value}</span>
      {sub && <span className="text-xs text-text-muted">{sub}</span>}
    </div>
  );
}
