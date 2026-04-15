"use client";

interface GaugeRingProps {
  value: number; // 0-100
  label: string;
  size?: number;
  subtitle?: string;
}

function getColor(value: number): string {
  if (value >= 80) return "#ff3355";
  if (value >= 60) return "#ff4f00";
  return "#00ff88";
}

export function GaugeRing({ value, label, size = 140, subtitle }: GaugeRingProps) {
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(value, 100) / 100) * circumference;
  const color = getColor(value);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Background ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#1e1e2e"
            strokeWidth={strokeWidth}
          />
          {/* Progress ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              transition: "stroke-dashoffset 0.6s ease, stroke 0.3s ease",
              filter: `drop-shadow(0 0 6px ${color}40)`,
            }}
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-2xl font-bold tabular-nums"
            style={{ color }}
          >
            {Math.round(value)}%
          </span>
        </div>
      </div>
      <p className="text-xs font-semibold uppercase tracking-widest text-[#6b7280]">
        {label}
      </p>
      {subtitle && (
        <p className="text-[11px] text-[#4a4a5a]">{subtitle}</p>
      )}
    </div>
  );
}
