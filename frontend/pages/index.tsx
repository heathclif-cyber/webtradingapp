import { useQuery } from "@tanstack/react-query";
import { RefreshCw, Wifi, WifiOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { fetchCoins } from "@/lib/api";
import CoinGrid from "@/components/dashboard/CoinGrid";
import type { CoinSummary } from "@/lib/types";

export default function Dashboard() {
  const { data: coins = [], isLoading, dataUpdatedAt, refetch, isFetching } =
    useQuery<CoinSummary[]>({
      queryKey: ["coins"],
      queryFn: fetchCoins,
      staleTime: 30_000,
    });

  const [wsStatus, setWsStatus] = useState<"connected" | "disconnected">("disconnected");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_API_URL?.replace("http", "ws")}/api/ws/live`
    );
    wsRef.current = ws;
    ws.onopen = () => setWsStatus("connected");
    ws.onclose = () => setWsStatus("disconnected");
    ws.onmessage = () => refetch();  // refresh on any live update
    return () => ws.close();
  }, [refetch]);

  const longs = coins.filter((c) => c.signal === "LONG").length;
  const shorts = coins.filter((c) => c.signal === "SHORT").length;
  const strongSignals = coins.filter((c) => c.score >= 70 && c.signal !== "FLAT").length;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Market Overview</h1>
          <p className="text-sm text-text-muted mt-0.5">
            AI Smart Money signals — 20 coins watchlist
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* WS status */}
          <div className="flex items-center gap-1.5 text-xs text-text-muted">
            {wsStatus === "connected"
              ? <><Wifi className="w-3.5 h-3.5 text-accent-green" /><span className="text-accent-green">Live</span></>
              : <><WifiOff className="w-3.5 h-3.5" />Offline</>}
          </div>

          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-bg-border text-xs text-text-secondary hover:text-text-primary hover:border-accent-purple/30 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary bar */}
      <div className="flex gap-3 mb-5 flex-wrap">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-accent-green/5 border border-accent-green/15">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-green" />
          <span className="text-xs font-mono text-accent-green">{longs} LONG</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-accent-red/5 border border-accent-red/15">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-red" />
          <span className="text-xs font-mono text-accent-red">{shorts} SHORT</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-accent-purple/5 border border-accent-purple/15">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-purple" />
          <span className="text-xs font-mono text-accent-purple">{strongSignals} strong signals (≥70)</span>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {Array.from({ length: 20 }).map((_, i) => (
            <div key={i} className="card animate-pulse h-40">
              <div className="h-3 bg-bg-border rounded w-16 mb-2" />
              <div className="h-3 bg-bg-border rounded w-24 mb-4" />
              <div className="h-8 bg-bg-border rounded" />
            </div>
          ))}
        </div>
      ) : (
        <CoinGrid coins={coins} />
      )}
    </div>
  );
}
