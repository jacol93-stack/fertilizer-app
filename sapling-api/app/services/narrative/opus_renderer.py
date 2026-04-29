"""Per-section Opus prose generator.

Public surface: `enhance_artifact_prose(artifact, *, baseline, mode)`.

`baseline` is the deterministic-engine prose dict the renderer would
otherwise have used. We use it as tone-reference few-shot AND as the
fallback when any layer FAILs.

What we generate (Phase C scope):
  - background_intro       → single paragraph
  - soil_intro             → single paragraph
  - walkthrough_intro      → single paragraph
  - year_outlook_cards     → list of {label, title, bullets}

Per-blend `walkthrough_brief` is intentionally OUT of v1 — would be
N calls per render (often 15+ blends), so we keep them deterministic
for now and revisit once the v1 pipeline has flown a few real renders.

Wiring:
  - Caller (pdf_renderer.render_programme_pdf) sets `narrative_mode`.
  - When "deterministic" → we never run.
  - When "opus" → we run, three-layer audit, then either the prose or
    the engine baseline is used. Verdict + telemetry returned for
    persistence and admin review.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from app.models import ProgrammeArtifact

from app.services.narrative.anthropic_client import (
    CompletionResult,
    NarrativeClient,
)
from app.services.narrative.fact_validator import to_jsonable
from app.services.narrative.policeman import PolicemanReport, audit
from app.services.narrative.prompts import (
    SYSTEM_PROMPT,
    background_intro_user_msg,
    soil_intro_user_msg,
    soil_report_holistic_user_msg,
    soil_report_summary_user_msg,
    year_outlook_user_msg,
)

log = logging.getLogger(__name__)


# ============================================================
# Result envelope
# ============================================================

@dataclass
class NarrativeResult:
    # The section keys here mirror what `pdf_renderer._build_context`
    # consumes. When a key is present, the renderer should use it
    # in place of the deterministic prose. When absent (or the result
    # is empty), the renderer keeps its baseline.
    overrides: dict[str, Any] = field(default_factory=dict)

    # Raw prose Opus produced, kept even on FAIL so the UI can show the
    # user what was generated and why it was rejected. The renderer
    # never reads this — `overrides` is the only authoritative source
    # of prose for rendering. `raw_prose` is purely for audit / UI
    # display.
    raw_prose: dict[str, Any] = field(default_factory=dict)

    # Audit trail.
    verdict: str = "PASS"
    issues: list[dict[str, Any]] = field(default_factory=list)

    # Cost telemetry — sum across every section call.
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    duration_seconds: float = 0.0
    section_count: int = 0

    @property
    def used_opus_prose(self) -> bool:
        return bool(self.overrides) and self.verdict != "FAIL"


# ============================================================
# Public entry point
# ============================================================

def enhance_artifact_prose(
    artifact: ProgrammeArtifact,
    *,
    baseline: dict[str, Any],
    mode: str = "client",
    client: Optional[NarrativeClient] = None,
) -> NarrativeResult:
    """Run the Opus pipeline. Always returns — never raises (except on
    config errors like a missing API key, which the caller should
    handle by falling back to deterministic).

    `baseline` carries the engine's deterministic prose for tone
    reference + fallback. Expected keys:
      - 'background_intro' : str
      - 'glance_facts'     : list[str]
      - 'soil_intro'       : str
      - 'walkthrough_intro': str
      - 'year_outlook_cards': list[{label, title, bullets}]
    """
    if mode != "client":
        raise NotImplementedError(
            "Operator-mode Opus rendering is Phase E scope (admin-triggered, "
            "fertigation-only). Not yet implemented."
        )

    started = time.monotonic()
    result = NarrativeResult()
    if client is None:
        try:
            client = NarrativeClient()
        except RuntimeError as exc:
            log.warning("Skipping Opus narrative: %s", exc)
            result.verdict = "FAIL"
            result.issues.append(
                {
                    "severity": "fail",
                    "category": "config",
                    "where": "(narrative)",
                    "what": str(exc),
                    "fix": "Set ANTHROPIC_API_KEY or run in deterministic mode.",
                }
            )
            return result

    artifact_json = to_jsonable(artifact)
    soil_summary = _soil_summary_for_prompt(artifact_json)
    header_for_prompt = _header_for_prompt(artifact_json)

    # ----- Run each section call. We keep these sequential rather than
    # parallel because the prompt cache is most useful when calls hit
    # the same client in series — first call writes the cache, every
    # subsequent call reads it. Parallel calls all miss the cache.

    rendered: dict[str, str] = {}
    parsed_overrides: dict[str, Any] = {}

    sections = _section_specs(
        artifact_json=artifact_json,
        baseline=baseline,
        header=header_for_prompt,
        soil_summary=soil_summary,
    )

    for spec in sections:
        try:
            completion = client.complete(
                system_prompt=SYSTEM_PROMPT,
                user_message=spec["user_message"],
                max_tokens=spec.get("max_tokens", 1024),
                cache_system=True,
            )
        except Exception as exc:
            log.warning("Opus section %s failed: %s", spec["id"], exc)
            result.issues.append(
                {
                    "severity": "fail",
                    "category": "api",
                    "where": spec["id"],
                    "what": f"Opus call failed: {exc!s}",
                    "fix": "Section will fall back to engine baseline.",
                }
            )
            continue
        result.section_count += 1
        result.input_tokens += completion.input_tokens
        result.output_tokens += completion.output_tokens
        result.cache_read_tokens += completion.cache_read_tokens
        result.cache_write_tokens += completion.cache_write_tokens

        post = spec.get("postprocess") or _passthrough
        try:
            value = post(completion.text)
        except Exception as exc:
            log.warning(
                "Opus section %s postprocess failed: %s", spec["id"], exc,
            )
            result.issues.append(
                {
                    "severity": "fail",
                    "category": "parse",
                    "where": spec["id"],
                    "what": f"Postprocess failed: {exc!s}",
                    "fix": "Section will fall back to engine baseline.",
                }
            )
            continue

        if value is None:
            continue

        parsed_overrides[spec["id"]] = value
        rendered[spec["id"]] = _flatten_for_audit(value)

    # ----- Three-layer audit. Layer 2 (fact validator) is run inside
    # `audit()` so we get one unified report.
    report: PolicemanReport = audit(
        artifact_json=artifact_json,
        rendered_prose=rendered,
        client=client,
        use_opus_critique=True,
    )

    result.verdict = report.verdict
    result.issues.extend(_issue_dicts(report))

    # `raw_prose` always holds whatever Opus produced — the wizard's
    # narrative review panel surfaces this so the user can compare
    # against engine baseline and decide regenerate vs accept-anyway.
    result.raw_prose = dict(parsed_overrides)

    if report.verdict == "FAIL":
        # Throw away the Opus prose for *rendering* — the renderer
        # keeps its deterministic baseline. We DO keep the verdict +
        # issues + raw prose for admin review.
        result.overrides = {}
    else:
        result.overrides = parsed_overrides

    result.duration_seconds = time.monotonic() - started
    return result


# ============================================================
# Soil Report — separate entry point with its own section specs
# ============================================================


def enhance_soil_report_prose(
    soil_report_payload: dict[str, Any],
    *,
    client: Optional[NarrativeClient] = None,
) -> NarrativeResult:
    """Run the Opus pipeline against a soil-report artifact.

    Different sections from a programme — a soil report has no schedule
    or blend logic, only analysis interpretation. We generate:
      - executive_summary (Section 01 lead paragraph)
      - holistic_intro (Section 04 lead, only when holistic_signals present)

    Same three-layer audit (engine + fact validator + policeman) as
    programmes. On FAIL the renderer falls back to deterministic baseline.
    """
    started = time.monotonic()
    result = NarrativeResult()
    if client is None:
        try:
            client = NarrativeClient()
        except RuntimeError as exc:
            log.warning("Skipping Opus soil-report narrative: %s", exc)
            result.verdict = "FAIL"
            result.issues.append({
                "severity": "fail",
                "category": "config",
                "where": "(narrative)",
                "what": str(exc),
                "fix": "Set ANTHROPIC_API_KEY or skip narrative.",
            })
            return result

    header = soil_report_payload.get("header") or {}
    soil_summary = _soil_summary_for_soil_report(soil_report_payload)
    headline_signals = list(soil_report_payload.get("headline_signals") or [])
    holistic_signals = list(soil_report_payload.get("holistic_signals") or [])
    trend_summary = _trend_summary_for_prompt(soil_report_payload)

    sections: list[dict[str, Any]] = []

    # Always run the executive summary
    sections.append({
        "id": "executive_summary",
        "user_message": soil_report_summary_user_msg(
            header={
                "title": header.get("title"),
                "scope_kind": header.get("scope_kind"),
                "client_name": header.get("client_name"),
                "farm_name": header.get("farm_name"),
                "block_count": header.get("block_count"),
                "analysis_count": header.get("analysis_count"),
                "earliest_sample_date": header.get("earliest_sample_date"),
                "latest_sample_date": header.get("latest_sample_date"),
            },
            headline_signals=headline_signals,
            soil_summary=soil_summary,
            holistic_signals=holistic_signals,
            trend_summary=trend_summary,
            baseline="",  # caller will replace deterministic intro
        ),
        "max_tokens": 800,
        "postprocess": _strip_quotes,
    })

    # Holistic intro only when there are cross-block signals
    if holistic_signals:
        sections.append({
            "id": "holistic_intro",
            "user_message": soil_report_holistic_user_msg(
                header={
                    "title": header.get("title"),
                    "scope_kind": header.get("scope_kind"),
                    "block_count": header.get("block_count"),
                },
                holistic_signals=holistic_signals,
                soil_summary=soil_summary,
                baseline="",
            ),
            "max_tokens": 600,
            "postprocess": _strip_quotes,
        })

    rendered: dict[str, str] = {}
    parsed_overrides: dict[str, Any] = {}

    for spec in sections:
        try:
            completion = client.complete(
                system_prompt=SYSTEM_PROMPT,
                user_message=spec["user_message"],
                max_tokens=spec.get("max_tokens", 1024),
                cache_system=True,
            )
        except Exception as exc:
            log.warning("Opus soil-report section %s failed: %s", spec["id"], exc)
            result.issues.append({
                "severity": "fail",
                "category": "api",
                "where": spec["id"],
                "what": f"Opus call failed: {exc!s}",
                "fix": "Section will fall back to engine baseline.",
            })
            continue
        result.section_count += 1
        result.input_tokens += completion.input_tokens
        result.output_tokens += completion.output_tokens
        result.cache_read_tokens += completion.cache_read_tokens
        result.cache_write_tokens += completion.cache_write_tokens

        post = spec.get("postprocess") or _passthrough
        try:
            value = post(completion.text)
        except Exception as exc:
            log.warning(
                "Opus soil-report section %s postprocess failed: %s", spec["id"], exc,
            )
            result.issues.append({
                "severity": "fail",
                "category": "parse",
                "where": spec["id"],
                "what": f"Postprocess failed: {exc!s}",
                "fix": "Section will fall back to engine baseline.",
            })
            continue
        if value is None:
            continue
        parsed_overrides[spec["id"]] = value
        rendered[spec["id"]] = _flatten_for_audit(value)

    # Audit pass — deterministic layers (denylist + fact_validator)
    # still run. The Opus-critique layer is OFF for soil reports until
    # its prompt is tuned for the soil-report payload shape: it currently
    # interprets the unfamiliar JSON keys (trend_reports, soil_snapshots
    # vs programme's blends/risk_flags) as "no data for these claims"
    # and over-flags genuine prose as fabrication. The deterministic
    # numeric extractor still catches every fabricated number against
    # the recursive walk of the payload, and the denylist still catches
    # raw-material / disclosure leaks. Reinstate the critique pass once
    # the policeman prompt is updated to recognise the soil-report shape.
    report: PolicemanReport = audit(
        artifact_json=soil_report_payload,
        rendered_prose=rendered,
        client=client,
        use_opus_critique=False,
    )

    result.verdict = report.verdict
    result.issues.extend(_issue_dicts(report))
    result.raw_prose = dict(parsed_overrides)
    if report.verdict == "FAIL":
        result.overrides = {}
    else:
        result.overrides = parsed_overrides
    result.duration_seconds = time.monotonic() - started
    return result


def _soil_summary_for_soil_report(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Pluck per-block factor findings + headline signals into the
    compact shape the prompt builder expects."""
    out: list[dict[str, Any]] = []
    for s in payload.get("soil_snapshots") or []:
        block_id = s.get("block_id") or ""
        if isinstance(block_id, str) and block_id.startswith("cluster_"):
            continue
        findings_summary: list[str] = []
        for f in (s.get("factor_findings") or []):
            label = f.get("parameter") or ""
            severity = f.get("severity") or ""
            if label:
                findings_summary.append(f"{label} ({severity})")
        out.append({
            "block_name": s.get("block_name"),
            "block_area_ha": s.get("block_area_ha"),
            "headline_signals": s.get("headline_signals"),
            "factor_summary": findings_summary,
        })
    return out


def _trend_summary_for_prompt(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Compact representation of trend reports for the Opus prompt."""
    out: list[dict[str, Any]] = []
    for t in payload.get("trend_reports") or []:
        # Pull only the major-significance parameters — minor ones add
        # noise to the prompt for marginal value.
        params: list[dict[str, Any]] = []
        for p in (t.get("parameters") or []):
            if p.get("significance") not in ("major", "minor"):
                continue
            params.append({
                "parameter": p.get("parameter"),
                "earliest_value": p.get("earliest_value"),
                "latest_value": p.get("latest_value"),
                "direction": p.get("direction"),
                "significance": p.get("significance"),
            })
        out.append({
            "block_name": t.get("block_name"),
            "n_analyses": t.get("n_analyses"),
            "span_days": t.get("span_days"),
            "headline_signals": t.get("headline_signals"),
            "parameters": params,
        })
    return out


# ============================================================
# Section specs — one entry per Opus call
# ============================================================

def _section_specs(
    *,
    artifact_json: dict[str, Any],
    baseline: dict[str, Any],
    header: dict,
    soil_summary: list[dict],
) -> list[dict[str, Any]]:
    is_mature = bool(baseline.get("is_mature"))
    specs: list[dict[str, Any]] = []

    specs.append(
        {
            "id": "background_intro",
            "user_message": background_intro_user_msg(
                header=header,
                glance_facts=baseline.get("glance_facts") or [],
                baseline=baseline.get("background_intro") or "",
            ),
            "max_tokens": 600,
            "postprocess": _strip_quotes,
        }
    )

    if soil_summary:
        specs.append(
            {
                "id": "soil_intro",
                "user_message": soil_intro_user_msg(
                    header=header,
                    soil_summary=soil_summary,
                    baseline=baseline.get("soil_intro") or "",
                ),
                "max_tokens": 700,
                "postprocess": _strip_quotes,
            }
        )

    walkthrough_baseline = baseline.get("walkthrough_intro")
    if walkthrough_baseline:
        # The walkthrough intro is a one-paragraph framing of the
        # season's application work. Reuse the background-intro shape;
        # it's the same narrative footprint.
        from app.services.narrative.prompts import _json as _to_json
        msg = (
            "SECTION: walkthrough_intro\n\n"
            "This is the lead paragraph of the Application Walkthrough "
            "section. It precedes the per-group calendar of applications. "
            "Frame what the season's application work looks like in plain "
            "language. 50–90 words.\n\n"
            "ARTIFACT FACTS:\n"
            f"{_to_json({'header': header, 'soil_summary': soil_summary})}\n\n"
            "ENGINE BASELINE (for tone reference — do not copy):\n"
            f"{walkthrough_baseline}\n\n"
            "Write the walkthrough intro paragraph now."
        )
        specs.append(
            {
                "id": "walkthrough_intro",
                "user_message": msg,
                "max_tokens": 600,
                "postprocess": _strip_quotes,
            }
        )

    year_outlook_baseline = baseline.get("year_outlook_cards") or []
    if year_outlook_baseline:
        specs.append(
            {
                "id": "year_outlook_cards",
                "user_message": year_outlook_user_msg(
                    header=header,
                    is_mature=is_mature,
                    soil_summary=soil_summary,
                    baseline=year_outlook_baseline,
                ),
                "max_tokens": 1500,
                "postprocess": _parse_year_outlook,
            }
        )

    return specs


# ============================================================
# Postprocessing
# ============================================================

def _passthrough(text: str) -> Any:
    return text.strip()


def _strip_quotes(text: str) -> str:
    """Opus sometimes wraps the paragraph in quote characters. Strip
    matched outer quotes plus any "Background:" / "Here is the …"
    preamble line if present."""
    if not text:
        return ""
    stripped = text.strip()
    # Drop a single leading "Section X:" / "Here is …" line.
    lines = stripped.splitlines()
    if lines and re.match(
        r"^(here(\s+is)?|section|background|soil|walkthrough)\b",
        lines[0],
        re.IGNORECASE,
    ):
        # Only drop if the first line looks like a label/header
        # (short, no period in the middle of a sentence).
        if len(lines[0].strip()) < 60 and ":" in lines[0]:
            stripped = "\n".join(lines[1:]).strip()
    if stripped.startswith(("\"", "'", "“", "‘")) and stripped.endswith(
        ("\"", "'", "”", "’")
    ):
        stripped = stripped[1:-1].strip()
    return stripped


def _parse_year_outlook(text: str) -> Optional[list[dict[str, Any]]]:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        payload = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    cards = payload.get("cards") or []
    out: list[dict[str, Any]] = []
    for c in cards:
        if not isinstance(c, dict):
            continue
        label = str(c.get("label", "")).strip()
        title = str(c.get("title", "")).strip()
        bullets_raw = c.get("bullets") or []
        bullets = [str(b).strip() for b in bullets_raw if str(b).strip()]
        if not (label and title and bullets):
            continue
        out.append({"label": label, "title": title, "bullets": bullets})
    return out or None


# ============================================================
# Audit-friendly flatten + summary builders
# ============================================================

def _flatten_for_audit(value: Any) -> str:
    """Reduce a section value to a single string the audit layer can
    grep through. Strings stay strings; the year_outlook list of cards
    flattens into label/title/bullets lines."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        out: list[str] = []
        for c in value:
            if isinstance(c, dict):
                out.append(c.get("label", ""))
                out.append(c.get("title", ""))
                out.extend(c.get("bullets") or [])
        return "\n".join(out)
    return json.dumps(value, default=str)


def _soil_summary_for_prompt(artifact_json: dict[str, Any]) -> list[dict]:
    out: list[dict] = []
    for s in artifact_json.get("soil_snapshots") or []:
        block_id = s.get("block_id") or ""
        if isinstance(block_id, str) and block_id.startswith("cluster_"):
            continue
        findings_summary: list[str] = []
        for f in (s.get("factor_findings") or []):
            label = f.get("ratio") or f.get("factor") or ""
            severity = f.get("severity") or ""
            value = f.get("value")
            if label:
                if value is not None:
                    findings_summary.append(f"{label}={value} ({severity})")
                else:
                    findings_summary.append(f"{label} ({severity})")
        out.append(
            {
                "block_name": s.get("block_name"),
                "block_area_ha": s.get("block_area_ha"),
                "headline_signals": s.get("headline_signals"),
                "factor_summary": findings_summary,
            }
        )
    return out


def _header_for_prompt(artifact_json: dict[str, Any]) -> dict:
    h = artifact_json.get("header") or {}
    return {
        "client_name": h.get("client_name"),
        "farm_name": h.get("farm_name"),
        "location": h.get("location"),
        "crop": h.get("crop"),
        "season": h.get("season"),
    }


def _issue_dicts(report: PolicemanReport) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for issue in report.issues:
        out.append(
            {
                "severity": issue.severity,
                "category": issue.category,
                "where": issue.where,
                "what": issue.what,
                "fix": issue.fix,
            }
        )
    return out
