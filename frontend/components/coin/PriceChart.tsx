import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import type { Signal, CoinSummary } from "@/lib/types";
import { format, parseISO } from "date-fns";

interface Props {
  signals: Signal[];
  coin: CoinSummary;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-bg-card border border-bg-border rounded-lg px-3 py-2 text-xs font-mono shadow-xl">
      <p className="text-text-muted">{label}</p>
      <p className="text-text-primary">Price: ${Number(payload[0]?.value).toLocaleString()}</p>
      {payload[0]?.payload?.signal !== "FLAT" && (
        <p className={payload[0]?.payload?.signal === "LONG" ? "text-accent-green" : "text-accent-red"}>
          {payload[0]?.payload?.signal} · {Math.round(payload[0]?.payload?.confidence * 100)}%
        </p>
      )}
    </div>
  );
};

export default function PriceChart({ signals, coin }: Props) {
  const data = signals
    .slice()
    .reverse()
    .filter((s) => s.entry_price)
    .map((s) => ({
      date: format(parseISO(s.timestamp), "dd MMM HH:mm"),
      price: s.entry_price,
      signal: s.signal,
      confidence: s.confidence,
    }));

  const prices = data.map((d) => d.price ?? 0).filter(Boolean);
  const minPrice = Math.min(...prices) * 0.998;
  const maxPrice = Math.max(...prices) * 1.002;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-text-secondary">Price & Signal History</p>
        {coin.entry_price && (
          <span className="font-mono text-sm text-text-primary">
            ${coin.entry_price.toLocaleString(undefined, { maximumFractionDigits: 4 })}
          </span>
        )}
      </div>

      {data.length === 0 ? (
        <div className="flex items-center justify-center h-52 text-text-muted text-sm">
          No signal history yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#448aff" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#448aff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e30" />
            <XAxis dataKey="date" tick={{ fill: "#546e7a", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis
              domain={[minPrice, maxPrice]}
              tick={{ fill: "#546e7a", fontSize: 10 }}
              axisLine={false} tickLine={false}
              tickFormatter={(v) => `$${Number(v).toLocaleString()}`}
            />
            <Tooltip content={<CustomTooltip />} />
            {coin.tp_price && (
              <ReferenceLine y={coin.tp_price} stroke="#00e676" strokeDasharray="4 4"
                label={{ value: "TP", fill: "#00e676", fontSize: 10 }} />
            )}
            {coin.sl_price && (
              <ReferenceLine y={coin.sl_price} stroke="#ff3d71" strokeDasharray="4 4"
                label={{ value: "SL", fill: "#ff3d71", fontSize: 10 }} />
            )}
            <Area type="monotone" dataKey="price" stroke="#448aff" strokeWidth={2}
              fill="url(#priceGradient)" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
