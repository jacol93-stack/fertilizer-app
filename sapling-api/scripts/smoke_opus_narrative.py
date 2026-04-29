"""Opus narrative pipeline smoke test.

Wires the real Opus call against the mac_levubu reference artifact (Anton-
shaped: macadamia, multiple blocks, real soil findings) and prints:

  - the four section overrides Opus produced
  - the policeman + fact-validator verdict
  - any issues raised by the audit layers
  - token + cost telemetry per call

Run from sapling-api root:
    ./venv/bin/python scripts/smoke_opus_narrative.py

Requires ANTHROPIC_API_KEY in env. This script makes ONE real API call per
section (~4 sections), so expect $0.50–$1.50 + 30–60s wall time.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Ensure repo root is on sys.path so app.* imports resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # type: ignore

load_dotenv()

from app.services.pdf_renderer import _baseline_for_narrative, _build_context
from app.services.narrative.opus_renderer import enhance_artifact_prose
from app.services.programme_builder_orchestrator import build_programme
from tests.fixtures.reference_block_inputs import reference_mac_levubu_input


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — aborting.", file=sys.stderr)
        return 1

    print("Building reference artifact (mac_levubu)…")
    artifact = build_programme(reference_mac_levubu_input())
    context = _build_context(artifact)
    baseline = _baseline_for_narrative(context, artifact)

    baseline_keys = sorted(baseline.keys())
    print(f"Baseline prose keys: {baseline_keys}")
    print()

    print("Firing Opus narrative pipeline (this will take 30–60s)…")
    started = time.monotonic()
    result = enhance_artifact_prose(artifact, baseline=baseline, mode="client")
    duration = time.monotonic() - started

    print()
    print("=" * 70)
    print(f"VERDICT: {result.verdict}")
    print(f"DURATION: {duration:.1f}s ({result.duration_seconds:.1f}s in pipeline)")
    print(f"SECTIONS: {result.section_count}")
    print(
        f"TOKENS: in={result.input_tokens:,} out={result.output_tokens:,} "
        f"cache_read={result.cache_read_tokens:,} cache_write={result.cache_write_tokens:,}"
    )
    # Cost estimate at Opus 4.7 list pricing (input $15/MTok, output $75/MTok,
    # cache reads $1.50/MTok, cache writes $18.75/MTok). Order-of-magnitude only.
    cost = (
        result.input_tokens * 15 / 1_000_000
        + result.output_tokens * 75 / 1_000_000
        + result.cache_read_tokens * 1.5 / 1_000_000
        + result.cache_write_tokens * 18.75 / 1_000_000
    )
    print(f"COST (estimated): ${cost:.3f}")
    print(f"USED OPUS PROSE: {result.used_opus_prose}")
    print("=" * 70)

    if result.issues:
        print()
        print("ISSUES:")
        for issue in result.issues:
            print(f"  [{issue['severity'].upper()}] {issue['category']} @ {issue['where']}")
            print(f"    what: {issue['what']}")
            print(f"    fix:  {issue['fix']}")

    print()
    print("OVERRIDES:")
    for section_id, value in result.overrides.items():
        print(f"\n--- {section_id} ---")
        if isinstance(value, str):
            print(value)
        else:
            print(json.dumps(value, indent=2, default=str))

    print()
    print("BASELINE FOR COMPARISON:")
    for section_id in result.overrides:
        baseline_value = baseline.get(section_id)
        if baseline_value is None:
            continue
        print(f"\n--- {section_id} (baseline) ---")
        if isinstance(baseline_value, str):
            print(baseline_value)
        else:
            print(json.dumps(baseline_value, indent=2, default=str))

    return 0 if result.verdict != "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
