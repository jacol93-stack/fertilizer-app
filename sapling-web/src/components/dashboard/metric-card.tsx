"use client";

import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  color?: "green" | "cyan" | "orange" | "red" | "white";
  children?: ReactNode;
}

const colorMap = {
  green: "#00ff88",
  cyan: "#00d4ff",
  orange: "#ff4f00",
  red: "#ff3355",
  white: "#e5e7eb",
};

export function MetricCard({ label, value, subtitle, color = "white", children }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-[#1e1e2e] bg-[#12121a] p-5">
      <p className="text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
        {label}
      </p>
      <p
        className="mt-1 text-3xl font-bold tabular-nums"
        style={{ color: colorMap[color] }}
      >
        {value}
      </p>
      {subtitle && (
        <p className="mt-0.5 text-xs text-[#6b7280]">{subtitle}</p>
      )}
      {children && <div className="mt-3">{children}</div>}
    </div>
  );
}
