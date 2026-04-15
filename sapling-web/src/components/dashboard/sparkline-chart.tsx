"use client";

import {
  AreaChart,
  Area,
  ResponsiveContainer,
  Tooltip,
  CartesianGrid,
} from "recharts";

interface SparklineChartProps {
  data: Array<Record<string, unknown>>;
  dataKey: string;
  color?: string;
  height?: number;
  showGrid?: boolean;
  formatValue?: (value: number) => string;
}

export function SparklineChart({
  data,
  dataKey,
  color = "#00ff88",
  height = 80,
  showGrid = false,
  formatValue,
}: SparklineChartProps) {
  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center text-xs text-[#4a4a5a]"
        style={{ height }}
      >
        No data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
        <defs>
          <linearGradient id={`grad-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        {showGrid && (
          <CartesianGrid stroke="#1e1e2e" strokeDasharray="3 3" vertical={false} />
        )}
        <Tooltip
          contentStyle={{
            backgroundColor: "#12121a",
            border: "1px solid #1e1e2e",
            borderRadius: "8px",
            fontSize: "12px",
            color: "#e5e7eb",
          }}
          formatter={(value) => [
            formatValue ? formatValue(Number(value)) : `${value}`,
            dataKey,
          ]}
          labelStyle={{ color: "#6b7280" }}
        />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          fill={`url(#grad-${dataKey})`}
          dot={false}
          activeDot={{ r: 3, fill: color, stroke: "#12121a", strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
