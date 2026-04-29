"""Layer 2 of the three-layer defense — every number in the rendered
prose must trace to the artifact.

The contract is conservative: we extract numerics from prose, then
confirm each appears (verbatim or within rounding tolerance) somewhere
in the artifact JSON. A number that can't be matched is reported as
unverified — the caller (policeman) decides whether to escalate to
FAIL.

We deliberately accept loose matching:
  - "2.5 t/ha" matches artifact value 2.5 anywhere
  - "150" matches 150.0 or 150
  - "85%" matches 0.85, 85, 85.0
  - "5:1" matches a Ca:Mg ratio entry of 5.0
This is intentional — the prose layer is allowed to round 154.7 → 155,
or to reformat 0.85 → 85%. The policeman catches actual fabrications,
not formatting choices.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable


# Match numbers in prose: integers, decimals, optional unit hints.
# We capture the bare numeric so matching collapses across units.
_NUMBER_RX = re.compile(r"\b(\d+(?:\.\d+)?)\b")

# Numbers below this threshold are treated as ambient ("first", "two
# blocks", "three to four weeks") and don't need to trace to the
# artifact. Keeps the validator from chasing every "2" in the prose.
_AMBIENT_MAX = 12.0

# Tolerance when matching prose numbers against artifact numbers. The
# prose can say 155 when the artifact has 154.7; both are correct. We
# allow ±2% relative or ±0.5 absolute, whichever is larger.
_REL_TOLERANCE = 0.02
_ABS_TOLERANCE = 0.5


@dataclass(frozen=True)
class UnverifiedNumber:
    value: float
    excerpt: str
    section: str


def extract_artifact_numbers(artifact_json: dict[str, Any]) -> set[float]:
    """Walk the artifact JSON and collect every numeric value. We keep
    them in a flat set + also stash a few derived forms: percentages
    written as 0.85 are collected as both 0.85 and 85.
    """
    seen: set[float] = set()

    def _walk(node):
        if isinstance(node, dict):
            for v in node.values():
                _walk(v)
        elif isinstance(node, (list, tuple)):
            for v in node:
                _walk(v)
        elif isinstance(node, bool):
            return  # bool subclasses int, skip
        elif isinstance(node, (int, float)):
            f = float(node)
            seen.add(f)
            # Percentage duals — 0.85 ↔ 85, 0.05 ↔ 5
            if 0 < f < 1:
                seen.add(round(f * 100, 4))
            if 1 <= f <= 100:
                seen.add(round(f / 100, 4))
            # Round-down / round-up duals so 154.7 in artifact matches
            # "155" in prose without a tolerance pass.
            seen.add(round(f))
            seen.add(round(f, 1))
        elif isinstance(node, str):
            # Numbers can also live in stringified prose fields inside
            # the artifact (e.g. headline_signals). Pull them too.
            for match in _NUMBER_RX.findall(node):
                try:
                    seen.add(float(match))
                except ValueError:
                    pass

    _walk(artifact_json)
    return seen


def find_unverified_numbers(
    *,
    section: str,
    prose: str,
    artifact_numbers: set[float],
) -> list[UnverifiedNumber]:
    """Extract numbers from one section's prose and report any that
    don't trace to the artifact within tolerance."""
    if not prose:
        return []
    out: list[UnverifiedNumber] = []
    for match in _NUMBER_RX.finditer(prose):
        raw = match.group(1)
        try:
            value = float(raw)
        except ValueError:
            continue
        if value <= _AMBIENT_MAX and "." not in raw:
            # Small whole numbers ("two blocks", "5 days") are ambient
            # — these would create false positives. Decimals like 2.5
            # still get checked even if small.
            continue
        if _matches_any(value, artifact_numbers):
            continue
        # Capture context — 30 chars either side of the offending
        # number so the policeman or admin reviewer can see what was
        # claimed.
        start = max(0, match.start() - 30)
        end = min(len(prose), match.end() + 30)
        excerpt = prose[start:end].replace("\n", " ").strip()
        out.append(UnverifiedNumber(value=value, excerpt=excerpt, section=section))
    return out


def validate_prose(
    *,
    artifact_json: dict[str, Any],
    rendered_prose: dict[str, str],
) -> list[UnverifiedNumber]:
    """Run all sections through the validator. Returns a flat list of
    unverified numbers across every section. Empty list = clean."""
    nums = extract_artifact_numbers(artifact_json)
    unverified: list[UnverifiedNumber] = []
    for section_id, prose in rendered_prose.items():
        unverified.extend(
            find_unverified_numbers(
                section=section_id,
                prose=prose,
                artifact_numbers=nums,
            )
        )
    return unverified


# ============================================================
# Internals
# ============================================================

def _matches_any(value: float, candidates: Iterable[float]) -> bool:
    abs_tol = max(_ABS_TOLERANCE, abs(value) * _REL_TOLERANCE)
    for c in candidates:
        if abs(value - c) <= abs_tol:
            return True
    return False


def to_jsonable(model_or_dict) -> dict:
    """Convert a Pydantic model (or dict) to the canonical JSON dict
    used by `extract_artifact_numbers`. Keeps the validator pure-data."""
    if hasattr(model_or_dict, "model_dump"):
        return model_or_dict.model_dump(mode="json")
    if isinstance(model_or_dict, dict):
        return json.loads(json.dumps(model_or_dict, default=str))
    return json.loads(json.dumps(model_or_dict, default=str))
