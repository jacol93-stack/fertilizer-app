import { SOIL_PARAMS } from "./types";

/**
 * Convert string soil values to numeric (null for empty).
 */
export function numericSoilValues(
  soilValues: Record<string, string>
): Record<string, number | null> {
  const result: Record<string, number | null> = {};
  for (const [key, val] of Object.entries(soilValues)) {
    result[key] = val ? parseFloat(val) : null;
  }
  return result;
}

/**
 * Import extracted sample values into soil or leaf form state.
 * Returns the mapped values as a Record<string, string>.
 */
export function importSampleValues(
  values: Record<string, number>,
  target: "soil" | "leaf"
): Record<string, string> {
  const normalize = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
  const extractedNormalized = Object.entries(values).map(([k, v]) => ({
    key: k,
    norm: normalize(k),
    value: v,
  }));

  const mapped: Record<string, string> = {};

  if (target === "leaf") {
    for (const elem of ["N", "P", "K", "Ca", "Mg", "S", "Fe", "Mn", "Zn", "Cu", "B", "Mo", "Na"]) {
      const match = extractedNormalized.find(
        (e) => e.norm === normalize(elem) || e.key.toUpperCase() === elem
      );
      if (match && match.value != null) mapped[elem] = String(match.value);
    }
  } else {
    for (const params of Object.values(SOIL_PARAMS)) {
      for (const param of params) {
        const paramNorm = normalize(param);
        const match = extractedNormalized.find(
          (e) =>
            e.norm === paramNorm ||
            e.norm.includes(paramNorm) ||
            paramNorm.includes(e.norm)
        );
        if (match && match.value != null) mapped[param] = String(match.value);
      }
    }
  }

  return mapped;
}

/**
 * Group extracted samples by crop and compute per-parameter averages.
 */
export function groupSamplesByCrop(
  samples: Array<{ crop?: string; values: Record<string, number> }>
): Map<string, { samples: typeof samples; averaged: Record<string, number> }> {
  const groups = new Map<string, { samples: typeof samples; averaged: Record<string, number> }>();

  for (const sample of samples) {
    const key = sample.crop || "Unknown";
    if (!groups.has(key)) {
      groups.set(key, { samples: [], averaged: {} });
    }
    groups.get(key)!.samples.push(sample);
  }

  for (const [, group] of groups) {
    const allKeys = new Set<string>();
    for (const s of group.samples) {
      for (const k of Object.keys(s.values)) allKeys.add(k);
    }
    for (const k of allKeys) {
      const vals = group.samples
        .map((s) => s.values[k])
        .filter((v) => v != null && !isNaN(v));
      if (vals.length > 0) {
        group.averaged[k] = vals.reduce((a, b) => a + b, 0) / vals.length;
      }
    }
  }

  return groups;
}
