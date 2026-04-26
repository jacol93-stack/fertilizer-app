/**
 * CSV parsing + column mapping helpers for the bulk-import flow.
 *
 * Wraps papaparse with auto-detection of common header variations
 * (Block / Block Name / Field / Lot etc. all map to the same target).
 * Lab CSVs from NViroTek and similar SA labs use varying headers per
 * report; we normalise them down to a canonical key before sending to
 * the backend.
 */
import Papa from "papaparse";

export interface ParsedSheet {
  headers: string[];
  rows: Record<string, string>[];
  raw_row_count: number;
}

/** Normalise a header — lowercase, trim, strip punctuation. */
export function normaliseHeader(h: string): string {
  return h.toLowerCase().trim().replace(/[^\w\s]/g, "").replace(/\s+/g, "_");
}

/** Parse a CSV file into rows of {header_normalised: cell_value}. */
export async function parseCsvFile(file: File): Promise<ParsedSheet> {
  return new Promise((resolve, reject) => {
    Papa.parse<Record<string, string>>(file, {
      header: true,
      skipEmptyLines: true,
      transformHeader: normaliseHeader,
      complete: (result) => {
        const headers = result.meta.fields ?? [];
        const rows = result.data.filter(
          (r) => Object.values(r).some((v) => v !== "" && v != null),
        );
        resolve({
          headers,
          rows,
          raw_row_count: result.data.length,
        });
      },
      error: (err) => reject(err),
    });
  });
}

/** Pick the first present value across a list of header aliases. */
export function pickField(row: Record<string, string>, aliases: string[]): string | undefined {
  for (const alias of aliases) {
    const norm = normaliseHeader(alias);
    if (row[norm] != null && row[norm] !== "") return row[norm];
  }
  return undefined;
}

/** Coerce to a positive number or null (empty string / non-numeric → null). */
export function toNumber(v: string | undefined): number | null {
  if (v == null || v === "") return null;
  const cleaned = v.trim().replace(/,/g, ".");
  const n = parseFloat(cleaned);
  return isFinite(n) ? n : null;
}

export function toInt(v: string | undefined): number | null {
  const n = toNumber(v);
  return n == null ? null : Math.trunc(n);
}

// ─── Field-row mapping (Excel sheet → BulkFieldRow) ─────────────────

export interface BulkFieldRowParsed {
  key: string;
  name: string;
  size_ha?: number | null;
  crop?: string | null;
  cultivar?: string | null;
  crop_type?: "annual" | "perennial" | null;
  planting_date?: string | null;
  tree_age?: number | null;
  pop_per_ha?: number | null;
  yield_target?: number | null;
  yield_unit?: string | null;
  irrigation_type?: "drip" | "pivot" | "micro" | "flood" | "none" | null;
  fertigation_capable?: boolean | null;
  soil_type?: string | null;
  notes?: string | null;
  /** Validation messages — surfaced in the preview UI. */
  warnings: string[];
  /** Hard errors that would reject this row server-side. */
  errors: string[];
}

const FIELD_NAME_ALIASES = ["block", "block name", "field", "field name", "lot", "name", "block id"];
const SIZE_ALIASES = ["size", "size ha", "area", "area ha", "hectares", "ha"];
const CROP_ALIASES = ["crop", "commodity"];
const CULTIVAR_ALIASES = ["cultivar", "variety", "var"];
const CROP_TYPE_ALIASES = ["crop type", "crop_type", "type"];
const PLANTING_DATE_ALIASES = ["planting date", "planted", "planted on", "establishment date"];
const TREE_AGE_ALIASES = ["tree age", "age", "years", "yrs"];
const POP_ALIASES = ["pop per ha", "pop_per_ha", "trees per ha", "plants per ha", "population"];
const YIELD_TARGET_ALIASES = ["yield target", "target yield", "expected yield", "target"];
const YIELD_UNIT_ALIASES = ["yield unit", "unit"];
const IRRIGATION_ALIASES = ["irrigation", "irrigation type", "irrigation_type"];
const FERTIGATION_ALIASES = ["fertigation", "fertigation capable", "injection", "has fertigation"];
const SOIL_TYPE_ALIASES = ["soil", "soil type", "soil_type"];
const NOTES_ALIASES = ["notes", "comment", "comments", "remarks"];

const VALID_IRRIGATION = new Set(["drip", "pivot", "micro", "flood", "none"]);

function parseBoolish(v: string | undefined): boolean | null {
  if (v == null || v === "") return null;
  const s = v.trim().toLowerCase();
  if (["yes", "y", "true", "1", "ja"].includes(s)) return true;
  if (["no", "n", "false", "0", "nee"].includes(s)) return false;
  return null;
}

export function mapFieldRow(row: Record<string, string>, idx: number): BulkFieldRowParsed {
  const warnings: string[] = [];
  const errors: string[] = [];

  const name = (pickField(row, FIELD_NAME_ALIASES) ?? "").trim();
  if (!name) errors.push("Block name is required");

  const cropTypeRaw = pickField(row, CROP_TYPE_ALIASES)?.toLowerCase().trim();
  let crop_type: "annual" | "perennial" | null = null;
  if (cropTypeRaw === "annual" || cropTypeRaw === "perennial") {
    crop_type = cropTypeRaw;
  } else if (cropTypeRaw) {
    warnings.push(`Unknown crop type "${cropTypeRaw}" — skipped`);
  }

  const irrRaw = pickField(row, IRRIGATION_ALIASES)?.toLowerCase().trim();
  let irrigation_type: BulkFieldRowParsed["irrigation_type"] = null;
  if (irrRaw && VALID_IRRIGATION.has(irrRaw)) {
    irrigation_type = irrRaw as BulkFieldRowParsed["irrigation_type"];
  } else if (irrRaw) {
    warnings.push(`Unknown irrigation type "${irrRaw}" — skipped`);
  }

  return {
    key: `row-${idx}`,
    name,
    size_ha: toNumber(pickField(row, SIZE_ALIASES)),
    crop: pickField(row, CROP_ALIASES) ?? null,
    cultivar: pickField(row, CULTIVAR_ALIASES) ?? null,
    crop_type,
    planting_date: pickField(row, PLANTING_DATE_ALIASES) ?? null,
    tree_age: toInt(pickField(row, TREE_AGE_ALIASES)),
    pop_per_ha: toInt(pickField(row, POP_ALIASES)),
    yield_target: toNumber(pickField(row, YIELD_TARGET_ALIASES)),
    yield_unit: pickField(row, YIELD_UNIT_ALIASES) ?? null,
    irrigation_type,
    fertigation_capable: parseBoolish(pickField(row, FERTIGATION_ALIASES)),
    soil_type: pickField(row, SOIL_TYPE_ALIASES) ?? null,
    notes: pickField(row, NOTES_ALIASES) ?? null,
    warnings,
    errors,
  };
}

// ─── Yield-row mapping (Excel sheet → BulkYieldRow) ─────────────────

export interface BulkYieldRowParsed {
  field_name: string;
  season: string;
  yield_actual: number | null;
  yield_unit: string;
  harvest_date?: string | null;
  source: string;
  notes?: string | null;
  warnings: string[];
  errors: string[];
}

const SEASON_ALIASES = ["season", "year", "harvest year"];
const YIELD_ACTUAL_ALIASES = ["yield", "actual yield", "yield actual", "harvest", "tons", "t per ha", "t ha"];
const HARVEST_DATE_ALIASES = ["harvest date", "harvested", "date"];

export function mapYieldRow(row: Record<string, string>): BulkYieldRowParsed {
  const warnings: string[] = [];
  const errors: string[] = [];
  const field_name = (pickField(row, FIELD_NAME_ALIASES) ?? "").trim();
  const season = (pickField(row, SEASON_ALIASES) ?? "").trim();
  const yield_actual = toNumber(pickField(row, YIELD_ACTUAL_ALIASES));
  const yield_unit = (pickField(row, YIELD_UNIT_ALIASES) ?? "t/ha").trim();
  const harvest_date = pickField(row, HARVEST_DATE_ALIASES) ?? null;
  const notes = pickField(row, NOTES_ALIASES) ?? null;

  if (!field_name) errors.push("Block name is required");
  if (!season) errors.push("Season is required");
  if (yield_actual == null || yield_actual <= 0) errors.push("Yield must be a positive number");

  return {
    field_name,
    season,
    yield_actual,
    yield_unit,
    harvest_date,
    source: "imported",
    notes,
    warnings,
    errors,
  };
}
