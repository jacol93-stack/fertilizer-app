"""
PDF renderer — Sapling-branded styled PDF from a ProgrammeArtifact.

Pipeline:
    ProgrammeArtifact (engine output)
        ↓
    Map to template context (this module's `_build_context`)
        ↓
    Jinja2 renders programme.html
        ↓
    WeasyPrint (HTML+CSS) writes deterministic PDF bytes

Design system: see `assets/design_references/SAPLING_DESIGN_SYSTEM.md`.
Reference PDFs: `clivia_garlic_WJ60421.pdf` + `allicro_karoo_2026-27.pdf`.

Usage:
    from app.services.pdf_renderer import render_programme_pdf
    pdf_bytes = render_programme_pdf(artifact, mode="client")
    with open("programme.pdf", "wb") as f:
        f.write(pdf_bytes)

The renderer enforces the client-disclosure boundary (see memory:
feedback_client_disclosure_boundary): no source citations, no raw
material names, no factory procedures. The same `_strip_source_refs`
sanitiser used by the markdown renderer is applied to all prose
fields here.
"""
from __future__ import annotations

import os
import platform
import re
import sys
from datetime import date as date_type
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote as _url_quote

# WeasyPrint on macOS needs Homebrew's libgobject/pango/cairo/glib on the
# dyld lookup path. Setting this BEFORE importing weasyprint avoids the
# user having to export DYLD_FALLBACK_LIBRARY_PATH manually. No-op on
# Linux / production containers where the libs live in standard paths.
if platform.system() == "Darwin":
    _BREW_LIB = "/opt/homebrew/lib"
    if os.path.isdir(_BREW_LIB):
        existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        parts = [p for p in existing.split(":") if p]
        if _BREW_LIB not in parts:
            parts.append(_BREW_LIB)
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(parts)

import logging as _logging

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

# WeasyPrint logs spurious "Font-face 'X' cannot be loaded" warnings even
# when the fonts ARE successfully fetched + embedded (verified via
# pdffonts on the rendered output). Drop those noisy warnings; real
# missing-font issues still surface as PDF text rendering with system
# fallbacks (which we'd notice in visual regression).
_logging.getLogger("weasyprint").setLevel(_logging.ERROR)

from app.models import (
    ApplicationMethod,
    Blend,
    BlendPart,
    ProgrammeArtifact,
)
from app.services.renderer import _strip_source_refs


# ============================================================
# Paths + environment
# ============================================================

_TEMPLATE_DIR = Path(__file__).parent / "pdf_templates"
_ASSET_DIR = Path(__file__).parent.parent.parent / "assets"
_FONT_DIR = _ASSET_DIR / "fonts"
_REPO_ROOT = _ASSET_DIR.parent.parent

_jinja = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _nutrient_pretty(symbol: str) -> str:
    """User-facing nutrient label. SA growers read fertilizer ratios as
    N : P : K with the convention that P and K are oxide forms (P₂O₅,
    K₂O) — same numeric values, simpler labels. Engine internals keep
    `P2O5` / `K2O` as the canonical keys so the chemistry stays
    explicit; this filter is the display boundary.

    Other gas / molecule prefixes (NH4, NO3, SO4, CO2) keep their
    subscripts because they're chemical formulas, not nutrient labels.
    """
    if symbol == "P2O5":
        return "P"
    if symbol == "K2O":
        return "K"
    return (
        symbol
        .replace("CO2", "CO₂")
        .replace("NH4", "NH₄")
        .replace("NO3", "NO₃")
        .replace("SO4", "SO₄")
    )


_jinja.filters["nutrient_pretty"] = _nutrient_pretty


# ============================================================
# Public entry point
# ============================================================

def render_programme_pdf(
    artifact: ProgrammeArtifact,
    *,
    mode: str = "client",
    narrative_mode: str = "deterministic",
    narrative_report: Optional[dict[str, Any]] = None,
    narrative_overrides: Optional[dict[str, Any]] = None,
) -> bytes:
    """Render a ProgrammeArtifact as a styled Sapling-branded PDF.

    `mode="client"` (default) strips all source citations from prose
    per the disclosure-boundary rule. `mode="operator"` is reserved
    for Phase E (admin-triggered factory recipes).

    `narrative_mode`:
      * `"deterministic"` (default) — engine-generated prose only.
      * `"opus"` — runs the Opus narrative pipeline + AI policeman
        on top of the deterministic baseline. On FAIL, falls back to
        the engine baseline so the PDF always renders.

    `narrative_report` is an optional dict the caller can pass in to
    receive verdict + token telemetry (mutated in place). Persist it
    on the artifact metadata for admin review. Ignored when
    `narrative_mode="deterministic"`.

    `narrative_overrides` is an optional pre-rendered prose dict (from
    a previous `enhance_artifact_prose` run, persisted on the artifact).
    When supplied, the renderer applies it directly and skips the live
    Opus call regardless of `narrative_mode`. This is the production
    path: generate-narrative endpoint persists the prose; the PDF route
    reads it back and passes it here. PDF rendering stays cheap +
    deterministic — no live API calls during a download.

    Switching between modes is opt-in by design: the user manually
    triggers an Opus render to compare against the deterministic
    baseline. Defaults stay deterministic until the comparison gates
    pass.
    """
    if mode != "client":
        raise NotImplementedError(
            "Operator-mode PDF rendering is Phase E scope (admin-triggered, "
            "fertigation-only, factory recipes exposed). Not yet implemented."
        )

    context = _build_context(artifact)
    # Persisted-prose path takes precedence over a live Opus call —
    # PDFs render against locked narrative whenever one is available
    # so download latency stays low and prose is reproducible.
    if narrative_overrides:
        _apply_narrative_overrides(context, narrative_overrides)
    elif narrative_mode == "opus":
        # Lazy import — keeps the deterministic path zero-cost (no
        # Anthropic SDK warmup, no API key check) when narrative_mode
        # isn't requested.
        from app.services.narrative.opus_renderer import (
            enhance_artifact_prose,
        )
        baseline = _baseline_for_narrative(context, artifact)
        result = enhance_artifact_prose(
            artifact,
            baseline=baseline,
            mode="client",
        )
        _apply_narrative_overrides(context, result.overrides)
        if narrative_report is not None:
            narrative_report.update(
                {
                    "verdict": result.verdict,
                    "issues": result.issues,
                    "section_count": result.section_count,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cache_read_tokens": result.cache_read_tokens,
                    "cache_write_tokens": result.cache_write_tokens,
                    "duration_seconds": result.duration_seconds,
                    "used_opus_prose": result.used_opus_prose,
                }
            )
    elif narrative_mode != "deterministic":
        raise ValueError(
            f"Unknown narrative_mode={narrative_mode!r} — expected "
            "'deterministic' or 'opus'."
        )


    template = _jinja.get_template("programme.html")
    html_str = template.render(**context)
    # Substitute the asset-dir placeholder so <img src="file://..."> resolves.
    # Spaces + special chars in the path are percent-encoded so WeasyPrint's
    # URL fetcher doesn't choke (file URLs MUST be RFC-3986-encoded).
    html_str = html_str.replace(
        "__ASSET_DIR__",
        _url_quote(str(_ASSET_DIR.resolve()), safe="/"),
    )

    # Inline the CSS with the font directory substituted to absolute paths.
    # Same percent-encoding rule applies to the @font-face URLs.
    css_path = _TEMPLATE_DIR / "style.css"
    css_text = css_path.read_text(encoding="utf-8")
    css_text = css_text.replace(
        "__FONT_DIR__",
        _url_quote(str(_FONT_DIR.resolve()), safe="/"),
    )

    # WeasyPrint requires an explicit FontConfiguration object passed to
    # BOTH the CSS constructor and write_pdf for @font-face rules to
    # register and resolve cleanly. Without this, @font-face URLs are
    # silently dropped and the renderer falls back to system fonts —
    # which on Linux containers means non-Inter, breaking brand fidelity.
    font_config = FontConfiguration()
    css_obj = CSS(string=css_text, font_config=font_config)

    pdf_bytes = HTML(string=html_str, base_url=str(_TEMPLATE_DIR)).write_pdf(
        stylesheets=[css_obj],
        font_config=font_config,
    )
    return pdf_bytes


# ============================================================
# Soil Report PDF — separate entry point
# ============================================================
# Same Sapling branding (cover / contents / running header / soil
# table visuals) as the programme PDF — drives off soil_report.html
# which links to the same style.css. Different content shape:
#   1. Executive summary (Opus narrative, optional)
#   2. Per-block soil snapshots (range bars, ratios, headline signals)
#   3. Trends per block (only when ≥ 2 analyses)
#   4. Holistic across-farm summary (only when ≥ 2 blocks)


def render_soil_report_pdf(
    artifact_dict: dict[str, Any],
    *,
    narrative_overrides: Optional[dict[str, Any]] = None,
    ideal_ratios: Optional[list[dict[str, Any]]] = None,
) -> bytes:
    """Render a soil_reports.report_payload dict as a Sapling-branded PDF.

    Takes the dict shape produced by `soil_report_builder.build_soil_report`
    + `.to_dict()` (or fetched directly from the soil_reports table).

    `narrative_overrides` is the Opus-generated executive summary +
    optional intros. When supplied, replaces the deterministic baselines
    in the rendered prose. Same shape as the programme renderer's
    overrides dict — keyed by section id.
    """
    context = _build_soil_report_context(artifact_dict, ideal_ratios=ideal_ratios)
    if narrative_overrides:
        _apply_soil_report_overrides(context, narrative_overrides)

    template = _jinja.get_template("soil_report.html")
    html_str = template.render(**context)
    html_str = html_str.replace(
        "__ASSET_DIR__",
        _url_quote(str(_ASSET_DIR.resolve()), safe="/"),
    )

    css_path = _TEMPLATE_DIR / "style.css"
    css_text = css_path.read_text(encoding="utf-8")
    css_text = css_text.replace(
        "__FONT_DIR__",
        _url_quote(str(_FONT_DIR.resolve()), safe="/"),
    )
    font_config = FontConfiguration()
    css_obj = CSS(string=css_text, font_config=font_config)
    pdf_bytes = HTML(string=html_str, base_url=str(_TEMPLATE_DIR)).write_pdf(
        stylesheets=[css_obj],
        font_config=font_config,
    )
    return pdf_bytes


def _build_soil_report_context(
    artifact: dict[str, Any],
    *,
    ideal_ratios: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Adapt a SoilReportArtifact dict into the Jinja context shape the
    soil_report.html template consumes. Reuses the programme renderer's
    soil-block view builder so the visuals are pixel-identical.

    `ideal_ratios` carries the cation-balance + cation-ratio target bands
    so the per-block view can render the saturation / ratio tables that
    the deterministic-only first pass left out. Loaded by the calling
    route from `ideal_ratios` (small reference table, fresh per render
    is cheap). Falls back to the hardcoded SA-norms when omitted so
    rendering never depends on DB availability.
    """
    ideal_ratios_list = ideal_ratios if ideal_ratios is not None else _FALLBACK_IDEAL_RATIOS
    header = artifact.get("header") or {}
    scope_kind = header.get("scope_kind") or "single_block"
    scope_label = {
        "single_block": "Single block snapshot",
        "block_with_history": "Block with history",
        "multi_block": "Multi-block snapshot",
    }.get(scope_kind, "Soil report")

    earliest = header.get("earliest_sample_date")
    latest = header.get("latest_sample_date")
    span_phrase = ""
    if earliest and latest and earliest != latest:
        try:
            from datetime import date as _date
            d1 = _date.fromisoformat(earliest) if isinstance(earliest, str) else earliest
            d2 = _date.fromisoformat(latest) if isinstance(latest, str) else latest
            months = max(1, (d2 - d1).days // 30)
            span_phrase = f"{months} month{'s' if months != 1 else ''}"
        except Exception:
            span_phrase = ""

    generated_on = header.get("generated_on")
    generated_on_formatted = ""
    if generated_on:
        try:
            from datetime import date as _date
            d = _date.fromisoformat(generated_on) if isinstance(generated_on, str) else generated_on
            generated_on_formatted = d.strftime("%-d %B %Y")
        except Exception:
            generated_on_formatted = str(generated_on)

    cover_subhead = ""
    if header.get("client_name") and header.get("farm_name"):
        cover_subhead = f"{header['farm_name']} · {header['client_name']}"
    elif header.get("client_name"):
        cover_subhead = header["client_name"]

    # Per-block soil snapshots — convert the JSON shape back into the
    # view shape the template expects. Reuse the programme renderer's
    # snapshot view builder so range bars, ratio rows, and headline
    # signals render identically.
    snapshot_views: list[dict[str, Any]] = []
    for snap in artifact.get("soil_snapshots") or []:
        view = _build_snapshot_view_from_dict(snap, ideal_ratios=ideal_ratios_list)
        if view:
            snapshot_views.append(view)

    # Trend reports — flatten into template-friendly view dicts
    trend_views: list[dict[str, Any]] = []
    for trend in artifact.get("trend_reports") or []:
        view = _build_trend_view(trend)
        if view:
            trend_views.append(view)

    holistic_signals = list(artifact.get("holistic_signals") or [])
    headline_signals = list(artifact.get("headline_signals") or [])

    # Default deterministic prose — Opus overrides replace these when
    # `narrative_overrides` is supplied to the renderer entry point.
    executive_intro = _default_executive_intro(scope_kind, header, headline_signals)
    blocks_intro = (
        f"{header.get('block_count', 0)} block"
        f"{'s' if header.get('block_count', 0) != 1 else ''} reviewed against the "
        f"crop's nutrient requirements + ratio targets. Range bars show where each "
        f"reading sits inside its optimal band."
    )
    trends_intro = (
        "How each parameter has moved across the analyses on file. Direction is "
        "judged against the optimal band; significance reflects both relative change "
        "and consistency across the timeline."
    )
    holistic_intro = (
        "Patterns the engine sees across all blocks — the farm-wide read on what "
        "moves the needle for everyone vs. block-by-block calls."
    )

    contents_entries = _build_soil_report_contents(
        has_blocks=bool(snapshot_views),
        has_trends=bool(trend_views),
        has_holistic=bool(holistic_signals),
    )

    return {
        "header": {
            "title": header.get("title") or "Soil Report",
            "scope_kind": scope_kind,
            "scope_label": scope_label,
            "client_name": header.get("client_name"),
            "farm_name": header.get("farm_name"),
            "generated_on_formatted": generated_on_formatted,
            "block_count": header.get("block_count", 0),
            "analysis_count": header.get("analysis_count", 0),
            "span_phrase": span_phrase,
        },
        "cover_subhead": cover_subhead,
        "contents_entries": contents_entries,
        "executive_intro": executive_intro,
        "blocks_intro": blocks_intro,
        "trends_intro": trends_intro,
        "holistic_intro": holistic_intro,
        "headline_signals": headline_signals,
        "soil_snapshots": snapshot_views,
        "trend_blocks": trend_views,
        "holistic_signals": holistic_signals,
    }


def _default_executive_intro(
    scope_kind: str,
    header: dict[str, Any],
    headline_signals: list[str],
) -> str:
    """Engine-baseline executive summary. Replaced by Opus when
    narrative_overrides['soil_report_summary'] is set."""
    bc = header.get("block_count", 0)
    ac = header.get("analysis_count", 0)
    if scope_kind == "single_block":
        return (
            f"Single block soil snapshot reviewed against the crop's nutrient "
            f"requirements. The detail sections below cover individual nutrient "
            f"status, cation balance, and any standout signals from the analysis."
        )
    if scope_kind == "block_with_history":
        return (
            f"Trend report covering {ac} analyses on one block. Each parameter is "
            f"compared across the timeline to surface what's moving — improving "
            f"into the optimal band, drifting out of it, or stable."
        )
    return (
        f"Multi-block soil report — {bc} blocks across "
        f"{ac} analyses. Each block carries its own snapshot below; the cross-"
        f"farm summary at the end pulls out patterns the engine sees across the "
        f"whole set."
    )


def _build_soil_report_contents(
    *,
    has_blocks: bool,
    has_trends: bool,
    has_holistic: bool,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = [
        {"title": "Executive summary", "anchor": "section-summary"},
    ]
    if has_blocks:
        entries.append({"title": "Per-block soil detail", "anchor": "section-blocks"})
    if has_trends:
        entries.append({"title": "Trends over time", "anchor": "section-trends"})
    if has_holistic:
        entries.append({"title": "Across the farm", "anchor": "section-holistic"})
    return entries


def _build_snapshot_view_from_dict(
    snap: dict[str, Any],
    *,
    ideal_ratios: Optional[list[dict[str, Any]]] = None,
) -> Optional[dict[str, Any]]:
    """Convert one persisted SoilSnapshot dict into the view shape the
    soil_report template (and programme template) expect.

    Returns three table-row groups (each a list of dicts the template
    iterates over):
      - nutrient_rows: parameters with sufficiency bands (range bars)
      - cation_balance_rows: % of CEC saturation for Ca/Mg/K/Na
      - cation_ratio_rows:   Ca:Mg, Mg:K, (Ca+Mg):K, Na:K, etc.

    The cation-balance + ratio rows surface lab-reported values that
    the original deterministic pass dropped — that left the per-block
    section with 8 nutrient rows and nothing else, which the user
    flagged as "not enough detail". Now both saturation and ratio data
    render as full tables with target bands sourced from the
    `ideal_ratios` reference table.
    """
    if not snap:
        return None
    block_id = snap.get("block_id") or ""
    if isinstance(block_id, str) and block_id.startswith("cluster_"):
        return None
    parameters = snap.get("parameters") or {}
    if not parameters:
        return None
    sample_label_parts: list[str] = []
    if snap.get("lab_name"):
        sample_label_parts.append(snap["lab_name"])
    if snap.get("lab_method"):
        sample_label_parts.append(snap["lab_method"])
    if snap.get("sample_date"):
        sd = snap["sample_date"]
        try:
            from datetime import date as _date
            sd_d = _date.fromisoformat(sd) if isinstance(sd, str) else sd
            sample_label_parts.append(f"sampled {sd_d.strftime('%-d %b %Y')}")
        except Exception:
            sample_label_parts.append(f"sampled {sd}")
    nutrient_rows = [
        _nutrient_status_view_from_dict(entry)
        for entry in (snap.get("nutrient_status") or [])
    ]
    ratio_rows = _ratio_finding_views_from_dicts(
        snap.get("factor_findings") or [],
        snap.get("computed_ratios") or {},
    )

    # Cation balance + ratio rows are the deep-dive additions. They
    # surface lab-reported saturations and ratios that don't have
    # sufficiency entries (and therefore wouldn't appear in the
    # `nutrient_rows` table) but DO have target bands in the
    # `ideal_ratios` reference table.
    soil_values = snap.get("parameters") or {}
    cation_balance_rows = _build_cation_balance_rows(soil_values, ideal_ratios or [])
    cation_ratio_rows = _build_cation_ratio_rows(soil_values, ideal_ratios or [])

    # Smart ratio-by-ratio interpretations + holistic summary + crop notes
    # — drives the new-direction "what does this soil pattern actually
    # mean for my crop" view. Falls back gracefully when a snap was
    # produced before the ratio_interpreter wiring landed.
    ratio_interpretations = [
        {
            "name": ri.get("name"),
            "value": ri.get("value"),
            "value_display": _format_ratio_value(ri.get("value"), ri.get("unit")),
            "ideal_low": ri.get("ideal_low"),
            "ideal_high": ri.get("ideal_high"),
            "ideal_display": _format_ratio_band(ri.get("ideal_low"), ri.get("ideal_high"), ri.get("unit")),
            "unit": ri.get("unit"),
            "state": ri.get("state"),
            "severity": ri.get("severity"),
            "what_it_measures": ri.get("what_it_measures"),
            "direct_effect": _strip_source_refs(ri.get("direct_effect") or ""),
            "bound_nutrients": ri.get("bound_nutrients") or [],
            "recommended_action": _strip_source_refs(ri.get("recommended_action") or "") if ri.get("recommended_action") else None,
            "source_citation": ri.get("source_citation"),
        }
        for ri in (snap.get("ratio_interpretations") or [])
    ]
    ratio_summary_dict = snap.get("ratio_summary") or None
    ratio_summary = None
    if ratio_summary_dict:
        ratio_summary = {
            "summary": _strip_source_refs(ratio_summary_dict.get("summary") or ""),
            "key_concerns": ratio_summary_dict.get("key_concerns") or [],
            "nutrients_at_risk": ratio_summary_dict.get("nutrients_at_risk") or [],
        }
    crop_notes = [
        {
            "kind": n.get("kind"),
            "headline": _strip_source_refs(n.get("headline") or ""),
            "detail": _strip_source_refs(n.get("detail") or ""),
            "severity": n.get("severity") or "info",
            "source_citation": n.get("source_citation"),
        }
        for n in (snap.get("crop_notes") or [])
    ]

    return {
        "block_id": block_id,
        "block_name": snap.get("block_name") or "",
        "block_area_ha": float(snap.get("block_area_ha") or 0.0),
        "sample_label": " · ".join(sample_label_parts) if sample_label_parts else None,
        "nutrient_rows": nutrient_rows,
        "cation_balance_rows": cation_balance_rows,
        "cation_ratio_rows": cation_ratio_rows,
        "ratio_rows": ratio_rows,
        "ratio_interpretations": ratio_interpretations,
        "ratio_summary": ratio_summary,
        "crop_notes": crop_notes,
        "headline_signals": [
            _strip_source_refs(s) for s in (snap.get("headline_signals") or []) if s
        ],
    }


def _format_ratio_value(value, unit):
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if unit == "%":
        return f"{v:.1f}%"
    return f"{v:.2f}"


def _format_ratio_band(low, high, unit):
    """Render a target band like '3.0–7.0' or '60–70%' or '≤ 5%' (one-sided)."""
    if low is None and high is None:
        return "—"
    suffix = "%" if unit == "%" else ""
    if low is None:
        return f"≤ {high:g}{suffix}"
    if high is None or high >= 999:
        return f"≥ {low:g}{suffix}"
    return f"{low:g}–{high:g}{suffix}"


# Fallback target bands when the live ideal_ratios table is unavailable
# (dev / test environments without a DB). Mirrors migration-time seeds
# from the `ideal_ratios` table so renders are deterministic when the
# DB lookup fails. Source: SA agronomy norms.
_FALLBACK_IDEAL_RATIOS: list[dict[str, Any]] = [
    {"ratio": "Ca:Mg",         "ideal_min": 3.0,  "ideal_max": 5.0,  "unit": "ratio"},
    {"ratio": "Mg:K",          "ideal_min": 2.0,  "ideal_max": 4.0,  "unit": "ratio"},
    {"ratio": "Ca:K",          "ideal_min": 10.0, "ideal_max": 20.0, "unit": "ratio"},
    {"ratio": "(Ca+Mg):K",     "ideal_min": 15.0, "ideal_max": 30.0, "unit": "ratio"},
    {"ratio": "K:Na",          "ideal_min": 5.0,  "ideal_max": 999.0, "unit": "ratio"},
    {"ratio": "Ca base sat.",  "ideal_min": 60.0, "ideal_max": 70.0, "unit": "%"},
    {"ratio": "Mg base sat.",  "ideal_min": 12.0, "ideal_max": 18.0, "unit": "%"},
    {"ratio": "K base sat.",   "ideal_min": 3.0,  "ideal_max": 5.0,  "unit": "%"},
    {"ratio": "Na base sat.",  "ideal_min": 0.0,  "ideal_max": 3.0,  "unit": "%"},
    {"ratio": "H+Al base sat.","ideal_min": 5.0,  "ideal_max": 15.0, "unit": "%"},
]


def _build_cation_balance_rows(
    soil_values: dict[str, Any],
    ideal_ratios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Per-cation saturation rows (% of CEC) — Ca, Mg, K, Na — plus
    Acid Saturation when the lab reports it. Each row carries value +
    target band + status pill + range-bar positions.

    Lab-reported saturations live in soil_values under keys like
    'Ca Saturation', 'Mg Saturation' etc. (the canonicaliser strips
    unit-suffixes upstream). Targets come from the `ideal_ratios`
    table keyed on '<Cation> base sat.' rows.
    """
    bands_by_cation: dict[str, tuple[float, float]] = {}
    for r in ideal_ratios:
        name = (r.get("ratio") or "").strip()
        if r.get("unit") != "%":
            continue
        # Map the ideal_ratios row name to the soil_values key. The lab
        # uses '<X> Saturation'; ideal_ratios uses '<X> base sat.'.
        for cation, label_match in (
            ("Ca", "Ca base sat"),
            ("Mg", "Mg base sat"),
            ("K",  "K base sat"),
            ("Na", "Na base sat"),
        ):
            if name.startswith(label_match):
                try:
                    bands_by_cation[cation] = (float(r["ideal_min"]), float(r["ideal_max"]))
                except (TypeError, ValueError, KeyError):
                    pass

    rows: list[dict[str, Any]] = []
    for cation, label, sv_key in (
        ("Ca", "Calcium",   "Ca Saturation"),
        ("Mg", "Magnesium", "Mg Saturation"),
        ("K",  "Potassium", "K Saturation"),
        ("Na", "Sodium",    "Na Saturation"),
    ):
        raw = soil_values.get(sv_key)
        if raw is None:
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            continue
        band = bands_by_cation.get(cation)
        if band:
            opt_low, opt_high = band
        else:
            opt_low, opt_high = 0.0, 100.0
        chart_max = max(opt_high * 1.4, v * 1.1, 1.0)
        chart_min = 0.0
        span = max(chart_max - chart_min, 1e-6)
        def pct(x: float) -> float:
            return max(0.0, min(100.0, (x - chart_min) / span * 100.0))
        status = (
            "low" if v < opt_low
            else "high" if v > opt_high
            else "ok"
        )
        rows.append({
            "label": f"{label} ({cation})",
            "value_display": f"{v:.1f}%",
            "optimal_display": f"{opt_low:g} – {opt_high:g}%",
            "status": status,
            "status_label": _status_label(status),
            "bar_value_pct": pct(v),
            "bar_optimal_left_pct": pct(opt_low),
            "bar_optimal_width_pct": max(0.0, pct(opt_high) - pct(opt_low)),
        })

    # Acid Saturation — surface as an info row when present, no band.
    acid = soil_values.get("Acid Saturation")
    if acid is not None:
        try:
            v = float(acid)
            status = "ok" if v <= 10 else "high"
            rows.append({
                "label": "Acid saturation (H+Al)",
                "value_display": f"{v:.1f}%",
                "optimal_display": "≤ 10% target",
                "status": status,
                "status_label": _status_label(status),
                "bar_value_pct": min(100.0, v / 25.0 * 100.0),
                "bar_optimal_left_pct": 0.0,
                "bar_optimal_width_pct": min(100.0, 10.0 / 25.0 * 100.0),
            })
        except (TypeError, ValueError):
            pass
    return rows


def _build_cation_ratio_rows(
    soil_values: dict[str, Any],
    ideal_ratios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Cation ratio rows — Ca:Mg, Mg:K, (Ca+Mg):K, Na:K — sourced from
    the lab's pre-computed values when present. Each row carries
    value + target band + status pill + range-bar positions.
    """
    bands_by_ratio: dict[str, tuple[float, float]] = {}
    for r in ideal_ratios:
        name = (r.get("ratio") or "").strip()
        if r.get("unit") not in ("ratio", None, ""):
            continue
        try:
            bands_by_ratio[name] = (float(r["ideal_min"]), float(r["ideal_max"]))
        except (TypeError, ValueError, KeyError):
            continue

    # Ratio key in soil_values → display label
    ratio_specs: list[tuple[str, str]] = [
        ("Ca:Mg",       "Ca : Mg"),
        ("Mg:K",        "Mg : K"),
        ("(Ca+Mg):K",   "(Ca + Mg) : K"),
        ("Na:K",        "Na : K"),
        ("Ca:K",        "Ca : K"),
    ]

    rows: list[dict[str, Any]] = []
    for sv_key, display in ratio_specs:
        raw = soil_values.get(sv_key)
        if raw is None:
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            continue
        # Match band by stripping spaces (Ca:Mg vs Ca : Mg)
        band = bands_by_ratio.get(sv_key)
        # K:Na in ideal_ratios is the inverse of Na:K in lab-reported
        # values; skip target band for the "Na:K" lab key.
        if band:
            opt_low, opt_high = band
            chart_max = max(opt_high * 1.4, v * 1.1, 1.0)
        else:
            # No target band — show value only with neutral marker.
            opt_low = opt_high = 0.0
            chart_max = max(v * 1.5, 1.0)
        chart_min = 0.0
        span = max(chart_max - chart_min, 1e-6)
        def pct(x: float) -> float:
            return max(0.0, min(100.0, (x - chart_min) / span * 100.0))
        if band:
            status = (
                "low" if v < opt_low
                else "high" if v > opt_high
                else "ok"
            )
            optimal_display = f"{opt_low:g} – {opt_high:g}"
        else:
            status = "info"
            optimal_display = "—"
        rows.append({
            "label": display,
            "value_display": f"{v:.2f}",
            "optimal_display": optimal_display,
            "status": status,
            "status_label": _status_label(status),
            "bar_value_pct": pct(v),
            "bar_optimal_left_pct": pct(opt_low) if band else 0.0,
            "bar_optimal_width_pct": (
                max(0.0, pct(opt_high) - pct(opt_low)) if band else 0.0
            ),
        })
    return rows


def _nutrient_status_view_from_dict(entry: dict[str, Any]) -> dict[str, Any]:
    """Mirror of `_nutrient_status_view` for dict input. Pre-computes the
    range-bar positions so the template stays presentation-only."""
    chart_min = entry.get("chart_min") if entry.get("chart_min") is not None else 0.0
    chart_max = entry.get("chart_max")
    optimal_low = float(entry.get("optimal_low") or 0)
    optimal_high = float(entry.get("optimal_high") or 0)
    value = float(entry.get("value") or 0)
    if chart_max is None:
        chart_max = max(optimal_high * 1.5, value * 1.1, 1.0)
    chart_min = float(chart_min)
    chart_max = float(chart_max)
    span = max(chart_max - chart_min, 1e-6)

    def pct(v: float) -> float:
        return max(0.0, min(100.0, (v - chart_min) / span * 100.0))

    optimal_low_pct = pct(optimal_low)
    optimal_high_pct = pct(optimal_high)
    return {
        "parameter": entry.get("parameter") or "",
        "label": entry.get("nutrient_label") or entry.get("parameter") or "",
        "value": value,
        "value_display": _fmt_soil_value(value),
        "optimal_low": optimal_low,
        "optimal_high": optimal_high,
        "optimal_display": f"{_fmt_soil_value(optimal_low)} – {_fmt_soil_value(optimal_high)}",
        "unit": entry.get("unit") or "",
        "status": entry.get("status") or "ok",
        "status_label": _status_label(entry.get("status") or "ok"),
        "bar_value_pct": pct(value),
        "bar_optimal_left_pct": optimal_low_pct,
        "bar_optimal_width_pct": max(0.0, optimal_high_pct - optimal_low_pct),
    }


def _ratio_finding_views_from_dicts(
    findings: list[dict[str, Any]],
    computed_ratios: dict[str, float],
) -> list[dict[str, Any]]:
    """Mirror of `_ratio_finding_views` for dict input."""
    out: list[dict[str, Any]] = []
    for f in findings:
        param = f.get("parameter") or ""
        # Skip the singleton 'kind' findings that are surfaced via
        # headline_signals already.
        if param in {"pH (KCl)", "pH (KCl)_high"} and f.get("kind") == "balance":
            # pH-band findings are surfaced as headline signals; the
            # ratios table is for cation/balance ratios, not pH.
            continue
        value = f.get("value") or 0
        threshold = f.get("threshold")
        severity = f.get("severity") or "info"
        message = _strip_source_refs(f.get("message") or "")
        action = _strip_source_refs(f.get("recommended_action") or "") if f.get("recommended_action") else ""
        # target_display direction: a flagged finding always has its
        # value on the wrong side of the threshold, so the side tells
        # us which bound it is. value > threshold → upper-bound breach
        # → "≤ T" (e.g. P:Zn ≤ 150, Al sat ≤ 5%). value < threshold →
        # lower-bound breach → "≥ T" (e.g. Ca:Mg ≥ 3). Equal or no
        # threshold → blank.
        if threshold is not None:
            try:
                t_num = float(threshold)
                v_num = float(value) if value is not None else t_num
                if v_num < t_num:
                    target_display = f"≥ {t_num:g}"
                else:
                    target_display = f"≤ {t_num:g}"
            except (TypeError, ValueError):
                target_display = ""
        else:
            target_display = ""
        # Range-bar positions — anchor 0..(threshold * 2) when threshold
        # known, else 0..(value * 2) so the marker has somewhere to sit.
        try:
            v = float(value)
        except (TypeError, ValueError):
            v = 0.0
        try:
            t = float(threshold) if threshold is not None else None
        except (TypeError, ValueError):
            t = None
        if t and t > 0:
            chart_max = max(t * 2.0, v * 1.1, t + 1.0)
            opt_left = 0.0
            opt_width = (t / chart_max) * 100.0
        else:
            chart_max = max(v * 2.0, 1.0)
            opt_left = 0.0
            opt_width = 100.0
        bar_value_pct = max(0.0, min(100.0, (v / chart_max) * 100.0)) if chart_max > 0 else 0.0
        out.append({
            "label": param,
            "value_display": f"{v:g}",
            "target_display": target_display,
            "severity": severity,
            "severity_label": _status_label(severity),
            "message": message,
            "recommended_action": action,
            "bar_value_pct": bar_value_pct,
            "bar_optimal_left_pct": opt_left,
            "bar_optimal_width_pct": opt_width,
        })
    return out


def _status_label(status: str) -> str:
    return {
        "low": "Low",
        "ok": "OK",
        "high": "High",
        "watch": "Watch",
        "warn": "Watch closely",
        "critical": "Critical",
        "info": "Note",
        "fyi": "Note",
    }.get(status, status.title())


def _build_trend_view(trend: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Adapt one BlockTrendReport dict into the template view shape."""
    n = trend.get("n_analyses") or 0
    if n < 2:
        return None
    span_days = trend.get("span_days") or 0
    months = max(1, span_days // 30)
    span_label = f"{months} month{'s' if months != 1 else ''}"

    direction_class = {
        "improving": "ok",
        "declining": "high",  # red marker for declining
        "stable": "ok",
        "uncertain": "watch",
    }
    direction_label = {
        "improving": "Improving",
        "declining": "Declining",
        "stable": "Stable",
        "uncertain": "Unclear",
    }
    sig_label = {
        "major": "Significant",
        "minor": "Minor",
        "none": "Within noise",
    }

    rows: list[dict[str, Any]] = []
    for p in trend.get("parameters") or []:
        rows.append({
            "parameter": p.get("parameter") or "",
            "earliest_display": _fmt_soil_value(p.get("earliest_value") or 0),
            "latest_display": _fmt_soil_value(p.get("latest_value") or 0),
            "delta_display": _fmt_delta(p),
            "direction": p.get("direction") or "stable",
            "direction_class": direction_class.get(p.get("direction") or "stable", "ok"),
            "direction_label": direction_label.get(p.get("direction") or "stable", "Stable"),
            "significance_label": sig_label.get(p.get("significance") or "none", "Unknown"),
        })
    return {
        "block_id": trend.get("block_id") or "",
        "block_name": trend.get("block_name") or "",
        "n_analyses": n,
        "span_label": span_label,
        "headline_signals": [_strip_source_refs(s) for s in (trend.get("headline_signals") or []) if s],
        "parameter_rows": rows,
    }


def _fmt_delta(p: dict[str, Any]) -> str:
    delta = p.get("delta")
    rel = p.get("relative_delta")
    if delta is None:
        return ""
    try:
        sign = "+" if float(delta) >= 0 else "−"
        delta_v = abs(float(delta))
        rel_v = abs(float(rel)) * 100 if rel is not None else 0
        return f"{sign}{_fmt_soil_value(delta_v)} ({sign}{rel_v:.1f}%)"
    except (TypeError, ValueError):
        return ""


def _apply_soil_report_overrides(
    context: dict[str, Any],
    overrides: dict[str, Any],
) -> None:
    """Replace deterministic intros with Opus-generated prose. Mirrors
    `_apply_narrative_overrides` for the programme path. Recognised
    keys: 'executive_summary', 'blocks_intro', 'trends_intro',
    'holistic_intro', 'headline_signals'."""
    if "executive_summary" in overrides and overrides["executive_summary"]:
        context["executive_intro"] = str(overrides["executive_summary"]).strip()
    if "blocks_intro" in overrides and overrides["blocks_intro"]:
        context["blocks_intro"] = str(overrides["blocks_intro"]).strip()
    if "trends_intro" in overrides and overrides["trends_intro"]:
        context["trends_intro"] = str(overrides["trends_intro"]).strip()
    if "holistic_intro" in overrides and overrides["holistic_intro"]:
        context["holistic_intro"] = str(overrides["holistic_intro"]).strip()
    if "headline_signals" in overrides and overrides["headline_signals"]:
        # Opus may produce richer headline strings — accept list-of-str.
        signals = overrides["headline_signals"]
        if isinstance(signals, list):
            context["headline_signals"] = [str(s).strip() for s in signals if s]


# ============================================================
# Narrative overlay — Opus prose replaces deterministic baseline
# ============================================================

def _baseline_for_narrative(
    context: dict[str, Any], artifact: ProgrammeArtifact,
) -> dict[str, Any]:
    """Pack the deterministic-engine prose into the shape the
    narrative pipeline expects. The pipeline uses these as tone
    references and as fallback when any layer FAILs."""
    return {
        "background_intro": context.get("background_intro", ""),
        "glance_facts": list(context.get("glance_facts") or []),
        "soil_intro": context.get("soil_intro", ""),
        "walkthrough_intro": (context.get("walkthrough") or {}).get("intro", ""),
        "year_outlook_cards": list(context.get("year_outlook_cards") or []),
        "is_mature": _infer_orchard_is_mature(artifact)
        if _is_perennial(artifact.header.crop)
        else False,
    }


def _apply_narrative_overrides(
    context: dict[str, Any], overrides: dict[str, Any],
) -> None:
    """Overlay Opus-generated prose onto the rendering context. Empty
    or missing keys leave the deterministic baseline untouched — the
    pipeline returns an empty dict when the policeman FAILs."""
    if not overrides:
        return
    if overrides.get("background_intro"):
        context["background_intro"] = overrides["background_intro"]
    if overrides.get("soil_intro"):
        context["soil_intro"] = overrides["soil_intro"]
    if overrides.get("walkthrough_intro") and isinstance(
        context.get("walkthrough"), dict
    ):
        context["walkthrough"]["intro"] = overrides["walkthrough_intro"]
    if overrides.get("year_outlook_cards"):
        context["year_outlook_cards"] = overrides["year_outlook_cards"]


# ============================================================
# Context builder — maps ProgrammeArtifact to template variables
# ============================================================

def _build_context(artifact: ProgrammeArtifact) -> dict[str, Any]:
    header = _build_header_context(artifact)
    soil_snapshots = _build_soil_context(artifact)
    pre_season_recommendations = _build_pre_season_context(artifact)
    walkthrough = _build_walkthrough_context(artifact)
    foliar_events = _build_foliar_context(artifact)
    nutrient_balance = _build_nutrient_balance_context(artifact)
    year_outlook_cards = _build_year_outlook_context(artifact)
    # Unified "Items We're Carrying" — replaces the old three-bucket
    # split (risk_flags / outstanding_items / assumptions). Dedupes
    # cross-bucket overlap and sorts by urgency band.
    carrying_items = _build_carrying_items_context(artifact)
    carrying_bands = _group_carrying_items_by_band(carrying_items)

    background_intro, glance_facts, soil_intro = _build_intro_prose(artifact)
    cover_subhead = _build_cover_subhead(artifact)

    contents_entries = _build_contents_entries(
        has_soil=bool(soil_snapshots),
        has_pre_season=bool(pre_season_recommendations),
        has_blends=bool(walkthrough.get("groups")),
        has_foliar=bool(foliar_events),
        has_nutrient_balance=bool(nutrient_balance),
        has_year_outlook=bool(year_outlook_cards),
        has_items=bool(carrying_items),
    )

    return {
        "header": header,
        "cover_subhead": cover_subhead,
        "contents_entries": contents_entries,
        "background_intro": background_intro,
        "glance_facts": glance_facts,
        "soil_intro": soil_intro,
        "soil_snapshots": soil_snapshots,
        "pre_season_recommendations": pre_season_recommendations,
        "walkthrough": walkthrough,
        "foliar_events": foliar_events,
        "nutrient_balance": nutrient_balance,
        "year_outlook_cards": year_outlook_cards,
        "carrying_items": carrying_items,
        "carrying_bands": carrying_bands,
    }


# ============================================================
# Section-level context builders
# ============================================================

def _build_header_context(artifact: ProgrammeArtifact) -> dict[str, Any]:
    h = artifact.header
    return {
        "client_name": h.client_name,
        "farm_name": h.farm_name,
        "location": h.location,
        "prepared_for": h.prepared_for,
        "prepared_by": h.prepared_by,
        "prepared_date_formatted": h.prepared_date.strftime("%-d %B %Y"),
        "ref_number": h.ref_number,
        "crop": h.crop,
        "season": h.season,
    }


def _build_cover_subhead(artifact: ProgrammeArtifact) -> str:
    """Subhead under the cover headline. One sentence describing scope."""
    h = artifact.header
    # Source blocks only — exclude cluster aggregates which carry the
    # cluster total area and would double the headline area number.
    sources = [s for s in artifact.soil_snapshots if not s.block_id.startswith("cluster_")]
    n_blocks = len(sources)
    total_ha = sum(s.block_area_ha for s in sources) if n_blocks else 0
    if n_blocks == 1:
        return (
            f"Season {h.season} programme for a {total_ha:.2f} ha block of "
            f"{h.crop.lower()}."
        )
    if n_blocks > 1:
        return (
            f"Season {h.season} programme for {n_blocks} blocks across "
            f"{total_ha:.1f} ha of {h.crop.lower()}."
        )
    return f"Season {h.season} programme for {h.crop.lower()}."


def _build_intro_prose(artifact: ProgrammeArtifact) -> tuple[str, list[str], str]:
    """Background intro paragraph, programme-at-a-glance bullets, soil intro."""
    h = artifact.header
    sources = [s for s in artifact.soil_snapshots if not s.block_id.startswith("cluster_")]
    n_blocks = len(sources)
    total_ha = sum(s.block_area_ha for s in sources) if n_blocks else 0

    background = (
        f"This programme covers the {h.season} season for {h.crop.lower()} "
        f"across {n_blocks} block{'s' if n_blocks != 1 else ''} totalling "
        f"{total_ha:.2f} ha. The strategy is built around the soil analysis, "
        f"the available equipment, and the crop's stage-by-stage demand curve."
    )

    glance: list[str] = []
    if n_blocks:
        glance.append(
            f"{n_blocks} block{'s' if n_blocks != 1 else ''} totalling "
            f"{total_ha:.2f} ha"
        )
    # Blends are the recipe definitions; applications are the
    # individual passes (one stage × one method × one event date).
    # Both numbers matter: blends drive shed planning, applications
    # drive the calendar. Render both so the two sections downstream
    # never look like they disagree.
    n_blends = len(artifact.blends)
    n_applications = sum(
        len(b.applications) if b.applications else 1
        for b in artifact.blends
    )
    if n_blends:
        if n_applications != n_blends:
            glance.append(
                f"{n_applications} application{'s' if n_applications != 1 else ''} "
                f"across {n_blends} blend{'s' if n_blends != 1 else ''} this season"
            )
        else:
            glance.append(
                f"{n_blends} blend{'s' if n_blends != 1 else ''} scheduled across the season"
            )
    n_foliar = len(artifact.foliar_events)
    if n_foliar:
        glance.append(
            f"{n_foliar} targeted foliar spray{'s' if n_foliar != 1 else ''} "
            f"addressing soil-availability gaps and stage-peak demand"
        )
    n_outstanding = len(artifact.outstanding_items)
    if n_outstanding:
        glance.append(
            f"{n_outstanding} open item{'s' if n_outstanding != 1 else ''} "
            f"flagged for tracking through the season"
        )

    soil_intro = ""
    if n_blocks == 1:
        s = artifact.soil_snapshots[0]
        soil_intro = (
            f"Soil analysis for {s.block_name} ({s.block_area_ha:.2f} ha) was "
            f"reviewed against the crop's nutrient requirements for the season."
        )
    elif n_blocks > 1:
        soil_intro = (
            f"Soil analyses across {n_blocks} blocks were reviewed against the "
            f"crop's nutrient requirements for the season."
        )

    return background, glance, soil_intro


def _build_contents_entries(
    *,
    has_soil: bool,
    has_pre_season: bool,
    has_blends: bool,
    has_foliar: bool,
    has_nutrient_balance: bool,
    has_year_outlook: bool,
    has_items: bool,
) -> list[dict[str, Any]]:
    """Build the contents list with stable anchors. Page numbers are
    NOT computed in Python — WeasyPrint's `target-counter()` resolves
    the actual rendered page number per anchor at print time, so the
    TOC stays correct regardless of section length, Opus prose
    expansion, or any other content variation. The template links each
    row to `#section-<anchor>`; CSS injects the page number via the
    `::after` pseudo-element. See style.css `.contents__row::after`.
    """
    entries: list[dict[str, Any]] = [
        {"title": "Background", "anchor": "section-background"},
    ]
    if has_soil:
        entries.append({"title": "Soil Report", "anchor": "section-soil"})
    if has_pre_season:
        entries.append({"title": "Pre-Season Actions", "anchor": "section-pre-season"})
    if has_blends:
        entries.append({"title": "Application Walkthrough", "anchor": "section-walkthrough"})
    if has_foliar:
        entries.append({"title": "Foliar Sprays", "anchor": "section-foliar"})
    if has_nutrient_balance:
        entries.append({"title": "Season Totals", "anchor": "section-totals"})
    if has_year_outlook:
        entries.append({"title": "Year 2 and Beyond", "anchor": "section-outlook"})
    if has_items:
        entries.append({"title": "Items We're Carrying Into The Season", "anchor": "section-items"})
    return entries


def _build_soil_context(artifact: ProgrammeArtifact) -> list[dict[str, Any]]:
    """Per-block soil report context — full parameter readings with
    range-bar positions, ratio findings with severity, and the headline
    signal callouts. Cluster aggregates are filtered out: their
    parameters are area-weighted means that the agronomist already sees
    via the per-block snapshots, and surfacing them again under their
    own header reads as duplication.
    """
    out: list[dict[str, Any]] = []
    for snap in artifact.soil_snapshots:
        # Skip cluster-aggregate snapshots — they're synthetic averages
        # of the block-level snapshots already rendered above them.
        if snap.block_id.startswith("cluster_"):
            continue
        # Skip dataless blocks (parameters empty) — there's no analysis
        # to read.
        if not snap.parameters:
            continue
        sample_label_parts = []
        if snap.lab_name:
            sample_label_parts.append(snap.lab_name)
        if snap.lab_method:
            sample_label_parts.append(snap.lab_method)
        if snap.sample_date:
            sample_label_parts.append(f"sampled {snap.sample_date.strftime('%-d %b %Y')}")
        nutrient_rows = [
            _nutrient_status_view(entry)
            for entry in (snap.nutrient_status or [])
        ]
        ratio_rows = _ratio_finding_views(snap.factor_findings or [], snap.computed_ratios or {})
        out.append({
            "block_id": snap.block_id,
            "block_name": snap.block_name,
            "block_area_ha": snap.block_area_ha,
            "sample_label": " · ".join(sample_label_parts) if sample_label_parts else None,
            "nutrient_rows": nutrient_rows,
            "ratio_rows": ratio_rows,
            "headline_signals": [
                _strip_source_refs(s) for s in snap.headline_signals if s
            ],
        })
    return out


def _nutrient_status_view(entry: Any) -> dict[str, Any]:
    """One parameter row with pre-computed range-bar positions so the
    template only renders presentation, not math.

    Positions are clamped 0-100% and assume the engine populated
    chart_min / chart_max with bounds that include the block's value
    even when it sits outside the optimal band.
    """
    chart_min = entry.chart_min if entry.chart_min is not None else 0.0
    chart_max = entry.chart_max if entry.chart_max is not None else max(
        entry.optimal_high * 1.5, entry.value * 1.1, 1.0
    )
    span = max(chart_max - chart_min, 1e-6)

    def pct(v: float) -> float:
        return max(0.0, min(100.0, (v - chart_min) / span * 100.0))

    optimal_low_pct = pct(entry.optimal_low)
    optimal_high_pct = pct(entry.optimal_high)
    return {
        "parameter": entry.parameter,
        "label": entry.nutrient_label,
        "value": entry.value,
        "value_display": _fmt_soil_value(entry.value),
        "optimal_low": entry.optimal_low,
        "optimal_high": entry.optimal_high,
        "optimal_display": f"{_fmt_soil_value(entry.optimal_low)} – {_fmt_soil_value(entry.optimal_high)}",
        "unit": entry.unit or "",
        "status": entry.status,
        "status_label": _STATUS_LABEL.get(entry.status, entry.status.upper()),
        "bar_optimal_left_pct": optimal_low_pct,
        "bar_optimal_width_pct": max(optimal_high_pct - optimal_low_pct, 1.0),
        "bar_value_pct": pct(entry.value),
    }


def _ratio_finding_views(
    findings: list[Any],
    computed_ratios: dict[str, float],
) -> list[dict[str, Any]]:
    """Build the COMPLETE ratio table for one block — every relevant
    ratio the engine knows about, including the in-range ones.

    Strategy:
      1. Walk `_RATIO_BOUNDS` (the curated list of ratios we care about).
      2. For each, pull the current value from `computed_ratios` first,
         then from any flagged finding — both are valid sources.
      3. Classify status from the bounds + value (low / ok / high).
      4. If a flagged finding exists and its severity beats the
         bounds-based status (warn/critical), let the finding's
         severity + message win — that's the engine speaking.
      5. Always emit a row, even when the ratio is `OK` and the
         engine had nothing to say. The agronomist gets a full picture
         — "Ca:Mg 4.2 (target 3-5) · OK" is just as informative as a
         flagged row.

    Returns rows sorted critical → warn → watch → ok → info, with
    alphabetical fallback so the same farm renders the same way every
    build.
    """
    severity_rank = {
        "critical": 0, "warn": 1, "high": 1, "low": 1,
        "watch": 2, "ok": 3, "info": 4,
    }
    findings_by_param: dict[str, Any] = {}
    for f in findings:
        if f.parameter and f.parameter not in findings_by_param:
            findings_by_param[f.parameter] = f

    rows: list[dict[str, Any]] = []
    for key, bounds in _RATIO_BOUNDS.items():
        value = computed_ratios.get(key)
        finding = findings_by_param.get(key)
        if value is None and finding is not None:
            value = finding.value
        if value is None or not isinstance(value, (int, float)):
            continue
        value = float(value)
        bounds_status = _classify_ratio(value, bounds)
        # Engine flag wins over bounds-derived status for severity.
        if finding is not None:
            severity = finding.severity
            severity_label = _STATUS_LABEL.get(severity, severity.upper())
            message = _strip_source_refs(finding.message or "") or _ratio_default_message(bounds_status, bounds)
            recommended_action = _strip_source_refs(finding.recommended_action or "") if finding.recommended_action else ""
        else:
            severity = bounds_status  # 'ok' / 'low' / 'high'
            severity_label = _STATUS_LABEL.get(severity, severity.upper())
            message = _ratio_default_message(bounds_status, bounds)
            recommended_action = ""
        cmin, cmax = bounds["chart_min"], bounds["chart_max"]
        # Adjust bounds so the marker stays on-chart for outliers
        # (especially Ca:B and Al saturation can blow the upper bound).
        if value > cmax:
            cmax = value * 1.05
        if value < cmin:
            cmin = max(0.0, value - abs(value) * 0.1 - 1)
        span = max(cmax - cmin, 1e-6)
        opt_low = max(cmin, bounds["ideal_low"])
        opt_high = min(cmax, bounds["ideal_high"])
        bar_opt_left = (opt_low - cmin) / span * 100
        bar_opt_width = max((opt_high - opt_low) / span * 100, 1.0)
        bar_value_pct = max(0.0, min(100.0, (value - cmin) / span * 100))
        rows.append({
            "parameter": key,
            "label": bounds["label"],
            "value_display": bounds["value_fmt"].format(value),
            "target_display": bounds["target_fmt"],
            "severity": severity,
            "severity_label": severity_label,
            "message": message,
            "recommended_action": recommended_action,
            "bar_optimal_left_pct": bar_opt_left,
            "bar_optimal_width_pct": bar_opt_width,
            "bar_value_pct": bar_value_pct,
        })
    rows.sort(key=lambda r: (severity_rank.get(r["severity"], 5), r["label"]))
    return rows


def _classify_ratio(value: float, bounds: dict) -> str:
    """Return 'low' / 'ok' / 'high' from the value relative to the
    target bounds. Three flavours of bounds:
      * `in_range` — ideal_low ≤ value ≤ ideal_high (e.g. Ca:Mg 3-5).
      * `upper_limit` — only too-high is bad (Al saturation, ESP, SAR).
      * `lower_limit` — only too-low is bad (K:Na must stay above 1).
    """
    kind = bounds.get("kind", "in_range")
    if kind == "upper_limit":
        return "high" if value > bounds["ideal_high"] else "ok"
    if kind == "lower_limit":
        return "low" if value < bounds["ideal_low"] else "ok"
    if value < bounds["ideal_low"]:
        return "low"
    if value > bounds["ideal_high"]:
        return "high"
    return "ok"


def _ratio_default_message(status: str, bounds: dict) -> str:
    """Plain-English status when the engine had nothing flagged. The
    agronomist still wants context, not a bare 'ok' next to a number."""
    if status == "ok":
        return "Within target — no action."
    if status == "low":
        return f"Below target ({bounds['target_fmt']}). {bounds.get('low_action', '')}".strip()
    if status == "high":
        return f"Above target ({bounds['target_fmt']}). {bounds.get('high_action', '')}".strip()
    return ""


# Curated list of soil ratios the report surfaces. Order = display
# order in the per-block ratios table (cation balance first, then
# antagonism / sodium / acid / carbon — same order an agronomist
# reading the report would expect). Bounds + targets follow FERTASA
# guidance for tropical / sub-tropical SA crops; per-crop overrides
# can land later if needed.
_RATIO_BOUNDS: dict[str, dict[str, Any]] = {
    "Ca:Mg": {
        "label": "Ca : Mg",
        "kind": "in_range",
        "ideal_low": 3.0, "ideal_high": 5.0,
        "chart_min": 0.0, "chart_max": 10.0,
        "value_fmt": "{:.1f} : 1",
        "target_fmt": "3 – 5 : 1",
        "low_action": "Lift Ca via lime / gypsum to balance the cation complex.",
        "high_action": "Mg may be antagonised — consider a Mg foliar at peak demand.",
    },
    "(Ca+Mg):K": {
        "label": "(Ca + Mg) : K",
        "kind": "in_range",
        "ideal_low": 20.0, "ideal_high": 30.0,
        "chart_min": 0.0, "chart_max": 50.0,
        "value_fmt": "{:.1f} : 1",
        "target_fmt": "20 – 30 : 1",
        "low_action": "K dominates the exchange — Mg uptake will be limited.",
        "high_action": "K is being out-competed — top up via fertigation or band.",
    },
    "Mg:K": {
        "label": "Mg : K",
        "kind": "in_range",
        "ideal_low": 2.0, "ideal_high": 4.0,
        "chart_min": 0.0, "chart_max": 8.0,
        "value_fmt": "{:.1f} : 1",
        "target_fmt": "2 – 4 : 1",
        "low_action": "Lift Mg to restore the balance.",
        "high_action": "K supply needs strengthening at this stage.",
    },
    "K:Na": {
        "label": "K : Na",
        "kind": "lower_limit",
        "ideal_low": 1.0, "ideal_high": 999.0,
        "chart_min": 0.0, "chart_max": 5.0,
        "value_fmt": "{:.1f} : 1",
        "target_fmt": "≥ 1 : 1",
        "low_action": "Na is competing with K — gypsum + extra K needed.",
    },
    "P:Zn": {
        # Antagonism threshold — Foth & Ellis "Soil Fertility" 2nd ed.
        # (1997) p.224. Above 150:1 soil P starts to lock up Zn
        # availability. Same threshold the engine uses internally
        # (`P_ZN_ANTAGONISM_THRESHOLD = 150.0` in soil_factor_reasoner)
        # — kept aligned so the Soil Report's "HIGH" status matches
        # the engine's antagonism finding + foliar-Zn trigger.
        "label": "P : Zn",
        "kind": "upper_limit",
        "ideal_low": 0.0, "ideal_high": 150.0,
        "chart_min": 0.0, "chart_max": 250.0,
        "value_fmt": "{:.1f} : 1",
        "target_fmt": "≤ 150 : 1",
        "high_action": "Heavy P will lock up Zn — foliar Zn to bypass soil-P antagonism.",
    },
    "Ca:B": {
        "label": "Ca : B",
        "kind": "upper_limit",
        "ideal_low": 0.0, "ideal_high": 1000.0,
        "chart_min": 0.0, "chart_max": 3000.0,
        "value_fmt": "{:,.0f} : 1",
        "target_fmt": "≤ 1000 : 1",
        "high_action": "B will be Ca-induced deficient — foliar B at flowering.",
    },
    "C:N": {
        "label": "C : N",
        "kind": "in_range",
        "ideal_low": 8.0, "ideal_high": 15.0,
        "chart_min": 0.0, "chart_max": 30.0,
        "value_fmt": "{:.1f} : 1",
        "target_fmt": "8 – 15 : 1",
        "low_action": "N mineralises rapidly — losses possible without timing care.",
        "high_action": "Microbial N tie-up — additional N needed early in the season.",
    },
    "Al_saturation_pct": {
        "label": "Acid (Al) saturation",
        "kind": "upper_limit",
        "ideal_low": 0.0, "ideal_high": 10.0,
        "chart_min": 0.0, "chart_max": 50.0,
        "value_fmt": "{:.1f} %",
        "target_fmt": "≤ 10 %",
        "high_action": "Lime to neutralise active Al before stressing the root system further.",
    },
    "soil_ESP_pct": {
        "label": "Sodium saturation (ESP)",
        "kind": "upper_limit",
        "ideal_low": 0.0, "ideal_high": 5.0,
        "chart_min": 0.0, "chart_max": 30.0,
        "value_fmt": "{:.1f} %",
        "target_fmt": "≤ 5 %",
        "high_action": "Sodic risk — gypsum to displace Na off the exchange.",
    },
    "SAR": {
        "label": "SAR",
        "kind": "upper_limit",
        "ideal_low": 0.0, "ideal_high": 3.0,
        "chart_min": 0.0, "chart_max": 15.0,
        "value_fmt": "{:.1f}",
        "target_fmt": "≤ 3",
        "high_action": "Irrigation water raising sodicity — gypsum + leaching.",
    },
    "water_SAR": {
        "label": "Irrigation SAR",
        "kind": "upper_limit",
        "ideal_low": 0.0, "ideal_high": 3.0,
        "chart_min": 0.0, "chart_max": 15.0,
        "value_fmt": "{:.1f}",
        "target_fmt": "≤ 3",
        "high_action": "Water test recommends gypsum injection or alternate source.",
    },
    "water_RSC_meq": {
        "label": "Irrigation RSC",
        "kind": "upper_limit",
        "ideal_low": 0.0, "ideal_high": 1.25,
        "chart_min": 0.0, "chart_max": 5.0,
        "value_fmt": "{:.2f} meq/L",
        "target_fmt": "≤ 1.25 meq/L",
        "high_action": "RSC indicates carbonate stress — acidify or alternate water.",
    },
}


def _fmt_soil_value(v: float) -> str:
    if v == 0:
        return "0"
    av = abs(v)
    if av >= 100:
        return f"{v:.0f}"
    if av >= 10:
        return f"{v:.1f}"
    return f"{v:.2f}"


# Status pill labels for both nutrient_status and factor finding rows.
# Maps engine codes to all-caps display strings (matches Allicro design).
_STATUS_LABEL: dict[str, str] = {
    "low": "LOW",
    "ok": "OK",
    "high": "HIGH",
    "info": "WITHIN RANGE",
    "watch": "WATCH",
    "warn": "WARN",
    "critical": "CRITICAL",
}

_RATIO_PRETTY: dict[str, str] = {
    "Ca:Mg": "Ca : Mg",
    "(Ca+Mg):K": "(Ca + Mg) : K",
    "Ca:K": "Ca : K",
    "Mg:K": "Mg : K",
    "K:Mg": "K : Mg",
    "K:Na": "K : Na",
    "P:Zn": "P : Zn",
    "Ca:B": "Ca : B",
    "C:N": "C : N",
    "Al_saturation_pct": "Al saturation",
    "soil_ESP_pct": "Exchangeable Na (ESP)",
    "SAR": "SAR",
    "water_SAR": "Irrigation SAR",
    "water_RSC_meq": "Irrigation RSC",
}


def _build_pre_season_context(
    artifact: ProgrammeArtifact,
) -> list[dict[str, Any]]:
    """Pre-season corrective recommendations aggregated per group.

    The farmer applies amendments at the group level (one spread of
    lime across all of Group A's blocks, not three different rates).
    Recommendations are grouped by (group_letter, material_label) and
    rates are area-weighted across the blocks in that group that need
    the material. Blocks in the group without a recommendation for
    that material aren't averaged in — the rate represents what blocks
    needing the action should receive on average.

    Returns one row per (group × material) combination, ordered by
    group letter then by material name.
    """
    if not artifact.pre_season_recommendations:
        return []

    # ── Per-block, grouped by group_letter ──────────────────────────
    # Pre-season corrections are applied per block — lime / gypsum /
    # dolomitic spreaders are routinely programmed per-area, and each
    # block in a group can have a genuinely different rate based on
    # its individual soil chemistry. Averaging across the group loses
    # that precision and can leave the most-affected block under-
    # treated. The grouping here is for VISUAL ORGANISATION only:
    # rows are grouped under the group header so the agronomist sees
    # all of Group A's pre-season work together, but each row carries
    # the specific block's specific rate.

    # Build block_id → group_letter map AND group_letter → full member
    # list. The full member list (from the cluster snapshot's
    # comma-joined block_name) drives the section header — every block
    # in the group shows in the header even when only some need a
    # given action.
    block_to_group: dict[str, str] = {}
    name_by_id: dict[str, str] = {}
    group_full_members: dict[str, list[str]] = {}
    for s in artifact.soil_snapshots:
        name_by_id[s.block_id] = s.block_name
        if not s.block_id.startswith("cluster_"):
            continue
        letter = s.block_id.replace("cluster_", "").upper()
        members = [m.strip() for m in (s.block_name or "").split(",") if m.strip()]
        group_full_members[letter] = members
        for member_label in members:
            for indiv in artifact.soil_snapshots:
                if indiv.block_id.startswith("cluster_"):
                    continue
                if indiv.block_name == member_label or indiv.block_name.startswith(member_label):
                    block_to_group[indiv.block_id] = letter
    if not block_to_group:
        # No clustering at all — singleton groups labelled A, B, C…
        for i, s in enumerate(
            x for x in artifact.soil_snapshots if not x.block_id.startswith("cluster_")
        ):
            letter = chr(ord("A") + i)
            block_to_group[s.block_id] = letter
            group_full_members[letter] = [s.block_name]

    rows: list[dict[str, Any]] = []
    for r in artifact.pre_season_recommendations:
        letter = block_to_group.get(r.block_id, "?")
        block_label = name_by_id.get(r.block_id, r.block_id)
        full_group_members = group_full_members.get(letter, [block_label])
        rows.append({
            "group_letter": letter,
            "group_members": full_group_members,
            "group_member_summary": ", ".join(full_group_members),
            "block_id": r.block_id,
            "block_name": block_label,
            "material": _display_material(r.material or ""),
            "target_rate_per_ha": r.target_rate_per_ha or "",
            "apply_by": _format_apply_by_period(r.recommended_apply_by_date),
            "reaction_time_months": r.reaction_time_months,
            "purpose": _strip_source_refs(r.purpose or ""),
            "reason": _strip_source_refs(r.reason or ""),
            "expected_status_at_planting": _strip_source_refs(r.expected_status_at_planting or ""),
        })
    # Sort by group letter, then by block name within the group, so the
    # template can emit "Group A: Blok 100 row, Blok 101 row, …" cleanly.
    rows.sort(key=lambda r: (r["group_letter"], r["block_name"]))
    return rows


def _format_apply_by_period(d: Any) -> str:
    """Apply-by date formatted as Early/Mid/Late-Month YYYY (matches
    the walkthrough's date convention). Returns "" when missing or
    unparseable."""
    if d is None:
        return ""
    try:
        if isinstance(d, str):
            from datetime import date as _date
            d = _date.fromisoformat(d[:10])
        period = "Early" if d.day <= 10 else "Mid" if d.day <= 20 else "Late"
        return f"{period}-{d.strftime('%B %Y')}"
    except Exception:  # noqa: BLE001
        return str(d)


def _display_material(raw: str) -> str:
    """Display name for a material — drops parenthetical qualifiers
    ("Calcitic lime (fine grade)" → "Calcitic lime") so the row label
    reads as the substance, not its descriptor variant. Casing is
    preserved as the engine emitted it."""
    if not raw:
        return ""
    stripped = re.sub(r"\([^)]*\)", "", raw)
    return re.sub(r"\s+", " ", stripped).strip()


def _build_blends_context(
    artifact: ProgrammeArtifact,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    """Legacy per-block blend grouping. Retained for tests; the live
    template uses _build_walkthrough_context instead, which flattens
    every (blend, application_event) into a chronological card so the
    farmer reads it as a calendar walk-through rather than a
    method-keyed catalogue."""
    block_names_by_id = {
        s.block_id: s.block_name for s in artifact.soil_snapshots
    }
    blends_by_block: dict[str, list[dict[str, Any]]] = {}
    for blend in artifact.blends:
        bucket = blends_by_block.setdefault(blend.block_id, [])
        bucket.append(_blend_view(blend))
    return blends_by_block, block_names_by_id


# ── Walkthrough rendering — chronological farmer-facing applications ─

# Plain-English action verb + placement note per method. The agronomist
# can read straight off this without translating engine-speak.
_METHOD_ACTION: dict[str, dict[str, str]] = {
    "DRY_BROADCAST": {
        "verb": "Spread",
        "placement": "Spread evenly under the canopy with a granular spreader.",
    },
    "DRY_BAND": {
        "verb": "Place",
        "placement": "Place in a banded ring around each tree at the drip line.",
    },
    "DRY_BASAL": {
        "verb": "Place",
        "placement": "Place as a pre-plant base and work in.",
    },
    "LIQUID_DRIP": {
        "verb": "Inject",
        "placement": "Inject through the drip irrigation line during a normal watering cycle.",
    },
    "LIQUID_PIVOT": {
        "verb": "Inject",
        "placement": "Inject into the centre-pivot during a normal irrigation pass.",
    },
    "LIQUID_SPRINKLER": {
        "verb": "Inject",
        "placement": "Inject through the sprinkler line during a normal irrigation cycle.",
    },
    "FOLIAR": {
        "verb": "Spray",
        "placement": "Spray onto the leaves with a foliar applicator.",
    },
}

# Plain-English context for each growth stage so a non-specialist
# reading the walkthrough understands *why* the timing matters.
_STAGE_EXPLANATION: dict[str, str] = {
    # Phrasings work for both annual and perennial crops. The
    # "establishment" / "vegetative" stages re-use the same key for
    # season-relative phases on perennials (where there's no actual
    # planting event) without implying a new planting.
    "establishment": "early-season re-growth — building roots, shoots, and the season's canopy",
    "vegetative": "leaf and shoot growth, building this year's canopy",
    "flowering": "flowering and pollination — the make-or-break window for the crop",
    "reproductive": "flowering and fruit-set — pushing flower spikes and starting nuts",
    "fruit_set": "early fruit-set — drop-prevention window",
    "fruit set": "early fruit-set — drop-prevention window",
    "fill": "nut / fruit fill — pulling nutrients into the kernel or fruit",
    "nut_fill": "nut fill — kernel oil and dry-matter accumulation",
    "nut fill": "nut fill — kernel oil and dry-matter accumulation",
    "maturation": "final maturation before harvest",
    "harvest": "harvest window",
    "post_harvest": "post-harvest recovery — replenishing reserves before next year",
    "post-harvest": "post-harvest recovery — replenishing reserves before next year",
    "pre_planting": "pre-plant preparation before drilling or transplanting",
    "pre-planting": "pre-plant preparation before drilling or transplanting",
    "at_planting": "the planting operation itself — starter feed at sowing or transplanting",
}


def _format_application_date(d: Any) -> tuple[str, str, str]:
    """Returns (period_label, week_label, month_label) e.g.
    ("Mid-March 2026", "Wk 11", "March 2026").

    Acceptable-period phrasing (early/mid/late + month) replaces exact
    calendar dates because field-application timing is weather-driven —
    a Tuesday vs Wednesday in mid-March doesn't change the agronomy.
    Bucket boundaries: 1-10 = early, 11-20 = mid, 21-end = late.
    """
    try:
        if isinstance(d, str):
            from datetime import date as _date
            d = _date.fromisoformat(d[:10])
        day = d.day
        if day <= 10:
            period = "Early"
        elif day <= 20:
            period = "Mid"
        else:
            period = "Late"
        month_name = d.strftime("%B")
        full = f"{period}-{month_name} {d.year}"
        short = f"{period[:3]} {d.strftime('%b')}"
        month = f"{month_name} {d.year}"
        return full, short, month
    except Exception:  # noqa: BLE001
        return str(d), str(d), ""


def _stage_explanation(stage_name: str) -> str:
    if not stage_name:
        return ""
    key = stage_name.strip().lower()
    if key in _STAGE_EXPLANATION:
        return _STAGE_EXPLANATION[key]
    # Loose match — strip parentheses, try base form.
    base = re.split(r"[()/]", key)[0].strip()
    return _STAGE_EXPLANATION.get(base, "")


def _walkthrough_brief(
    blend: Blend,
    stage_explanation: str,
    block_summary: str,
) -> str:
    """One-paragraph 'why this application' brief — deterministic,
    derived from the dominant nutrients delivered + stage explanation +
    block context. Reads like an agronomist briefing the farmer.
    """
    delivered = blend.nutrients_delivered or {}
    macro_order = ("N", "P2O5", "K2O", "Ca", "Mg", "S")
    ranked = sorted(
        ((nut, delivered.get(nut, 0.0)) for nut in macro_order),
        key=lambda kv: kv[1],
        reverse=True,
    )
    top = [k for k, v in ranked if v > 0][:2]
    nutrient_labels = {
        "N": "nitrogen", "P2O5": "phosphorus", "K2O": "potassium",
        "Ca": "calcium", "Mg": "magnesium", "S": "sulphur",
    }
    if top:
        nutrient_phrase = " and ".join(nutrient_labels.get(n, n) for n in top)
    else:
        nutrient_phrase = "supporting nutrients"
    pieces = []
    if stage_explanation:
        pieces.append(f"Trees are at {stage_explanation}, so this pass leads with {nutrient_phrase}.")
    else:
        pieces.append(f"This pass delivers {nutrient_phrase}.")
    if blend.method.kind.name == "FOLIAR":
        pieces.append(
            "Going on as a foliar spray puts the correction directly on the leaf — "
            "doesn't rely on the soil moving it for you."
        )
    elif blend.method.kind.name.startswith("LIQUID_"):
        pieces.append(
            "Delivered through the irrigation system so it reaches the active root zone "
            "without an extra ground operation."
        )
    elif blend.method.kind.name == "DRY_BAND":
        pieces.append(
            "Placed in a ring at the drip line so the feeder roots get it first."
        )
    return " ".join(pieces)


def _split_reason_text(blends_in_window: list[Blend]) -> str:
    """Plain-English explanation when multiple blends fire on the same
    date for the same group. Mirrors the wizard's explainSplit logic
    but written for a farmer audience.
    """
    if len(blends_in_window) < 2:
        return ""
    methods = {b.method.kind.name for b in blends_in_window}
    has_foliar = any(b.method.kind.name == "FOLIAR" for b in blends_in_window)
    has_soil = any(b.method.kind.name != "FOLIAR" for b in blends_in_window)
    if has_foliar and has_soil:
        return (
            "These two passes go on the same day. The foliar spray is a leaf-direct "
            "supplement on top of the main soil pass — not a replacement for it."
        )
    if len(methods) == 1:
        return (
            "Two separate passes on the same day. The products can't share a bag "
            "(urea + lime / SSP would release ammonia and lose nitrogen), so they go "
            "on as separate spreads."
        )
    return (
        "Two parallel passes on the same day, each via the method that suits its "
        "nutrient profile. The two passes together give the trees what they need at "
        "this stage."
    )


def _build_walkthrough_context(artifact: ProgrammeArtifact) -> dict[str, Any]:
    """Build the per-group, chronological walkthrough context. Layout:

        Group A — Blok 1, Blok 2, Blok 3 · 12.0 ha
          Day 1: A1 (single pass)
          Day 2: A2 + A3 (paired — 2 parallel passes)
          Day 3: A4 …

        Group B — Blok 4, Blok 5 · 8.0 ha
          Day 1: B1 (single pass)
          …

    Each "day" entry is either a single application or a paired-day
    bundle showing the two concurrent passes that share a date for the
    same group. The pair carries the engine's split reason as a header
    so the farmer reads "two trips on this day, here's why" rather than
    two unconnected cards.

    Returns {} when the artifact has no blends.
    """
    if not artifact.blends:
        return {}

    block_names_by_id: dict[str, str] = {}
    block_area_by_id: dict[str, float] = {}
    for s in artifact.soil_snapshots:
        block_names_by_id[s.block_id] = s.block_name
        block_area_by_id[s.block_id] = s.block_area_ha

    blend_by_row_id: dict[int, Blend] = {}

    # Step 1 — flatten every (blend, ApplicationEvent) into a row, then
    # bucket by group (block_id).
    rows_by_group: dict[str, list[dict[str, Any]]] = {}
    for blend in artifact.blends:
        events = blend.applications or [None]
        for app_event in events:
            row = _walkthrough_row(
                blend,
                application_event=app_event,
                block_names_by_id=block_names_by_id,
                block_area_by_id=block_area_by_id,
            )
            blend_by_row_id[id(row)] = blend
            rows_by_group.setdefault(blend.block_id, []).append(row)

    # Step 2 — for each group, sort chronologically, number rows
    # within the group ("A1", "A2"…), and bundle paired-day rows under
    # a single "day" entry.
    groups: list[dict[str, Any]] = []
    # Stable group order: cluster_A, cluster_B, … then singletons by id.
    cluster_keys = sorted(k for k in rows_by_group if k.startswith("cluster_"))
    singleton_keys = sorted(k for k in rows_by_group if not k.startswith("cluster_"))
    ordered_keys = cluster_keys + singleton_keys

    for group_idx, group_id in enumerate(ordered_keys):
        rows = rows_by_group[group_id]
        rows.sort(key=lambda r: (r["sort_key"], r.get("formula") or ""))

        # Group letter: from "cluster_A" use the suffix; for singletons
        # number A, B, C… in order of appearance.
        if group_id.startswith("cluster_"):
            letter = group_id.replace("cluster_", "").upper()
        else:
            letter = chr(ord("A") + group_idx)

        for i, row in enumerate(rows):
            row["number"] = f"{letter}{i + 1}"

        # Bucket adjacent rows that share a date into "day" objects.
        days: list[dict[str, Any]] = []
        for row in rows:
            day_key = row["sort_key"]
            if days and days[-1]["date_key"] == day_key:
                days[-1]["applications"].append(row)
            else:
                days.append({
                    "date_key": day_key,
                    "date_full": row["date_full"],
                    "date_short": row["date_short"],
                    "month_label": row["month_label"],
                    "week_from_planting": row.get("week_from_planting"),
                    "applications": [row],
                    "is_split": False,
                    "split_reason": "",
                })

        for day in days:
            if len(day["applications"]) > 1:
                day["is_split"] = True
                paired_blends = [blend_by_row_id[id(r)] for r in day["applications"]]
                day["split_reason"] = _split_reason_text(paired_blends)
                # Within a paired day, label each pass as Pass 1 / Pass 2 …
                # so the farmer reads the bundle as one day's work split
                # into N concurrent trips.
                for i, r in enumerate(day["applications"]):
                    r["pass_label"] = f"Pass {i + 1} of {len(day['applications'])}"
            else:
                day["applications"][0]["pass_label"] = ""

        # Group metadata — total area, member blocks. Cluster snapshots
        # carry the member list in their block_name (comma-joined); for
        # singleton groups it's just the one block name.
        cluster_snap = next(
            (s for s in artifact.soil_snapshots if s.block_id == group_id),
            None,
        )
        if cluster_snap:
            members = [m.strip() for m in cluster_snap.block_name.split(",") if m.strip()]
            total_area = cluster_snap.block_area_ha
        else:
            members = [block_names_by_id.get(group_id, group_id)]
            total_area = block_area_by_id.get(group_id, 0.0)

        application_count = len(rows)
        events_count = sum(
            len(b.applications) if b.applications else 1
            for b in artifact.blends if b.block_id == group_id
        )

        groups.append({
            "letter": letter,
            "group_id": group_id,
            "members": members,
            "block_count": len(members),
            "total_area_ha": total_area,
            "application_count": application_count,
            "events_count": events_count,
            "days": days,
        })

    # Strip internal-only fields.
    for g in groups:
        for d in g["days"]:
            for a in d["applications"]:
                a.pop("sort_key", None)

    # Calendar strip — use all rows across all groups, in date order.
    all_rows: list[dict[str, Any]] = []
    for g in groups:
        for d in g["days"]:
            all_rows.extend(d["applications"])
    calendar = _walkthrough_calendar_strip(all_rows)

    apps = sum(g["application_count"] for g in groups)
    n_groups = len(groups)
    n_blocks = sum(g["block_count"] for g in groups)
    total_ha = sum(g["total_area_ha"] for g in groups)
    crop = artifact.header.crop.lower() if artifact.header.crop else "the crop"
    if n_groups > 1:
        intro = (
            f"Across the season you'll do {apps} fertilizer application{'s' if apps != 1 else ''} "
            f"across {n_groups} groups ({n_blocks} blocks, {total_ha:.1f} ha) of {crop}. "
            f"Each group has its own programme — laid out below in calendar order, "
            "with paired-pass days clearly marked."
        )
    else:
        intro = (
            f"Across the season you'll do {apps} fertilizer application{'s' if apps != 1 else ''}"
            + (f" across {n_blocks} block{'s' if n_blocks != 1 else ''} ({total_ha:.1f} ha total)" if n_blocks else "")
            + f" of {crop}. Each one is laid out below in calendar order — "
            "what to apply, where, how, and why."
        )

    return {
        "intro": intro,
        "calendar_strip": calendar,
        "groups": groups,
        # Perennials get a generic "Week X" — anchoring to a planting
        # event makes no sense in a mature orchard. Annuals keep the
        # explicit "Week X from planting" label.
        "is_perennial": _is_perennial(artifact.header.crop),
    }


def _walkthrough_row(
    blend: Blend,
    application_event: Any,
    block_names_by_id: dict[str, str],
    block_area_by_id: dict[str, float],
) -> dict[str, Any]:
    """Single application card. `application_event` is None for legacy
    blends without per-event records — we fall back to dates_label."""
    if application_event is not None:
        date_full, date_short, month_label = _format_application_date(application_event.event_date)
        sort_key = application_event.event_date.isoformat() if hasattr(application_event.event_date, "isoformat") else str(application_event.event_date)
        week = getattr(application_event, "week_from_planting", None)
    else:
        date_full = blend.dates_label or ""
        date_short = date_full
        month_label = ""
        sort_key = ""
        week = None

    method_action = _METHOD_ACTION.get(
        blend.method.kind.name,
        {"verb": "Apply", "placement": "Apply through the standard farm route."},
    )
    formula = _blend_formula_string(blend)
    rate_per_event = _blend_combined_rate_per_event(blend)
    block_name = block_names_by_id.get(blend.block_id, blend.block_id)
    area_ha = block_area_by_id.get(blend.block_id, 0.0)
    total_kg = rate_per_event * area_ha if rate_per_event and area_ha else 0.0

    if blend.method.kind.name == "FOLIAR":
        action_headline = (
            f"{method_action['verb']} a foliar correction at the recommended rate"
        )
    elif formula and rate_per_event:
        action_headline = f"{method_action['verb']} {formula} at {rate_per_event:.0f} kg/ha"
    elif rate_per_event:
        action_headline = f"{method_action['verb']} the blend at {rate_per_event:.0f} kg/ha"
    else:
        action_headline = f"{method_action['verb']} the {blend.stage_name} blend"

    stage_exp = _stage_explanation(blend.stage_name)
    block_summary_parts: list[str] = []
    if blend.block_id.startswith("cluster_"):
        block_summary_parts.append(f"Group {blend.block_id.replace('cluster_', '')}")
    if area_ha:
        block_summary_parts.append(f"{area_ha:.1f} ha")
    block_summary_parts.append(block_name)
    block_summary = " · ".join(block_summary_parts)

    nutrient_chips = []
    for nut, val in _ordered_nutrients(blend.nutrients_delivered or {}):
        # Trace micros displayed as g/ha.
        if val < 1.0 and nut in ("Zn", "B", "Mn", "Fe", "Cu", "Mo"):
            chip_value = f"{val * 1000:.0f} g"
        else:
            chip_value = f"{val:.1f} kg"
        nutrient_chips.append({"label": _nutrient_pretty(nut), "value": chip_value})

    return {
        "_blend_id": id(blend),
        "sort_key": sort_key,
        "block_id": blend.block_id,
        "date_full": date_full,
        "date_short": date_short,
        "month_label": month_label,
        "week_from_planting": week,
        "action_headline": action_headline,
        "method_label": _method_short_label(blend.method),
        "method_placement": method_action["placement"],
        "formula": formula,
        "rate_per_ha_kg": rate_per_event,
        "block_summary": block_summary,
        "block_name": block_name,
        "area_ha": area_ha,
        "total_kg": total_kg,
        "stage_name": blend.stage_name or "",
        "stage_explanation": stage_exp,
        "why_brief": _walkthrough_brief(blend, stage_exp, block_summary),
        "nutrient_chips": nutrient_chips,
        "is_split": False,
        "split_partners": [],
        "split_reason": "",
    }


def _walkthrough_calendar_strip(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compact 'X applications in May, Y in Jun, …' summary so the
    farmer sees the season's load distribution at a glance before
    diving into the cards."""
    if not rows:
        return []
    counts: dict[str, int] = {}
    order: list[str] = []
    for r in rows:
        m = r.get("month_label") or "Unscheduled"
        if m not in counts:
            order.append(m)
        counts[m] = counts.get(m, 0) + 1
    return [{"month": m, "count": counts[m]} for m in order]


def _blend_view(blend: Blend) -> dict[str, Any]:
    formula = _blend_formula_string(blend)
    rate_per_event = _blend_combined_rate_per_event(blend)
    rate_per_stage = _blend_combined_rate_per_stage(blend)
    return {
        "stage_number": blend.stage_number,
        "stage_name": blend.stage_name,
        "method_label": _method_short_label(blend.method),
        "is_liquid": blend.method.kind.name.startswith("LIQUID_"),
        "weeks": blend.weeks,
        "events": blend.events,
        "dates_label": blend.dates_label,
        # Combined SA-notation formula (e.g. "2:3:2 (22) + Ca 2.2% + S 0.7%")
        # so the headline reads as a single grower-recognised product
        # rather than a stack of raw-material analysis lines.
        "combined_formula": formula,
        # Total per-event / per-stage kg/ha across all parts of the blend.
        # Drives the headline "{formula} at {rate} kg/ha" line.
        "rate_per_event_kg_ha": rate_per_event,
        "rate_per_stage_kg_ha": rate_per_stage,
        # Raw products kept for admin-mode rendering. Client mode hides
        # them; the combined formula + per-ha delivery is the deliverable.
        "raw_products": [_part_view(p) for p in blend.raw_products],
        "applications": [
            {
                "date_formatted": a.event_date.strftime("%-d %b %Y"),
                "week_from_planting": a.week_from_planting,
            }
            for a in blend.applications
        ],
        "nutrients_delivered": _ordered_nutrients(blend.nutrients_delivered),
    }


def _part_view(part: BlendPart) -> dict[str, Any]:
    """Client-mode product label: nutrient analysis only, never raw name."""
    return {
        "display_label": _display_product_label(part),
        "stream": part.stream,
        "rate_per_event_per_ha": part.rate_per_event_per_ha,
        "rate_per_stage_per_ha": part.rate_per_stage_per_ha,
        "batch_total": part.batch_total,
    }


def _display_product_label(part: BlendPart) -> str:
    """Client-mode product display: ONLY the nutrient analysis string,
    never the raw `part.product` material name. Mirrors the rule in
    `renderer._display_product`."""
    analysis = (part.analysis or "").strip()
    lower = analysis.lower()
    if not analysis or lower in {"—", "-", "n/a", "none"} or "not specified" in lower:
        return "nutrient blend"
    return f"{analysis} source"


# ── SA-notation formula computation ─────────────────────────────────
#
# The agronomist sees a blend as a single SA-grower-recognised string —
# "2:3:2 (22)" or "10:5:20" — not a list of raw-material analyses. The
# combined formula is computed from the per-event kg of every part:
# total mass per ha across parts, then NPK%, then scale to a peak-15
# integer ratio (the convention SA growers read fluently).
#
# When NPK is trivial (Ca/S corrective blends), we drop the X:Y:Z form
# and lead with secondaries — "Ca 10.3% + S 7.4%" reads correctly while
# "0:0:0 (3) + Ca 10.3%" doesn't.


# Threshold for "is this an NPK-dominant blend?" — sum of N% + P₂O₅% +
# K₂O% in the combined formulation. Below this, secondaries lead.
_NPK_DOMINANT_THRESHOLD_PCT = 5.0


def _parse_kg_per_ha(label: str | None) -> float:
    """Pull a kg/ha figure out of strings like "210 kg" or "1 500 kg/ha".
    Returns 0 if no number found. Handles SA thin-space digit groupings.
    """
    if not label:
        return 0.0
    # Drop everything after the first unit word — "kg", "L", "g".
    s = re.split(r"\s*(?:kg|l|g)\b", label, flags=re.IGNORECASE)[0]
    # Compact thin-spaces / regular spaces inside numbers ("1 500" → "1500").
    s = re.sub(r"(?<=\d)[\s  ](?=\d)", "", s)
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if not m:
        return 0.0
    try:
        return float(m.group(0))
    except ValueError:
        return 0.0


def _blend_combined_rate_per_event(blend: Blend) -> float:
    """Sum of per-event kg/ha across all parts. Liquid blends use whatever
    the engine recorded as solute equivalent — the renderer treats the
    sum the same way."""
    return sum(_parse_kg_per_ha(p.rate_per_event_per_ha) for p in blend.raw_products)


def _blend_combined_rate_per_stage(blend: Blend) -> float:
    return sum(_parse_kg_per_ha(p.rate_per_stage_per_ha) for p in blend.raw_products)


def _parse_analysis_pct(analysis: str, nutrient: str) -> float:
    """Pull "{nutrient} X%" from analysis strings like
    "N 2.1%, P 1.0%, K 1.6%, Ca 2.2%, Mg 1.0%, S 0.7%". Returns 0 if
    not present.

    Recognises three forms for the same nutrient:
      * Bare letter — `P 1.0%` / `K 1.6%` (current convention; P / K
        labels carry the oxide-form percentage by SA grower
        agreement)
      * ASCII oxide — `P2O5 1.0%` / `K2O 1.6%` (legacy / explicit)
      * Subscripted oxide — `P₂O₅ 1.0%` / `K₂O 1.6%` (older renderer
        output)

    For non-P/K nutrients (`N`, `Ca`, `Mg`, `S`, `Zn`, etc.), only the
    plain code matches.
    """
    if not analysis:
        return 0.0
    forms: list[str] = []
    if nutrient == "P2O5":
        forms = ["P2O5", "P₂O₅", "P"]
    elif nutrient == "K2O":
        forms = ["K2O", "K₂O", "K"]
    else:
        forms = [nutrient]
    for form in forms:
        # Word-boundary on the leading edge keeps `P` from matching the
        # `P` inside `P2O5` or `P₂O₅`. The trailing whitespace handles
        # both spaces and non-breaking spaces.
        pattern = rf"(?:^|[^A-Za-z0-9₂₅]){re.escape(form)}(?![A-Za-z0-9₂₅])\s+([0-9]+(?:\.[0-9]+)?)\s*%"
        m = re.search(pattern, analysis)
        if m is not None:
            try:
                return float(m.group(1))
            except ValueError:
                return 0.0
    return 0.0


def _format_secondary_pct(nutrient: str, pct: float) -> str:
    """`Ca 23.0%` style string for the formula tail. No subscripts —
    Ca / Mg / S are single-letter labels."""
    return f"{nutrient} {pct:.1f}%"


def _blend_formula_string(blend: Blend) -> str:
    """Combined SA-notation formula across all parts of the blend, e.g.
    "2:3:2 (22) + Ca 2.2% + S 0.7%". Returns "" when the blend doesn't
    have enough info to compute (legacy artifacts without parts, or
    foliar / fulvic-only cases where total mass is zero).

    Method: weight each part's nutrient % by its mass per ha, sum across
    parts to get combined nutrient kg/ha, then divide by total mass to
    get the blend's effective % for each nutrient. Scale N:P₂O₅:K₂O so
    the peak hits 15 (SA grower convention — e.g. 15:1:5 instead of
    15.2:0.8:5.0). Append secondaries that exceed 0.1%.

    For Ca/S/Mg-corrective blends where NPK is trivial (sum < ~5%), the
    SA-notation reads as nonsense ("0:0:0 (3) + Ca 10%") so we drop the
    NPK head and lead with secondaries instead.
    """
    if blend.method.kind.name == "FOLIAR":
        return ""
    parts = list(blend.raw_products)
    if not parts:
        return ""
    total_mass = 0.0
    nutrient_kg: dict[str, float] = {}
    nutrients = ("N", "P2O5", "K2O", "Ca", "Mg", "S")
    for part in parts:
        kg = _parse_kg_per_ha(part.rate_per_event_per_ha)
        if kg <= 0:
            kg = _parse_kg_per_ha(part.rate_per_stage_per_ha)
        if kg <= 0:
            continue
        total_mass += kg
        analysis = part.analysis or ""
        for nut in nutrients:
            pct = _parse_analysis_pct(analysis, nut)
            if pct > 0:
                nutrient_kg[nut] = nutrient_kg.get(nut, 0.0) + kg * pct / 100.0
    if total_mass <= 0:
        return ""
    pct_of = {nut: (kg / total_mass) * 100.0 for nut, kg in nutrient_kg.items()}
    n_pct = pct_of.get("N", 0.0)
    p_pct = pct_of.get("P2O5", 0.0)
    k_pct = pct_of.get("K2O", 0.0)
    npk_sum = n_pct + p_pct + k_pct
    secondaries = [
        _format_secondary_pct(nut, pct_of.get(nut, 0.0))
        for nut in ("Ca", "Mg", "S")
        if pct_of.get(nut, 0.0) >= 0.1
    ]
    if npk_sum < _NPK_DOMINANT_THRESHOLD_PCT:
        # Secondary-dominant: NPK is trivial. Lead with the secondaries
        # so the formula reads as the correction it is.
        return " + ".join(secondaries) if secondaries else ""
    peak = max(n_pct, p_pct, k_pct)
    scale = 15 / peak if peak > 0 else 0
    n_int = max(0, round(n_pct * scale))
    p_int = max(0, round(p_pct * scale))
    k_int = max(0, round(k_pct * scale))
    head = f"{n_int}:{p_int}:{k_int} ({npk_sum:.0f})"
    if secondaries:
        return head + " + " + " + ".join(secondaries)
    return head


def _method_short_label(method: ApplicationMethod) -> str:
    """Short method label for the per-pass row in the PDF.

    The method selector currently picks LIQUID_DRIP as the canonical
    fertigation kind whenever ANY liquid method is available — drip
    isn't actually distinct from pivot/sprinkler/micro in the engine's
    decision today. Labelling everything "Fertigation (drip)" misled
    farmers with non-drip irrigation; using a generic "Fertigation"
    label until the selector actually differentiates fixes the lie
    without forcing a method-selector rewrite.
    """
    kind_name = method.kind.name
    return {
        "LIQUID_DRIP": "Fertigation",
        "LIQUID_PIVOT": "Fertigation (pivot)",
        "LIQUID_SPRINKLER": "Fertigation (sprinkler)",
        "DRY_BROADCAST": "Dry broadcast",
        "DRY_BAND": "Dry band",
        "DRY_BASAL": "Dry basal",
        "FOLIAR": "Foliar",
    }.get(kind_name, kind_name.replace("_", " ").title())


def _ordered_nutrients(delivered: dict[str, float]) -> list[tuple[str, float]]:
    """Return nutrient deliveries in canonical display order (macros first)."""
    order = ("N", "P2O5", "K2O", "Ca", "Mg", "S", "Zn", "B", "Mn", "Fe", "Cu", "Mo")
    out: list[tuple[str, float]] = []
    for nut in order:
        if nut in delivered and delivered[nut] > 0:
            out.append((nut, delivered[nut]))
    # Append any nutrients not in canonical order at the end
    seen = {nut for nut, _ in out}
    for nut, val in delivered.items():
        if nut not in seen and val > 0:
            out.append((nut, val))
    return out


def _build_foliar_context(artifact: ProgrammeArtifact) -> list[dict[str, Any]]:
    """Foliar events grouped by application-group letter so the
    template can render Group A's foliar plan separate from Group B's
    rather than a flat farm-wide table that hides which block gets
    what. Singletons (no clustering) collapse to one "Group A".
    """
    if not artifact.foliar_events:
        return []

    # Build block_id → group_letter from the cluster snapshots. Each
    # cluster snapshot's block_name is a comma-joined member list of
    # block names; we walk the individual snapshots to map their ids.
    block_to_group: dict[str, str] = {}
    for snap in artifact.soil_snapshots:
        if not snap.block_id.startswith("cluster_"):
            continue
        letter = snap.block_id.replace("cluster_", "").upper()
        # Cluster-keyed foliar events (foliar.block_id = "cluster_C")
        # must also resolve to the letter — otherwise the renderer
        # falls through to "Group ?" because foliar's block_id never
        # appears as an individual snapshot key.
        block_to_group[snap.block_id] = letter
        members = [m.strip() for m in (snap.block_name or "").split(",") if m.strip()]
        for member_label in members:
            for indiv in artifact.soil_snapshots:
                if indiv.block_id.startswith("cluster_"):
                    continue
                # Match on block_name prefix — labs often label blocks
                # as "Blok 100" but cluster member lists store the same
                # name (or the leading token of a fuller display name).
                if indiv.block_name == member_label or indiv.block_name.startswith(member_label):
                    block_to_group[indiv.block_id] = letter
    # Singletons (no cluster) get sequential letters in artifact order
    # so a single-block programme reads as Group A.
    if not block_to_group:
        for i, snap in enumerate(
            s for s in artifact.soil_snapshots if not s.block_id.startswith("cluster_")
        ):
            block_to_group[snap.block_id] = chr(ord("A") + i)

    name_by_id = {s.block_id: s.block_name for s in artifact.soil_snapshots}

    grouped: dict[str, list[dict[str, Any]]] = {}
    for f in artifact.foliar_events:
        letter = block_to_group.get(f.block_id, "?")
        grouped.setdefault(letter, []).append({
            "event_number": f.event_number,
            "week": f.week,
            "stage_name": f.stage_name,
            "analysis": f.analysis,
            "rate_per_ha": f.rate_per_ha,
            "block_name": name_by_id.get(f.block_id, f.block_id),
            "trigger_reason": _strip_source_refs(f.trigger_reason),
        })
    # Order events within each group by week, then stable on block_name.
    for events in grouped.values():
        events.sort(key=lambda e: (e["week"] if e["week"] is not None else 999, e["block_name"]))
    return [
        {
            "letter": letter,
            "events": events,
            "event_count": len(events),
        }
        for letter, events in sorted(grouped.items())
    ]


def _build_nutrient_balance_context(
    artifact: ProgrammeArtifact,
) -> list[dict[str, str]]:
    """Per-nutrient applied totals computed from the actual blend
    delivery — `nutrients_delivered` (kg/ha · per event) × event count
    × area. This is what the farmer actually receives, not the engine's
    pre-adjustment season target.

    Earlier this section read from `artifact.block_totals`, which
    carries the engine's TARGET dict (only what target_computation
    surfaced as a per-nutrient demand) — Ca/Mg amendment passes were
    invisible there because they're delivered by side-pass blends, not
    by the season-target accumulator. Switching the source to
    `artifact.blends` makes the report match what's on the calendar.

    Cluster snapshots carry the area for every blend keyed to a
    `cluster_X` block_id; singleton (un-clustered) blends use the
    individual block's area. Whole-farm per-ha total = total kg
    delivered across the farm ÷ sum of source-block areas.
    """
    if not artifact.blends:
        return []

    # Area per block_id — clusters carry their own (sum of members),
    # singletons carry their block's. Either way, blend × area gives
    # the kg delivered for that blend pass.
    area_by_block_id: dict[str, float] = {
        s.block_id: s.block_area_ha for s in artifact.soil_snapshots
    }

    # Whole-farm area is the sum of source-block areas (cluster
    # snapshots already aggregate so summing both would double-count;
    # we sum only the source rows).
    farm_area = sum(
        s.block_area_ha for s in artifact.soil_snapshots
        if not s.block_id.startswith("cluster_")
    ) or 1.0

    delivered_kg: dict[str, float] = {}
    for blend in artifact.blends:
        area = area_by_block_id.get(blend.block_id, 0.0)
        if area <= 0:
            continue
        events = len(blend.applications) if blend.applications else 1
        for nut, kg_per_ha_per_event in (blend.nutrients_delivered or {}).items():
            delivered_kg[nut] = delivered_kg.get(nut, 0.0) + kg_per_ha_per_event * events * area

    rows = []
    for nut in ("N", "P2O5", "K2O", "Ca", "Mg", "S", "Zn", "B", "Mn"):
        if nut not in delivered_kg:
            continue
        per_ha = delivered_kg[nut] / farm_area
        if per_ha < 1.0 and nut in ("Zn", "B", "Mn", "Fe", "Cu"):
            applied = f"~{per_ha * 1000:.0f} g"
        else:
            applied = f"~{per_ha:.0f} kg"
        rows.append({
            "label": _nutrient_long_name(nut),
            "applied": applied,
        })
    return rows


def _nutrient_long_name(nut: str) -> str:
    return {
        "N": "Nitrogen", "P2O5": "Phosphorus", "K2O": "Potassium",
        "Ca": "Calcium", "Mg": "Magnesium", "S": "Sulphur",
        "Zn": "Zinc", "B": "Boron", "Mn": "Manganese",
        "Fe": "Iron", "Cu": "Copper", "Mo": "Molybdenum",
    }.get(nut, nut)


def _build_ratios_context(artifact: ProgrammeArtifact) -> list[dict[str, str]]:
    """One row per computed ratio across all blocks. v1: just lists what
    the engine computed; status logic refined post-demo."""
    if not artifact.soil_snapshots:
        return []
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for snap in artifact.soil_snapshots:
        for key, val in (snap.computed_ratios or {}).items():
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "label": _ratio_display_label(key),
                "current": _format_ratio_value(key, val),
                "target": _ratio_target(key),
                "status": "",
                "status_class": "soft",
            })
    return rows


def _ratio_display_label(key: str) -> str:
    return {
        "Ca:Mg": "Ca : Mg",
        "(Ca+Mg):K": "(Ca + Mg) : K",
        "Mg:K": "Mg : K",
        "soil_ESP_pct": "Sodium saturation",
        "SAR": "SAR",
        "Al_saturation_pct": "Acid saturation",
        "P:Zn": "P : Zn",
        "Ca:B": "Ca : B",
        "C:N": "C : N",
    }.get(key, key)


def _format_ratio_value(key: str, val: float) -> str:
    if "_pct" in key or "saturation" in key.lower():
        return f"{val:.1f} %"
    if ":" in key:
        return f"{val:.1f} : 1"
    return f"{val:.2f}"


def _ratio_target(key: str) -> str:
    return {
        "Ca:Mg": "3-5 : 1",
        "(Ca+Mg):K": "20-30 : 1",
        "Mg:K": "2-4 : 1",
        "soil_ESP_pct": "< 5 %",
        "SAR": "< 3",
        "Al_saturation_pct": "< 10 %",
    }.get(key, "—")


_PERENNIAL_CROP_PATTERNS = (
    "macadamia", "citrus", "avocado", "pecan", "mango",
    "guava", "lucerne", "banana", "pineapple", "rooibos",
    "apple", "pear", "peach", "plum", "grape",
)


def _is_perennial(crop: Optional[str]) -> bool:
    """Heuristic crop-type check used by the renderer wherever the
    perennial / annual distinction changes copy. Pure name match — the
    artifact doesn't carry a crop_type field today."""
    if not crop:
        return False
    lower = crop.lower()
    return any(p in lower for p in _PERENNIAL_CROP_PATTERNS)


def _build_year_outlook_context(artifact: ProgrammeArtifact) -> list[dict[str, Any]]:
    """Multi-year cards. For perennials only.

    Two narrative tracks based on orchard maturity:

      * NEW PLANTINGS (avg block tree_age < 4) — "establishment →
        first full bearing → productive stand". Standard new-orchard
        progression where Year 1 is about getting the trees set up
        and Year 2/3 is about ramping into yield.

      * MATURE ORCHARDS (avg tree_age ≥ 4) — "this season → Year 2
        outlook → Year 3 maintenance trajectory". The orchard is
        already producing; the multi-year frame is about the
        trajectory of soil-side corrections (lime build, Mg lift, K
        drawdown) rather than orchard establishment.

    Tree age comes from the BlockInput rows that fed the artifact —
    not directly on the artifact today, so we infer maturity from the
    soil snapshots' block names where the engine can't tell us
    otherwise. For annuals, no outlook section.
    """
    if not _is_perennial(artifact.header.crop):
        return []

    # Maturity heuristic — average tree_age across blocks if any block
    # carries it, otherwise fall back to "mature" for any perennial
    # programme with non-zero block area (production farms vs new
    # plantings is roughly 90/10 in real usage). When the engine
    # eventually persists block tree_age onto the artifact this
    # heuristic upgrades to a real read.
    is_mature = _infer_orchard_is_mature(artifact)

    if is_mature:
        return [
            {
                "label": "This season",
                "title": "Soil-side corrections in motion",
                "bullets": [
                    "Pre-season lime / gypsum / dolomitic actions move soil "
                    "chemistry in the right direction across Year 1, but most "
                    "won't fully reflect in leaf or kernel until Year 2.",
                    "In-season programme delivers the season's nutrient "
                    "targets while the soil-side corrections work in the "
                    "background.",
                ],
            },
            {
                "label": "Year 2 outlook",
                "title": "Where the soil should be",
                "bullets": [
                    "Soil re-test mid-Year-2 to confirm pH / Ca / Mg movement "
                    "from this season's amendments.",
                    "Per-block rates revisited based on the re-test — blocks "
                    "still trending wrong direction get a second pass; blocks "
                    "that hit target shift to maintenance rates.",
                    "Leaf analysis at flowering becomes the primary feedback "
                    "loop once soil corrections are settled.",
                ],
            },
            {
                "label": "Year 3+",
                "title": "Maintenance trajectory",
                "bullets": [
                    "Soil corrections largely complete — annual maintenance "
                    "lime / gypsum + leaf-driven foliar plan.",
                    "Programme stabilises around the orchard's productive "
                    "rhythm; biggest variations come from yield carry-over "
                    "and seasonal weather rather than soil-chemistry shifts.",
                ],
            },
        ]

    # New plantings — original establishment progression.
    return [
        {
            "label": "Year 1",
            "title": "Establishment",
            "bullets": [
                "Programme delivers the season's nutrient targets via the "
                "applications above.",
                "Soil re-test in autumn closes the loop and informs Year 2 "
                "adjustments.",
            ],
        },
        {
            "label": "Year 2",
            "title": "First full bearing season",
            "bullets": [
                "Yield expectations climb as the orchard / stand matures.",
                "Soil re-test directs any rate adjustments — phosphorus + "
                "potassium top-ups against measured drawdown.",
            ],
        },
        {
            "label": "Year 3+",
            "title": "Productive stand",
            "bullets": [
                "Annual repeat of the organic-anchored programme builds soil "
                "carbon and carrying capacity.",
                "Foliar adjustments fine-tune year-over-year as leaf-analysis "
                "data accumulates.",
            ],
        },
    ]


def _infer_orchard_is_mature(artifact: ProgrammeArtifact) -> bool:
    """Heuristic: a perennial programme is treated as mature when the
    artifact carries any signal of an established orchard.

    Signals checked, in priority order:
      1. Risk flags / outstanding items mentioning "mature blocks"
         or yield targets ≥ 1.5 t/ha NIS — strong production signals.
      2. block_names hinting at established orchards (e.g. naming
         conventions like "Beaumont mature" or "9 jaar"; SA growers
         often label blocks with the cultivar age).
      3. Default to mature for any perennial programme — new
         plantings are the exception in real customer data, not the
         norm. False positives bias toward the maintenance-trajectory
         narrative which is also broadly applicable to mid-life stand.

    When the engine persists per-block tree_age / planting_date onto
    the artifact this lookup will tighten — for now the heuristic
    avoids the worst case (a Loskop production orchard reading as
    "Year 1 establishment" when it's been bearing for 9 years).
    """
    # Signal 1 — explicit mature mention in narrative fields.
    text_blob = " ".join(
        [a.message for a in artifact.risk_flags]
        + [a.item for a in artifact.outstanding_items]
        + [a.why_it_matters for a in artifact.outstanding_items]
    ).lower()
    if "mature" in text_blob or "bearing" in text_blob or "established" in text_blob:
        return True
    # Signal 2 — block-name hints. SA macadamia growers often write the
    # tree age into the block label ("A4 9 jaar", "Beaumont mature").
    for s in artifact.soil_snapshots:
        name = (s.block_name or "").lower()
        if any(k in name for k in ("mature", "jaar", "bearing", "established")):
            return True
        # "9-year-old" style or numeric age "9 jaar / 12 jaar"
        if re.search(r"\b(\d+)\s*(?:jaar|year|yr)s?\b", name):
            return True
    # Signal 3 — default to mature on perennials. Most customer
    # programmes are on existing orchards.
    return True


def _build_carrying_items_context(artifact: ProgrammeArtifact) -> list[dict[str, str]]:
    """Unified 'Items We're Carrying' list.

    Merges risk flags, outstanding items, and assumptions into ONE
    severity-banded list, deduplicated. Returns a list of dicts with:
        - band: "act_now" | "watch" | "filled_in"
        - band_label: human-readable banner ("Act before the season",
          "Watch through the season", "Filled in by Sapling — override
          if you have better data")
        - title: short heading
        - body: detail paragraph
        - action: optional what-to-do clause
        - severity: original severity (critical|warn|watch|info|fyi)
        - kind: source bucket (for the audit trail in the artifact)

    Deduplication heuristic: when a risk_flag and an outstanding_item
    share a strong noun phrase (e.g. "lime application", "irrigation
    water"), the outstanding_item wins because it carries the action
    + impact-if-skipped that the risk_flag lacks. Otherwise both keep
    their slot. This catches the very common "engine raises a flag
    AND queues a follow-up about the same gap" duplication without
    requiring a brittle exact-match key.

    Severity → band mapping:
        critical, warn  → "Act before the season"
        watch, info     → "Watch through the season"
        (assumptions)   → "Filled in by Sapling"
    """
    severity_order = {"critical": 0, "warn": 1, "watch": 2, "info": 3, "fyi": 4}

    # ----- 1. Detect overlap between risk_flags and outstanding_items.
    # Each outstanding_item carries an `item` heading; use its lower-
    # cased keyword set to match against risk_flag messages. When a
    # match scores ≥ 2 noun overlaps, we drop the risk_flag and keep
    # only the outstanding_item (more action-oriented).
    def _key_terms(text: str) -> set[str]:
        # Strip non-alphanumeric, lowercase, drop short tokens.
        import re as _re
        return {
            t for t in _re.split(r"[^A-Za-z0-9]+", (text or "").lower())
            if len(t) >= 4
        }

    outstanding_keysets = [
        (_key_terms(o.item) | _key_terms(o.why_it_matters), o)
        for o in artifact.outstanding_items
    ]

    items: list[dict[str, Any]] = []

    # ----- 2. Risk flags (filter dupes against outstanding) -----
    for f in artifact.risk_flags:
        flag_keys = _key_terms(f.message)
        is_dup = False
        for o_keys, _o in outstanding_keysets:
            # Threshold of 2 shared content tokens is empirically the
            # sweet spot — single shared word fires too often (every
            # two items mention "soil" or "block"); three drops genuine
            # near-dupes like the lime / pH pairing where overlap is
            # "lime/Lime + apply/application".
            if len(flag_keys & o_keys) >= 2:
                is_dup = True
                break
        if is_dup:
            continue
        sev = f.severity if f.severity in severity_order else "watch"
        band = "act_now" if sev in ("critical", "warn") else "watch"
        items.append({
            "band": band,
            "title": _flag_title_from_message(f.message),
            "body": _strip_source_refs(f.message),
            "action": "",
            "severity": sev,
            "kind": "risk_flag",
        })

    # ----- 3. Outstanding items (always kept) -----
    URGENT_PHRASES = (
        "too late",
        "no time to",
        "before the season starts",
        "insufficient for this season",
        "this season for full",
        "lost opportunity",
    )
    for o in artifact.outstanding_items:
        # Outstanding items don't carry an explicit severity. The most
        # reliable signal is the item-title phrasing — any "too late
        # this season for X" entry is genuinely act-now. Body-text
        # matching is too noisy ("missed deficiencies" tripped a false
        # positive on a Mid-season leaf-analysis recommendation).
        title_lower = (o.item or "").lower()
        body_lower = (o.why_it_matters or "").lower()
        is_urgent = any(
            term in title_lower or term in body_lower
            for term in URGENT_PHRASES
        )
        items.append({
            "band": "act_now" if is_urgent else "watch",
            "title": o.item,
            "body": _strip_source_refs(o.why_it_matters),
            "action": (
                _strip_source_refs(o.impact_if_skipped)
                if o.impact_if_skipped else ""
            ),
            "severity": "warn" if is_urgent else "watch",
            "kind": "outstanding",
        })

    # ----- 4. Assumptions (always the bottom band) -----
    for a in artifact.assumptions:
        items.append({
            "band": "filled_in",
            "title": a.field,
            "body": _strip_source_refs(a.assumed_value),
            "action": (
                _strip_source_refs(a.override_guidance) if a.override_guidance else ""
            ),
            "severity": "fyi",
            "kind": "assumption",
        })

    # ----- 5. Sort within bands by severity, then alphabetically -----
    band_order = {"act_now": 0, "watch": 1, "filled_in": 2}
    items.sort(key=lambda it: (
        band_order[it["band"]],
        severity_order.get(it["severity"], 99),
        it["title"].lower(),
    ))
    return items


def _flag_title_from_message(message: str) -> str:
    """Cheap title extraction — first clause of the message, ≤ 60 chars.
    Risk flag messages aren't structured so we synthesise a heading from
    the leading noun phrase."""
    first = (message or "").split("—")[0].split(".")[0].strip()
    if len(first) > 60:
        first = first[:57].rstrip() + "…"
    return first or "Watchpoint"


def _group_carrying_items_by_band(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group carrying items by band so the template can render one
    sub-heading per band followed by the items under it. Bands without
    any items are filtered out so we never render an empty heading."""
    band_meta = {
        "act_now": {
            "key": "act_now",
            "title": "Act before the season",
            "description": (
                "These need attention up front — either too late to "
                "fully resolve this cycle, or material risks the engine "
                "wants flagged."
            ),
        },
        "watch": {
            "key": "watch",
            "title": "Watch through the season",
            "description": (
                "Monitor these as the season progresses. Catch them on "
                "the next leaf or soil test, or on an in-season check-in."
            ),
        },
        "filled_in": {
            "key": "filled_in",
            "title": "Filled in by Sapling",
            "description": (
                "Defaults the engine applied where data was missing. "
                "Override on the next programme build if you have better "
                "values."
            ),
        },
    }
    out: list[dict[str, Any]] = []
    for band_key in ("act_now", "watch", "filled_in"):
        band_items = [it for it in items if it["band"] == band_key]
        if not band_items:
            continue
        meta = band_meta[band_key]
        out.append({
            "key": band_key,
            "title": meta["title"],
            "description": meta["description"],
            "items": band_items,
        })
    return out
