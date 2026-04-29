"""Layer 3 of the three-layer defense — the AI policeman.

Three checks, in order:

  1. Deterministic denylist — raw material names, factory / QC / SOP
     terms, source citations. Any hit is an automatic FAIL.
  2. Deterministic rate caps — foliar B + Zn upper bounds against
     the artifact (not the prose — the policeman doesn't infer rates
     from prose, it confirms the engine's rates are within reason).
  3. Opus critique — Opus reads artifact + prose, returns a structured
     verdict + issue list.

The final verdict is the worst of the three. FAIL anywhere → FAIL.
WARN anywhere → WARN. Otherwise PASS.

Caller contract:
  - PASS → use the Opus prose
  - WARN → use the Opus prose, persist verdict for admin review
  - FAIL → fall back to deterministic prose, persist verdict + issues
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from app.services.narrative.anthropic_client import NarrativeClient
from app.services.narrative.fact_validator import UnverifiedNumber, validate_prose
from app.services.narrative.prompts import (
    POLICEMAN_SYSTEM,
    policeman_user_msg,
)

log = logging.getLogger(__name__)


Verdict = Literal["PASS", "WARN", "FAIL"]
_VERDICT_RANK = {"PASS": 0, "WARN": 1, "FAIL": 2}


# ============================================================
# Deterministic denylist
# ============================================================
#
# This list is the safety net regardless of what Opus says. It catches
# the obvious leaks: raw material names, factory steps, QC checks,
# source citations. The list is checked as case-insensitive whole-word
# matches — substrings inside other words don't fire (e.g. "Urea" in
# "ureasolyte" is rare enough not to worry about, but "UREA" anywhere
# we'll catch).
#
# Sapling's own branded products ARE allowed (Rescue, Rescue + Gypsum)
# so they're explicitly excluded.

_RAW_MATERIAL_TERMS = [
    # Common SA raw materials (noun forms)
    "MAP", "DAP", "Urea", "LAN", "CAN", "MOP", "SOP",
    "KCl", "KNO3", "MKP", "SOA", "TSP", "SSP",
    "Ammonium Sulphate", "Ammonium Nitrate",
    "Calcium Nitrate", "Magnesium Nitrate", "Potassium Nitrate",
    "Potassium Chloride", "Potassium Sulphate",
    "Mono-Ammonium Phosphate", "Di-Ammonium Phosphate",
    "Mono-Potassium Phosphate", "Mono Potassium Phosphate",
    "Triple Super Phosphate", "Single Super Phosphate",
    "Solubor", "Boric Acid",
    "Magnisal", "Krista K", "Multi-K", "Polyfeed", "Calmag",
    "ZinPlus", "Zintrac",
    # Generic compounds farmers also recognise
    "Limestone Ammonium Nitrate",
]

_FACTORY_TERMS = [
    "stock tank", "stock-tank",
    "Part A", "Part B",
    "mixing order",
    "batch number", "batch ID", "lot number",
    "shelf life",
    "EC verification", "EC check",
    "compatibility trial",
    "assay result",
    "QC check", "QC step", "QA check",
    "SOP",  # When used as Standard Operating Procedure rather than the fertiliser; both senses are off-limits in client mode.
]

_SOURCE_CITATION_TERMS = [
    "FERTASA", "SAMAC", "SASRI", "CRI", "CitrusAcademy", "SAAGA",
    "NZAGA", "ARC ", "DALRRD", "Hortgro", "GrainSA",
    "IPNI", "Yara", "Haifa", "CABI", "UC ANR", "Cornell",
    "SAJEV", "HortScience", "Manson & Sheard", "Manson and Sheard",
    "Du Plessis & Koen", "Schoeman", "Cedara", "Ambic",
    "Tier 1", "Tier 2", "Tier 3", "Tier-1", "Tier-2", "Tier-3",
    "according to published",
    "per the SA sufficiency",
]

# Handbook section patterns — "5.7.3", "5.X.Y" — appearing in prose
# is almost always a leaked source citation. Section-number-shaped
# tokens elsewhere (e.g. an A1 / A2 block label) don't match this rx.
_SECTION_NUMBER_RX = re.compile(r"\b\d+\.\d+\.\d+\b")


@dataclass
class Issue:
    severity: Literal["fail", "warn", "info"]
    category: str
    where: str
    what: str
    fix: str = ""


@dataclass
class PolicemanReport:
    verdict: Verdict
    issues: list[Issue] = field(default_factory=list)
    unverified_numbers: list[UnverifiedNumber] = field(default_factory=list)
    opus_raw: Optional[str] = None  # raw policeman response — admin trace

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "issues": [i.__dict__ for i in self.issues],
            "unverified_numbers": [u.__dict__ for u in self.unverified_numbers],
            "opus_raw": self.opus_raw,
        }


# ============================================================
# Public entry point
# ============================================================

def audit(
    *,
    artifact_json: dict[str, Any],
    rendered_prose: dict[str, str],
    client: Optional[NarrativeClient] = None,
    use_opus_critique: bool = True,
) -> PolicemanReport:
    """Run the three-layer audit on a render and return the verdict.

    `client` is optional — only required when `use_opus_critique=True`.
    For unit tests of just the deterministic layers, pass `client=None`
    and `use_opus_critique=False`.
    """
    issues: list[Issue] = []

    # Layer 3a — denylist
    issues.extend(_check_denylist(rendered_prose))

    # Layer 3b — rate caps (against the artifact, not the prose)
    issues.extend(_check_rate_caps(artifact_json))

    # Layer 2 (re-run here so the policeman owns the unified report)
    unverified = validate_prose(
        artifact_json=artifact_json,
        rendered_prose=rendered_prose,
    )
    for u in unverified:
        issues.append(
            Issue(
                severity="fail",
                category="fabrication",
                where=u.section,
                what=f"Number {u.value!r} appears in prose but does not trace to the artifact (excerpt: '{u.excerpt}').",
                fix="Use only numbers present in the artifact, or rephrase to drop the figure.",
            )
        )

    opus_raw: Optional[str] = None
    if use_opus_critique and client is not None:
        try:
            opus_raw, opus_issues = _run_opus_critique(
                client=client,
                artifact_json=artifact_json,
                rendered_prose=rendered_prose,
            )
            issues.extend(opus_issues)
        except Exception as exc:
            # Opus critique is best-effort — its absence shouldn't block
            # the deterministic layers. Log but continue.
            log.warning("Opus critique failed: %s", exc)
            issues.append(
                Issue(
                    severity="warn",
                    category="voice",
                    where="(policeman)",
                    what=f"Opus critique step did not complete: {exc!s}",
                    fix="Audit will rely on deterministic layers only this run.",
                )
            )

    verdict = _verdict_from_issues(issues)
    return PolicemanReport(
        verdict=verdict,
        issues=issues,
        unverified_numbers=unverified,
        opus_raw=opus_raw,
    )


# ============================================================
# Deterministic checks
# ============================================================

def _check_denylist(rendered_prose: dict[str, str]) -> list[Issue]:
    """Walk every section's prose and flag any denylisted phrase.

    Pre-mask known soil-test method labels (`pH (KCl)`, `pH (H2O)`)
    before scanning. The bare token `KCl` is a denylisted raw fertilizer
    (potassium chloride), but inside `pH (KCl)` it's the analytical
    method specifier — agronomically legitimate in narrative prose.
    Without the mask, every Opus paragraph that quotes a soil pH reading
    by method gets a false-positive disclosure failure. Same workaround
    we apply on the PDF-renderer leak test.
    """
    method_label_masks = {
        "pH (KCl)": "pH(method-K)",
        "pH (H2O)": "pH(method-H)",
    }
    issues: list[Issue] = []
    for section, raw_prose in rendered_prose.items():
        if not raw_prose:
            continue
        prose = raw_prose
        for label, mask in method_label_masks.items():
            prose = prose.replace(label, mask)
        for term, category in _denylist_with_categories():
            for match in _whole_word_finditer(term, prose):
                start = max(0, match.start() - 25)
                end = min(len(prose), match.end() + 25)
                excerpt = prose[start:end].replace("\n", " ").strip()
                issues.append(
                    Issue(
                        severity="fail",
                        category="disclosure",
                        where=section,
                        what=f"Disclosure-boundary breach — '{term}' is a {category} and may not appear in client-mode output (excerpt: '{excerpt}').",
                        fix=f"Replace the reference to '{term}' with a nutrient-analysis or commercial-blend label.",
                    )
                )
        for match in _SECTION_NUMBER_RX.finditer(prose):
            start = max(0, match.start() - 25)
            end = min(len(prose), match.end() + 25)
            excerpt = prose[start:end].replace("\n", " ").strip()
            issues.append(
                Issue(
                    severity="fail",
                    category="disclosure",
                    where=section,
                    what=f"Source-citation pattern '{match.group(0)}' (handbook section number) leaked into prose (excerpt: '{excerpt}').",
                    fix="Strip the citation; keep the agronomic statement only.",
                )
            )
    return issues


def _denylist_with_categories() -> list[tuple[str, str]]:
    return (
        [(t, "raw material") for t in _RAW_MATERIAL_TERMS]
        + [(t, "factory / QC / SOP term") for t in _FACTORY_TERMS]
        + [(t, "source citation") for t in _SOURCE_CITATION_TERMS]
    )


def _whole_word_finditer(term: str, text: str):
    """Whole-word match. Acronym-style raw materials are case-sensitive
    (so "CAN" does not match the English word "can", "MAP" does not match
    "map", "SOP" does not match "sop"); full multi-word names stay
    case-insensitive ("calcium nitrate" still hits "Calcium Nitrate").

    Heuristic: if the term has no spaces AND is ≤ 5 characters AND
    contains no lowercase letters except the trailing-l in mixed-case
    chemistry shorthand (`KCl`), match case-sensitively. Anything else
    is case-insensitive.
    """
    is_acronym = (
        " " not in term
        and len(term) <= 5
        and not re.search(r"[a-z]", term.replace("Cl", ""))  # tolerate Cl, NO3 tail
    )
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
    flags = 0 if is_acronym else re.IGNORECASE
    return re.finditer(pattern, text, flags=flags)


def _check_rate_caps(artifact_json: dict[str, Any]) -> list[Issue]:
    """Cap-check the engine's foliar rates against agronomic upper
    bounds. The policeman doesn't override the engine — it raises a
    FAIL if the engine ever produced a phytotoxic rate, on the
    assumption that this means an upstream regression we want to catch
    before the document leaves the system.
    """
    issues: list[Issue] = []
    foliar_events = artifact_json.get("foliar_events") or []
    for ev in foliar_events:
        nutrients = ev.get("nutrients") or {}
        rate = float(ev.get("rate_l_per_ha") or ev.get("rate_kg_per_ha") or 0.0)
        # Foliar nutrient kg/ha is rate * %nutrient (approximate; engine
        # carries the precise number when it computes the spray).
        # Accept either an explicit 'kg_per_ha' breakdown or fall back
        # to rate × concentration if engine carried that shape.
        b_kg = _nutrient_kg(nutrients, "B", rate) or float(ev.get("b_kg_per_ha") or 0.0)
        zn_kg = _nutrient_kg(nutrients, "Zn", rate) or float(ev.get("zn_kg_per_ha") or 0.0)
        if b_kg > 1.5:
            issues.append(
                Issue(
                    severity="fail",
                    category="agronomy",
                    where=f"foliar:{ev.get('id') or ev.get('stage') or '?'}",
                    what=f"Foliar boron {b_kg:.2f} kg B/ha exceeds the 1.5 kg/ha phytotoxicity cap.",
                    fix="Split the application or reduce concentration.",
                )
            )
        if zn_kg > 5.0:
            issues.append(
                Issue(
                    severity="fail",
                    category="agronomy",
                    where=f"foliar:{ev.get('id') or ev.get('stage') or '?'}",
                    what=f"Foliar zinc {zn_kg:.2f} kg Zn/ha exceeds the 5 kg/ha phytotoxicity cap.",
                    fix="Split the application or reduce concentration.",
                )
            )
    return issues


def _nutrient_kg(nutrients: dict, key: str, rate: float) -> float:
    """Best-effort kg/ha extraction. Returns 0.0 when the data shape
    doesn't give us enough to compute — caller falls back to explicit
    fields on the event."""
    if not isinstance(nutrients, dict):
        return 0.0
    raw = nutrients.get(key)
    if raw is None:
        return 0.0
    try:
        return float(raw) * rate / 100.0
    except (TypeError, ValueError):
        return 0.0


# ============================================================
# Opus critique
# ============================================================

def _run_opus_critique(
    *,
    client: NarrativeClient,
    artifact_json: dict[str, Any],
    rendered_prose: dict[str, str],
) -> tuple[str, list[Issue]]:
    """Run the policeman LLM call. Returns (raw_text, parsed issues).

    The system prompt instructs Opus to return JSON; we tolerate stray
    whitespace / a leading explainer and pull the first balanced JSON
    object we find. If parsing fails entirely we surface that as a
    WARN — the deterministic layers still stand.
    """
    summary = _summarise_artifact_for_audit(artifact_json)
    user = policeman_user_msg(
        artifact_summary=summary,
        rendered_prose=rendered_prose,
    )
    result = client.complete(
        system_prompt=POLICEMAN_SYSTEM,
        user_message=user,
        max_tokens=2048,
        cache_system=True,
    )
    parsed = _parse_policeman_json(result.text)
    if parsed is None:
        return result.text, [
            Issue(
                severity="warn",
                category="voice",
                where="(policeman)",
                what="Opus critique returned non-JSON output; deterministic layers stand.",
                fix="Investigate prompt drift if this happens repeatedly.",
            )
        ]
    issues: list[Issue] = []
    for raw in parsed.get("issues") or []:
        try:
            issues.append(
                Issue(
                    severity=str(raw.get("severity", "warn")).lower(),
                    category=str(raw.get("category", "voice")),
                    where=str(raw.get("where", "")),
                    what=str(raw.get("what", "")),
                    fix=str(raw.get("fix", "")),
                )
            )
        except Exception:
            continue
    return result.text, issues


def _parse_policeman_json(text: str) -> Optional[dict]:
    if not text:
        return None
    # Strip markdown fences if Opus added them despite instructions.
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    # Find the first {...} block.
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None


def _summarise_artifact_for_audit(artifact_json: dict[str, Any]) -> dict[str, Any]:
    """Trim the artifact to the fields the policeman needs. The full
    artifact is large and pushes us into avoidable token cost; the
    policeman audits prose against engine ground truth, so it only
    needs the engine ground truth that prose can reference."""
    return {
        "header": artifact_json.get("header"),
        "soil_snapshots": [
            {
                "block_name": s.get("block_name"),
                "block_area_ha": s.get("block_area_ha"),
                "headline_signals": s.get("headline_signals"),
                "factor_findings": s.get("factor_findings"),
            }
            for s in (artifact_json.get("soil_snapshots") or [])
        ],
        "pre_season_recommendations": artifact_json.get("pre_season_recommendations"),
        "blends": [
            {
                "stage_name": b.get("stage_name"),
                "method": (b.get("method") or {}).get("kind"),
                "rate_per_ha_kg": b.get("rate_per_ha_kg"),
                "nutrients_delivered": b.get("nutrients_delivered"),
            }
            for b in (artifact_json.get("blends") or [])
        ],
        "foliar_events": artifact_json.get("foliar_events"),
        "risk_flags": artifact_json.get("risk_flags"),
    }


def _verdict_from_issues(issues: list[Issue]) -> Verdict:
    worst: Verdict = "PASS"
    for issue in issues:
        if issue.severity == "fail":
            return "FAIL"
        if issue.severity == "warn" and _VERDICT_RANK[worst] < _VERDICT_RANK["WARN"]:
            worst = "WARN"
    return worst
