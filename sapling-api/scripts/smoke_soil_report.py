"""End-to-end soil report smoke — synthetic Anton-shaped multi-block + history.

Builds a multi-block soil report against synthetic data shaped like
Anton's Laborie farm (16 blocks, mixed acidity/alkalinity/Ca:Mg
issues), generates the Opus narrative, prints the verdict + telemetry,
renders the PDF.

Run:
    ./venv/bin/python scripts/smoke_soil_report.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # type: ignore
load_dotenv()

from app.services.narrative.opus_renderer import enhance_soil_report_prose
from app.services.pdf_renderer import render_soil_report_pdf
from app.services.soil_report_builder import (
    AnalysisInput,
    BlockAnalysesInput,
    SoilReportBuilderInputs,
    build_soil_report,
)


SUFF = [
    {"parameter": "pH (KCl)", "low_max": 5.0, "optimal_max": 6.5,
     "display_min": 3.5, "display_max": 8.0},
    {"parameter": "Ca", "low_max": 1000, "optimal_max": 2000,
     "display_min": 0, "display_max": 3000},
    {"parameter": "Mg", "low_max": 150, "optimal_max": 400,
     "display_min": 0, "display_max": 600},
    {"parameter": "P (Bray-1)", "low_max": 20, "optimal_max": 40,
     "display_min": 0, "display_max": 80},
    {"parameter": "K", "low_max": 150, "optimal_max": 350,
     "display_min": 0, "display_max": 500},
]


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — running engine baseline only.")
        opus_enabled = False
    else:
        opus_enabled = True

    # Synthetic mac orchard, three signal patterns:
    blocks = [
        # Acidic blocks with multi-year history (mode B trends embedded)
        BlockAnalysesInput(
            block_id="b-7C2", block_name="Blok 7C2", block_area_ha=5.0, crop="Macadamia",
            analyses=[
                AnalysisInput("a-7C2-2023", date(2023, 4, 1), "Lab", "KCl",
                              {"pH (KCl)": 4.3, "Ca": 750, "Mg": 240, "P (Bray-1)": 16, "K": 140, "Na": 50, "CEC": 7.5}),
                AnalysisInput("a-7C2-2024", date(2024, 4, 1), "Lab", "KCl",
                              {"pH (KCl)": 4.5, "Ca": 880, "Mg": 230, "P (Bray-1)": 19, "K": 150, "Na": 50, "CEC": 7.8}),
                AnalysisInput("a-7C2-2025", date(2025, 4, 1), "Lab", "KCl",
                              {"pH (KCl)": 4.7, "Ca": 1020, "Mg": 220, "P (Bray-1)": 22, "K": 160, "Na": 50, "CEC": 8.0}),
                AnalysisInput("a-7C2-2026", date(2026, 4, 1), "Lab", "KCl",
                              {"pH (KCl)": 5.0, "Ca": 1180, "Mg": 210, "P (Bray-1)": 26, "K": 170, "Na": 50, "CEC": 8.2}),
            ],
        ),
        BlockAnalysesInput(
            block_id="b-1A", block_name="Blok 1A", block_area_ha=5.0, crop="Macadamia",
            analyses=[
                AnalysisInput("a-1A-2026", date(2026, 4, 1), "Lab", "KCl",
                              {"pH (KCl)": 4.6, "Ca": 950, "Mg": 230, "P (Bray-1)": 22, "K": 175, "Na": 50, "CEC": 8.1}),
            ],
        ),
        # Alkaline block
        BlockAnalysesInput(
            block_id="b-1B", block_name="Blok 1B", block_area_ha=5.0, crop="Macadamia",
            analyses=[
                AnalysisInput("a-1B-2026", date(2026, 4, 1), "Lab", "KCl",
                              {"pH (KCl)": 7.4, "Ca": 4500, "Mg": 600, "P (Bray-1)": 35, "K": 300, "Na": 80, "CEC": 30}),
            ],
        ),
        # Ca:Mg-low at OK pH
        BlockAnalysesInput(
            block_id="b-1", block_name="Blok 1", block_area_ha=5.0, crop="Macadamia",
            analyses=[
                AnalysisInput("a-1-2026", date(2026, 4, 1), "Lab", "KCl",
                              {"pH (KCl)": 5.8, "Ca": 600, "Mg": 400, "P (Bray-1)": 25, "K": 200, "Na": 50, "CEC": 9}),
            ],
        ),
    ]

    print(f"Building Anton-shaped multi-block + history soil report ({len(blocks)} blocks)...")
    artifact = build_soil_report(SoilReportBuilderInputs(
        title="Anton Muller — Laborie soil snapshot",
        client_name="Anton Muller", farm_name="Laborie",
        blocks=blocks,
        sufficiency_rows=SUFF, param_map_rows=[],
    ))
    print(f"  scope={artifact.header.scope_kind}")
    print(f"  snapshots={len(artifact.soil_snapshots)} trends={len(artifact.trend_reports)} holistic={len(artifact.holistic_signals)}")
    print(f"  decision_trace ({len(artifact.decision_trace)} entries):")
    for line in artifact.decision_trace[:5]:
        print(f"    {line}")

    payload = artifact.to_dict()
    overrides = None
    if opus_enabled:
        print()
        print("Firing Opus narrative pipeline (~15-30s)...")
        started = time.monotonic()
        result = enhance_soil_report_prose(payload)
        duration = time.monotonic() - started
        print(f"  VERDICT: {result.verdict}")
        print(f"  DURATION: {duration:.1f}s ({result.duration_seconds:.1f}s in pipeline)")
        print(f"  SECTIONS: {result.section_count}")
        print(
            f"  TOKENS: in={result.input_tokens:,} out={result.output_tokens:,} "
            f"cache_read={result.cache_read_tokens:,} cache_write={result.cache_write_tokens:,}"
        )
        cost = (
            result.input_tokens * 15 / 1_000_000
            + result.output_tokens * 75 / 1_000_000
            + result.cache_read_tokens * 1.5 / 1_000_000
            + result.cache_write_tokens * 18.75 / 1_000_000
        )
        print(f"  COST: ${cost:.4f}")
        if result.issues:
            print(f"  ISSUES ({len(result.issues)}):")
            for issue in result.issues:
                print(f"    [{issue['severity']}] {issue['category']} @ {issue['where']}: {issue['what'][:120]}")
        if result.overrides:
            overrides = result.overrides
            print(f"  OVERRIDES KEYS: {list(result.overrides.keys())}")
            for k, v in result.overrides.items():
                print(f"\n  --- {k} ---")
                print(f"  {str(v)[:400]}")
        else:
            print("  No overrides applied (FAIL → engine baseline used)")

    print()
    print("Rendering PDF...")
    pdf = render_soil_report_pdf(payload, narrative_overrides=overrides)
    out = Path("tests/fixtures/soil_report_e2e.pdf")
    out.write_bytes(pdf)
    print(f"PDF: {len(pdf):,} bytes → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
