"""Generate the crop-data coverage audit at docs/CROP_DATA_COVERAGE.md.

The audit is a snapshot of what the live Supabase has per crop across the
ten per-crop reference tables, with the gaps rendered explicitly so an
agronomist can see "Macadamia has no pH (KCl) override row yet" at a
glance instead of having to know the universe of expected parameters.

Usage:
    python sapling-api/scripts/generate_crop_coverage.py

Pulls live state from Supabase via the API's existing admin client, so
you need the sapling-api venv active (env vars loaded from
`sapling-api/.env`).

The output is a single markdown file in `docs/`, version-controlled so
each citation that lands in the DB diffs cleanly here too.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Make `app` importable when running from anywhere.
_HERE = Path(__file__).resolve().parent
_API_ROOT = _HERE.parent
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.supabase_client import get_supabase_admin
from app.services.soil_canonicaliser import CANONICAL_PARAMETERS


# ── Per-crop reference tables we audit ──────────────────────────────
TABLES = [
    "crop_requirements",
    "crop_sufficiency_overrides",
    "crop_growth_stages",
    "fertilizer_rate_tables",
    "fertasa_leaf_norms",
    "fertasa_nutrient_removal",
    "perennial_age_factors",
    "crop_calc_flags",
    "crop_yield_benchmarks",
    "crop_application_methods",
]

# Soil parameters worth a per-crop override row. Filtered from
# CANONICAL_PARAMETERS to drop ratios / saturations / physical params
# that don't typically vary per crop.
CROP_RELEVANT_SOIL_PARAMS = [
    "pH (KCl)", "pH (H2O)",
    "N (total)",
    "P (Bray-1)", "P (Citric acid)", "P (Olsen)",
    "K", "Ca", "Mg", "S", "Na",
    "B", "Zn", "Fe", "Mn", "Cu", "Mo",
    "Org C", "CEC",
]

# Leaf elements the engine reads from fertasa_leaf_norms.
LEAF_ELEMENTS = ["N", "P", "K", "Ca", "Mg", "S", "B", "Zn", "Fe", "Mn", "Cu", "Mo"]


# ── Markdown helpers ────────────────────────────────────────────────


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a markdown table with sensible separators. Empty `rows` →
    a placeholder line so the section doesn't render as a stray header."""
    if not rows:
        return "_No rows._\n"
    out = ["| " + " | ".join(headers) + " |"]
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        out.append("| " + " | ".join(str(c) if c is not None and c != "" else "—" for c in r) + " |")
    return "\n".join(out) + "\n"


def fmt(v) -> str:
    """Render a cell value defensively — None/empty → em-dash, numbers
    print without trailing zeros, strings escape pipes."""
    if v is None or v == "":
        return "—"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v).replace("|", "\\|")


def slug(crop: str) -> str:
    return crop.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "-")


# ── Per-table renderers ─────────────────────────────────────────────


def section_base_requirements(row: dict) -> str:
    """`crop_requirements` is the master row for the crop — base nutrient
    targets, type, default yield, pop/ha, age-to-bearing."""
    if not row:
        return "_No `crop_requirements` row — this crop is unknown to the engine._\n"
    fields_order = [
        ("crop_type", "Crop type"),
        ("type", "Type (legacy)"),
        ("parent_crop", "Parent crop"),
        ("default_yield", "Default yield"),
        ("yield_unit", "Yield unit"),
        ("pop_per_ha", "Population / ha"),
        ("years_to_bearing", "Years to bearing"),
        ("years_to_full_bearing", "Years to full bearing"),
        ("n", "N (target/uptake)"),
        ("p", "P"),
        ("k", "K"),
        ("ca", "Ca"),
        ("mg", "Mg"),
        ("s", "S"),
        ("b", "B"),
        ("zn", "Zn"),
        ("fe", "Fe"),
        ("mn", "Mn"),
        ("cu", "Cu"),
        ("mo", "Mo"),
        ("customer_ready", "Customer-ready flag"),
    ]
    rows = [[label, fmt(row.get(key))] for key, label in fields_order]
    return md_table(["Field", "Value"], rows)


def section_sufficiency_overrides(crop: str, rows: list[dict]) -> str:
    """`crop_sufficiency_overrides` — per-soil-parameter bands. We render
    every CROP_RELEVANT_SOIL_PARAM as a row so empties show up explicitly
    as gaps, not by their absence. Extra (non-canonical) override rows
    surface below the canonical block."""
    by_param = {r["parameter"]: r for r in rows if r.get("parameter")}
    table_rows = []
    for p in CROP_RELEVANT_SOIL_PARAMS:
        r = by_param.get(p)
        if r:
            table_rows.append([
                p,
                fmt(r.get("very_low_max")),
                fmt(r.get("low_max")),
                fmt(r.get("optimal_max")),
                fmt(r.get("high_max")),
                fmt(r.get("notes")),
            ])
        else:
            table_rows.append([f"**{p}**", "—", "—", "—", "—", "_needs source_"])
    extra = [p for p in by_param if p not in CROP_RELEVANT_SOIL_PARAMS]
    out = md_table(
        ["Parameter", "Very Low ≤", "Low ≤", "Optimal ≤", "High ≤", "Source / notes"],
        table_rows,
    )
    if extra:
        out += "\n_Extra rows on this crop outside the canonical soil schema:_ "
        out += ", ".join(f"`{p}`" for p in sorted(extra)) + "\n"
    return out


def section_growth_stages(rows: list[dict]) -> str:
    rows_sorted = sorted(rows, key=lambda r: (r.get("stage_order") or 0))
    table_rows = []
    for r in rows_sorted:
        months = f"{fmt(r.get('month_start'))}–{fmt(r.get('month_end'))}"
        table_rows.append([
            fmt(r.get("stage_order")),
            fmt(r.get("stage_name")),
            months,
            fmt(r.get("num_applications")),
            fmt(r.get("n_pct")),
            fmt(r.get("p_pct")),
            fmt(r.get("k_pct")),
            fmt(r.get("ca_pct")),
            fmt(r.get("mg_pct")),
            fmt(r.get("default_method")),
            fmt(r.get("notes")),
        ])
    return md_table(
        ["#", "Stage", "Months", "Apps", "N %", "P %", "K %", "Ca %", "Mg %", "Method", "Notes"],
        table_rows,
    )


def section_rate_tables(rows: list[dict]) -> str:
    """fertilizer_rate_tables — 2D rate cells (soil-test × yield → kg/ha).
    Heavily-cited table; render compact with source per cell."""
    rows_sorted = sorted(rows, key=lambda r: (r.get("nutrient") or "", r.get("soil_test_min") or 0))
    table_rows = []
    for r in rows_sorted:
        soil_band = f"{fmt(r.get('soil_test_min'))}–{fmt(r.get('soil_test_max'))} {fmt(r.get('soil_test_unit'))}"
        yield_band = f"{fmt(r.get('yield_min_t_ha'))}–{fmt(r.get('yield_max_t_ha'))}"
        rate = f"{fmt(r.get('rate_min_kg_ha'))}–{fmt(r.get('rate_max_kg_ha'))}"
        source = f"{fmt(r.get('source'))} {fmt(r.get('source_section'))}".strip()
        table_rows.append([
            fmt(r.get("nutrient")),
            fmt(r.get("soil_test_method")),
            soil_band,
            yield_band,
            rate,
            fmt(r.get("texture") or r.get("region")),
            source,
        ])
    return md_table(
        ["Nutrient", "Soil method", "Soil-test band", "Yield band (t/ha)", "Rate (kg/ha)", "Filter", "Source"],
        table_rows,
    )


def section_leaf_norms(crop: str, rows: list[dict]) -> str:
    by_element = defaultdict(list)
    for r in rows:
        el = r.get("element")
        if el:
            by_element[el].append(r)
    table_rows = []
    for el in LEAF_ELEMENTS:
        rs = by_element.get(el, [])
        if not rs:
            table_rows.append([f"**{el}**", "—", "—", "—", "—", "—", "_needs source_"])
            continue
        for r in rs:
            sufficient = f"{fmt(r.get('sufficient_min'))}–{fmt(r.get('sufficient_max'))}"
            table_rows.append([
                el,
                fmt(r.get("sample_part")),
                fmt(r.get("sample_timing")),
                fmt(r.get("low_max")),
                sufficient,
                fmt(r.get("excess_min")),
                fmt(r.get("source_section") or r.get("notes")),
            ])
    extra = [el for el in by_element if el not in LEAF_ELEMENTS]
    out = md_table(
        ["Element", "Part", "Timing", "Low ≤", "Sufficient", "Excess ≥", "Source / notes"],
        table_rows,
    )
    if extra:
        out += "\n_Extra leaf rows outside the canonical element set:_ "
        out += ", ".join(f"`{el}`" for el in sorted(extra)) + "\n"
    return out


def section_nutrient_removal(rows: list[dict]) -> str:
    table_rows = []
    for r in rows:
        table_rows.append([
            fmt(r.get("plant_part")),
            fmt(r.get("yield_unit")),
            fmt(r.get("n")),
            fmt(r.get("p")),
            fmt(r.get("k")),
            fmt(r.get("ca")),
            fmt(r.get("mg")),
            fmt(r.get("s")),
            fmt(r.get("source_section") or r.get("notes")),
        ])
    return md_table(
        ["Part", "Per", "N", "P", "K", "Ca", "Mg", "S", "Source / notes"],
        table_rows,
    )


def section_age_factors(rows: list[dict]) -> str:
    rows_sorted = sorted(rows, key=lambda r: (r.get("age_min") or 0))
    table_rows = []
    for r in rows_sorted:
        age = f"{fmt(r.get('age_min'))}–{fmt(r.get('age_max'))}"
        table_rows.append([
            fmt(r.get("age_label")),
            age,
            fmt(r.get("general_factor")),
            fmt(r.get("n_factor")),
            fmt(r.get("p_factor")),
            fmt(r.get("k_factor")),
            fmt(r.get("notes")),
        ])
    return md_table(
        ["Age label", "Age range (yr)", "General", "N", "P", "K", "Notes"],
        table_rows,
    )


def section_yield_benchmarks(rows: list[dict]) -> str:
    table_rows = []
    for r in rows:
        table_rows.append([
            fmt(r.get("cultivar")),
            fmt(r.get("region")),
            fmt(r.get("irrigation_regime")),
            fmt(r.get("low_t_per_ha")),
            fmt(r.get("typical_t_per_ha")),
            fmt(r.get("high_t_per_ha")),
            fmt(r.get("yield_unit")),
            fmt(r.get("source")),
        ])
    return md_table(
        ["Cultivar", "Region", "Water regime", "Low t/ha", "Typical t/ha", "High t/ha", "Unit", "Source"],
        table_rows,
    )


def section_calc_flags(rows: list[dict]) -> str:
    table_rows = []
    for r in rows:
        table_rows.append([
            fmt(r.get("skip_cation_ratio_path")),
            fmt(r.get("source")),
            fmt(r.get("source_section")),
            fmt(r.get("source_year")),
            fmt(r.get("tier")),
            fmt(r.get("source_note")),
        ])
    return md_table(
        ["skip_cation_ratio_path", "Source", "Section", "Year", "Tier", "Note"],
        table_rows,
    )


def section_application_methods(rows: list[dict]) -> str:
    table_rows = []
    for r in rows:
        table_rows.append([
            fmt(r.get("method")),
            fmt(r.get("is_default")),
            fmt(r.get("nutrients_suited")),
            fmt(r.get("timing_notes")),
            fmt(r.get("crop_specific_notes")),
        ])
    return md_table(
        ["Method", "Default", "Nutrients suited", "Timing", "Crop notes"],
        table_rows,
    )


# ── Main ────────────────────────────────────────────────────────────


def main() -> None:
    sb = get_supabase_admin()

    data: dict[str, list[dict]] = {}
    for t in TABLES:
        try:
            data[t] = sb.table(t).select("*").execute().data or []
        except Exception as exc:
            print(f"[warn] failed to read {t}: {exc}", file=sys.stderr)
            data[t] = []

    # Master crop list comes from crop_requirements. Sort alphabetically
    # — easier to scan than the DB's natural order.
    crops = sorted({r["crop"] for r in data["crop_requirements"] if r.get("crop")})

    # Bucket per-crop rows for every table.
    by_crop: dict[str, dict[str, list[dict]]] = {c: {t: [] for t in TABLES} for c in crops}
    for t in TABLES:
        for r in data[t]:
            c = r.get("crop")
            if c in by_crop:
                by_crop[c][t].append(r)

    # ── Render ────────────────────────────────────────────────
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out: list[str] = []
    out.append(f"# Crop Data Coverage Audit\n")
    out.append(
        f"_Generated {now}. {len(crops)} crops in `crop_requirements`._\n"
        f"_Regenerate: `python sapling-api/scripts/generate_crop_coverage.py`_\n"
    )
    out.append(
        "Every blank cell or `_needs source_` marker is a literature search. "
        "When a citation lands, add the row to the appropriate table and rerun "
        "this script — the gap will close on the next diff.\n"
    )

    # Coverage matrix
    out.append("## Summary — coverage matrix\n")
    out.append("Counts are rows in each per-crop table.\n")
    matrix_headers = [
        "Crop",
        "base reqs",
        "soil bands",
        "growth stages",
        "rate cells",
        "leaf norms",
        "removal",
        "age factors",
        "yield bench",
        "calc flags",
        "methods",
    ]
    matrix_rows = []
    for c in crops:
        rows_per_table = by_crop[c]
        link = f"[{c}](#{slug(c)})"
        matrix_rows.append([
            link,
            len(rows_per_table["crop_requirements"]),
            len(rows_per_table["crop_sufficiency_overrides"]),
            len(rows_per_table["crop_growth_stages"]),
            len(rows_per_table["fertilizer_rate_tables"]),
            len(rows_per_table["fertasa_leaf_norms"]),
            len(rows_per_table["fertasa_nutrient_removal"]),
            len(rows_per_table["perennial_age_factors"]),
            len(rows_per_table["crop_yield_benchmarks"]),
            len(rows_per_table["crop_calc_flags"]),
            len(rows_per_table["crop_application_methods"]),
        ])
    out.append(md_table(matrix_headers, matrix_rows))

    # Per-crop sections
    out.append("\n---\n\n## Per-crop detail\n")
    for c in crops:
        rows_per_table = by_crop[c]
        base = next(iter(rows_per_table["crop_requirements"]), {})
        out.append(f"### {c}\n")
        out.append(f'<a id="{slug(c)}"></a>\n')

        out.append("**Base requirements** (`crop_requirements`)\n")
        out.append(section_base_requirements(base))

        out.append("**Soil sufficiency bands** (`crop_sufficiency_overrides`)\n")
        out.append(
            "_Engine merges these on top of universal `soil_sufficiency`. "
            "Bold rows are gaps — generic bands apply until a citation is added._\n"
        )
        out.append(section_sufficiency_overrides(c, rows_per_table["crop_sufficiency_overrides"]))

        out.append("**Growth stages** (`crop_growth_stages`)\n")
        out.append(section_growth_stages(rows_per_table["crop_growth_stages"]))

        out.append("**Rate-table cells** (`fertilizer_rate_tables`)\n")
        out.append(section_rate_tables(rows_per_table["fertilizer_rate_tables"]))

        out.append("**Leaf norms** (`fertasa_leaf_norms`)\n")
        out.append(section_leaf_norms(c, rows_per_table["fertasa_leaf_norms"]))

        out.append("**Nutrient removal** (`fertasa_nutrient_removal`)\n")
        out.append(section_nutrient_removal(rows_per_table["fertasa_nutrient_removal"]))

        out.append("**Perennial age factors** (`perennial_age_factors`)\n")
        out.append(section_age_factors(rows_per_table["perennial_age_factors"]))

        out.append("**Yield benchmarks** (`crop_yield_benchmarks`)\n")
        out.append(section_yield_benchmarks(rows_per_table["crop_yield_benchmarks"]))

        out.append("**Calc flags** (`crop_calc_flags`)\n")
        out.append(section_calc_flags(rows_per_table["crop_calc_flags"]))

        out.append("**Application methods** (`crop_application_methods`)\n")
        out.append(section_application_methods(rows_per_table["crop_application_methods"]))

        out.append("\n")

    # Write the file
    repo_root = _API_ROOT.parent
    out_path = repo_root / "docs" / "CROP_DATA_COVERAGE.md"
    out_path.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  {len(crops)} crops, {sum(len(by_crop[c]['crop_sufficiency_overrides']) for c in crops)} sufficiency override rows")


if __name__ == "__main__":
    main()
