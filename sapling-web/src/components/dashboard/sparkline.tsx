"use client";

/**
 * Hand-rolled SVG sparkline. Inline, dependency-free — keeps the
 * sapling-orange palette consistent with the rest of the app and
 * doesn't drag in a chart library's opinions about styling.
 *
 * Designed for the field dashboard's per-nutrient mini-charts. Renders
 * a baseline, a connecting line, dots per data point, and an optional
 * shaded sufficiency band for visual reference.
 */
import { useMemo } from "react";

export interface SparklinePoint {
  /** ISO date or year string for the x-axis. Sparkline orders points
   * by their order in the array — pre-sort caller-side. */
  label: string;
  value: number | null;
}

export interface SparklineBand {
  /** Optional sufficiency band (e.g. low / typical / high). Renders as
   * a translucent rectangle behind the line. */
  low?: number | null;
  high?: number | null;
  colour?: string; // tailwind colour class fragment, e.g. "emerald"
}

export interface SparklineProps {
  points: SparklinePoint[];
  width?: number;
  height?: number;
  /** Optional sufficiency band overlaid behind the line. */
  band?: SparklineBand | null;
  /** When true, draw a single dot for series with one point. */
  showSinglePoint?: boolean;
  /** Shown above the chart as a label. */
  title?: string;
  /** Suffix the latest value ends with (e.g. "%", "kg/ha"). */
  unit?: string;
  /** Number of decimals on the latest-value display. */
  decimals?: number;
}

export function Sparkline({
  points,
  width = 140,
  height = 40,
  band = null,
  showSinglePoint = true,
  title,
  unit = "",
  decimals = 1,
}: SparklineProps) {
  const usable = points.filter((p) => typeof p.value === "number") as Array<
    SparklinePoint & { value: number }
  >;

  const { pathD, dots, yScale, xScale, valueRange, latest } = useMemo(() => {
    if (usable.length === 0) {
      return { pathD: "", dots: [], yScale: null, xScale: null, valueRange: null, latest: null };
    }
    const values = usable.map((p) => p.value);
    let yMin = Math.min(...values, band?.low ?? Infinity);
    let yMax = Math.max(...values, band?.high ?? -Infinity);
    if (!isFinite(yMin)) yMin = Math.min(...values);
    if (!isFinite(yMax)) yMax = Math.max(...values);
    if (yMax === yMin) {
      // Avoid flat-line / div-by-zero
      const pad = Math.abs(yMin) * 0.1 || 1;
      yMin -= pad;
      yMax += pad;
    }
    const padX = 4;
    const padY = 4;
    const innerW = width - padX * 2;
    const innerH = height - padY * 2;
    const n = usable.length;
    const xStep = n > 1 ? innerW / (n - 1) : 0;

    const project = (idx: number, val: number) => {
      const x = padX + (n === 1 ? innerW / 2 : idx * xStep);
      const y = padY + innerH * (1 - (val - yMin) / (yMax - yMin));
      return [x, y] as const;
    };
    const pts = usable.map((p, i) => project(i, p.value));
    const path = pts
      .map(([x, y], i) => `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`)
      .join(" ");

    return {
      pathD: path,
      dots: pts,
      yScale: { yMin, yMax, padY, innerH },
      xScale: { padX, innerW, n, xStep },
      valueRange: [yMin, yMax],
      latest: usable[usable.length - 1].value,
    };
  }, [usable, width, height, band]);

  if (usable.length === 0) {
    return (
      <div className="text-xs text-muted-foreground">
        {title && <p className="font-medium text-[var(--sapling-dark)]">{title}</p>}
        <p className="mt-0.5">No data</p>
      </div>
    );
  }

  const bandRect = (() => {
    if (!band || !yScale) return null;
    const { yMin, yMax, padY, innerH } = yScale;
    const lo = band.low ?? yMin;
    const hi = band.high ?? yMax;
    if (lo === hi) return null;
    const yLo = padY + innerH * (1 - (Math.max(lo, yMin) - yMin) / (yMax - yMin));
    const yHi = padY + innerH * (1 - (Math.min(hi, yMax) - yMin) / (yMax - yMin));
    return (
      <rect
        x={0}
        y={Math.min(yLo, yHi)}
        width={width}
        height={Math.abs(yLo - yHi)}
        className={`fill-${band.colour ?? "emerald"}-200 opacity-30`}
      />
    );
  })();

  return (
    <div>
      {title && (
        <div className="mb-1 flex items-baseline justify-between gap-2">
          <p className="text-xs font-medium text-[var(--sapling-dark)]">{title}</p>
          {latest != null && (
            <p className="text-xs tabular-nums text-muted-foreground">
              {latest.toFixed(decimals)}{unit && ` ${unit}`}
            </p>
          )}
        </div>
      )}
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="overflow-visible"
        aria-label={title ?? "Sparkline"}
      >
        {bandRect}
        <path
          d={pathD}
          stroke="var(--sapling-orange, #E55A30)"
          strokeWidth="1.5"
          fill="none"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {(dots.length === 1 ? showSinglePoint : true) && dots.map(([x, y], i) => (
          <circle
            key={i}
            cx={x}
            cy={y}
            r={i === dots.length - 1 ? 2.5 : 1.5}
            fill="var(--sapling-orange, #E55A30)"
          />
        ))}
      </svg>
      {valueRange && (
        <div className="mt-0.5 flex justify-between text-[10px] text-muted-foreground tabular-nums">
          <span>{valueRange[0].toFixed(decimals)}</span>
          <span>{usable.length} {usable.length === 1 ? "point" : "points"}</span>
          <span>{valueRange[1].toFixed(decimals)}</span>
        </div>
      )}
    </div>
  );
}
