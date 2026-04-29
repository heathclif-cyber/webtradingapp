import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";
import type { PnLPoint } from "@/lib/types";

interface Props {
  data: PnLPoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const val = payload[0].value as number;
  const positive = val >= 0;
  return (
    <div className="bg-bg-card border border-bg-border rounded-lg px-3 py-2 text-xs font-mono shadow-xl">
      <p className="text-text-muted">{label}</p>
      <p className={positive ? "text-accent-green" : "text-accent-red"}>
        {positive ? "+" : ""}${val.toFixed(2)}
      </p>
    </div>
  );
};

export default function PnLChart({ data }: Props) {
  const formatted = data.map((d) => ({
    date: format(parseISO(d.date), "dd MMM"),
    pnl: d.cumulative_pnl,
  }));

  const isPositive = (formatted[formatted.length - 1]?.pnl ?? 0) >= 0;
  const color = isPositive ? "#00e676" : "#ff3d71";

  return (
    <div className="card">
      <p className="text-sm font-medium text-text-secondary mb-4">Cumulative PnL</p>
      {formatted.length === 0 ? (
        <div className="flex items-center justify-center h-40 text-text-muted text-sm">
          No closed trades yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={formatted} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.2} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e30" />
            <XAxis
              dataKey="date" tick={{ fill: "#546e7a", fontSize: 11 }}
              axisLine={false} tickLine={false}
            />
            <YAxis
              tick={{ fill: "#546e7a", fontSize: 11 }}
              axisLine={false} tickLine={false}
              tickFormatter={(v) => `$${v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey="pnl"
              stroke={color} strokeWidth={2}
              fill="url(#pnlGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
