import { useQuery } from "@tanstack/react-query";
import { fetchPortfolio, fetchTrades, fetchPnLHistory } from "@/lib/api";
import PortfolioStatsPanel from "@/components/portfolio/PortfolioStats";
import TradeTable from "@/components/portfolio/TradeTable";
import PnLChart from "@/components/portfolio/PnLChart";
import type { PortfolioStats, Trade, PnLPoint } from "@/lib/types";

export default function Portfolio() {
  const { data: stats, isLoading: statsLoading } = useQuery<PortfolioStats>({
    queryKey: ["portfolio"],
    queryFn: fetchPortfolio,
  });

  const { data: allTrades = [] } = useQuery<Trade[]>({
    queryKey: ["trades"],
    queryFn: () => fetchTrades(undefined, 200),
  });

  const { data: pnlHistory = [] } = useQuery<PnLPoint[]>({
    queryKey: ["pnl-history"],
    queryFn: () => fetchPnLHistory(30),
  });

  const openTrades = allTrades.filter((t) => t.status === "OPEN");
  const closedTrades = allTrades.filter((t) => t.status === "CLOSED");

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-text-primary">Paper Trading Portfolio</h1>
        <p className="text-sm text-text-muted mt-0.5">Simulated trades — virtual $10,000 USDT</p>
      </div>

      {/* Stats */}
      {statsLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card animate-pulse h-20" />
          ))}
        </div>
      ) : stats ? (
        <PortfolioStatsPanel stats={stats} />
      ) : null}

      {/* PnL Chart */}
      <div className="mb-4">
        <PnLChart data={pnlHistory} />
      </div>

      {/* Active trades */}
      <div className="mb-4">
        <TradeTable trades={openTrades} title="Active Positions" />
      </div>

      {/* History */}
      <TradeTable trades={closedTrades} title="Trade History" />
    </div>
  );
}
