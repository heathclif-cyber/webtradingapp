import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import type { ShapFeature } from "@/lib/types";

interface Props {
  features: ShapFeature[];
  signal: string;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-bg-card border border-bg-border rounded-lg px-3 py-2 text-xs font-mono shadow-xl">
      <p className="text-text-secondary">{payload[0].payload.feature}</p>
      <p className="text-accent-purple">{payload[0].value.toFixed(4)}</p>
    </div>
  );
};

export default function ShapChart({ features, signal }: Props) {
  const top = [...features]
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 12);

  const barColor = signal === "LONG" ? "#00e676" : signal === "SHORT" ? "#ff3d71" : "#7c4dff";

  return (
    <div className="card">
      <p className="text-sm font-medium text-text-secondary mb-1">
        Top Features Driving AI Decision
      </p>
      <p className="text-xs text-text-muted mb-4">SHAP feature importance</p>

      {top.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-8">No SHAP data available</p>
      ) : (
        <ResponsiveContainer width="100%" height={top.length * 32 + 20}>
          <BarChart
            data={top}
            layout="vertical"
            margin={{ top: 0, right: 16, bottom: 0, left: 140 }}
          >
            <XAxis type="number" tick={{ fill: "#546e7a", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis
              type="category" dataKey="feature"
              tick={{ fill: "#9fa8da", fontSize: 11, fontFamily: "JetBrains Mono" }}
              axisLine={false} tickLine={false} width={130}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "#1e1e30" }} />
            <Bar dataKey="importance" radius={[0, 3, 3, 0]} barSize={14}>
              {top.map((_, i) => (
                <Cell
                  key={i}
                  fill={barColor}
                  fillOpacity={1 - (i / top.length) * 0.5}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
