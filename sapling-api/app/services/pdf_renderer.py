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
from typing import Any
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
    """Render nutrient codes with proper subscripts: P2O5 → P₂O₅, K2O → K₂O."""
    return (
        symbol
        .replace("P2O5", "P₂O₅")
        .replace("K2O", "K₂O")
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
) -> bytes:
    """Render a ProgrammeArtifact as a styled Sapling-branded PDF.

    `mode="client"` (default) strips all source citations from prose
    per the disclosure-boundary rule. `mode="operator"` is reserved
    for Phase E (admin-triggered factory recipes).
    """
    if mode != "client":
        raise NotImplementedError(
            "Operator-mode PDF rendering is Phase E scope (admin-triggered, "
            "fertigation-only, factory recipes exposed). Not yet implemented."
        )

    context = _build_context(artifact)
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
# Context builder — maps ProgrammeArtifact to template variables
# ============================================================

def _build_context(artifact: ProgrammeArtifact) -> dict[str, Any]:
    header = _build_header_context(artifact)
    soil_snapshots = _build_soil_context(artifact)
    blends_by_block, block_names_by_id = _build_blends_context(artifact)
    foliar_events = _build_foliar_context(artifact)
    nutrient_balance = _build_nutrient_balance_context(artifact)
    ratios_rows = _build_ratios_context(artifact)
    year_outlook_cards = _build_year_outlook_context(artifact)
    risk_flags = _build_risk_flags_context(artifact)
    outstanding_items = _build_outstanding_context(artifact)
    assumptions = _build_assumptions_context(artifact)

    background_intro, glance_facts, soil_intro = _build_intro_prose(artifact)
    cover_subhead = _build_cover_subhead(artifact)

    contents_entries = _build_contents_entries(
        has_soil=bool(soil_snapshots),
        has_blends=bool(blends_by_block),
        has_foliar=bool(foliar_events),
        has_nutrient_balance=bool(nutrient_balance),
        has_ratios=bool(ratios_rows),
        has_year_outlook=bool(year_outlook_cards),
        has_items=bool(risk_flags or outstanding_items or assumptions),
    )

    return {
        "header": header,
        "cover_subhead": cover_subhead,
        "contents_entries": contents_entries,
        "background_intro": background_intro,
        "glance_facts": glance_facts,
        "soil_intro": soil_intro,
        "soil_snapshots": soil_snapshots,
        "blends_by_block": blends_by_block,
        "block_names_by_id": block_names_by_id,
        "foliar_events": foliar_events,
        "nutrient_balance": nutrient_balance,
        "ratios_rows": ratios_rows,
        "year_outlook_cards": year_outlook_cards,
        "risk_flags": risk_flags,
        "outstanding_items": outstanding_items,
        "assumptions": assumptions,
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
    n_blends = len(artifact.blends)
    if n_blends:
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
    has_blends: bool,
    has_foliar: bool,
    has_nutrient_balance: bool,
    has_ratios: bool,
    has_year_outlook: bool,
    has_items: bool,
) -> list[dict[str, Any]]:
    """Build the contents list, with page numbers estimated. Page numbers
    are coarse approximations — refined post-render when WeasyPrint's
    page-counting pass settles. For v1 we estimate: cover=1, contents=2,
    each section ≥ 1 page starting at p.3."""
    entries = [{"title": "Background", "page": 3}]
    page = 4
    if has_soil:
        entries.append({"title": "Reading of the Soil", "page": page})
        page += 1
    if has_blends:
        entries.append({"title": "Applications", "page": page})
        page += 2  # often 2+ pages
    if has_foliar:
        entries.append({"title": "Foliar Sprays", "page": page})
        page += 1
    if has_nutrient_balance:
        entries.append({"title": "Nutrient Balance", "page": page})
        page += 1
    if has_ratios:
        entries.append({"title": "Ratios — Where You Are and Where We're Heading", "page": page})
        page += 1
    if has_year_outlook:
        entries.append({"title": "Year 2 and Beyond", "page": page})
        page += 1
    if has_items:
        entries.append({"title": "Items We're Carrying Into The Season", "page": page})
    return entries


def _build_soil_context(artifact: ProgrammeArtifact) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for snap in artifact.soil_snapshots:
        sample_label_parts = []
        if snap.lab_name:
            sample_label_parts.append(snap.lab_name)
        if snap.sample_date:
            sample_label_parts.append(snap.sample_date.strftime("%b %Y"))
        out.append({
            "block_id": snap.block_id,
            "block_name": snap.block_name,
            "block_area_ha": snap.block_area_ha,
            "sample_label": " · ".join(sample_label_parts) if sample_label_parts else None,
            "headline_signals": [
                _strip_source_refs(s) for s in snap.headline_signals if s
            ],
        })
    return out


def _build_blends_context(
    artifact: ProgrammeArtifact,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    block_names_by_id = {
        s.block_id: s.block_name for s in artifact.soil_snapshots
    }
    blends_by_block: dict[str, list[dict[str, Any]]] = {}
    for blend in artifact.blends:
        bucket = blends_by_block.setdefault(blend.block_id, [])
        bucket.append(_blend_view(blend))
    return blends_by_block, block_names_by_id


def _blend_view(blend: Blend) -> dict[str, Any]:
    return {
        "stage_number": blend.stage_number,
        "stage_name": blend.stage_name,
        "method_label": _method_short_label(blend.method),
        "is_liquid": blend.method.kind.name.startswith("LIQUID_"),
        "weeks": blend.weeks,
        "events": blend.events,
        "dates_label": blend.dates_label,
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


def _method_short_label(method: ApplicationMethod) -> str:
    kind_name = method.kind.name
    return {
        "LIQUID_DRIP": "Fertigation (drip)",
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
    return [
        {
            "event_number": f.event_number,
            "week": f.week,
            "stage_name": f.stage_name,
            "analysis": f.analysis,
            "rate_per_ha": f.rate_per_ha,
            "trigger_reason": _strip_source_refs(f.trigger_reason),
        }
        for f in artifact.foliar_events
    ]


def _build_nutrient_balance_context(
    artifact: ProgrammeArtifact,
) -> list[dict[str, str]]:
    """Per-nutrient applied vs removed. For now uses block_totals as the
    'applied' figure; removed comes from artifact-level future work
    (target_computation surfaces removal). Returns [] if data missing."""
    if not artifact.block_totals:
        return []
    # Simple v1: aggregate across all blocks
    aggregated: dict[str, float] = {}
    n_blocks = max(1, len(artifact.block_totals))
    for block_id, totals in artifact.block_totals.items():
        for nut, kg in totals.items():
            aggregated[nut] = aggregated.get(nut, 0.0) + kg
    # Average per ha across blocks
    rows = []
    for nut in ("N", "P2O5", "K2O", "Ca", "Mg", "S"):
        if nut not in aggregated:
            continue
        per_block = aggregated[nut] / n_blocks
        rows.append({
            "label": _nutrient_long_name(nut),
            "applied": f"~{per_block:.0f} kg",
            "removed": "—",  # populated when removal data wired
            "net": "Carried this season",
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


def _build_year_outlook_context(artifact: ProgrammeArtifact) -> list[dict[str, Any]]:
    """Multi-year cards. For perennials only — fires when crop is a tree
    crop or pasture. v1: returns empty for annuals."""
    crop_lower = artifact.header.crop.lower()
    perennial_crops = ("macadamia", "citrus", "avocado", "pecan", "mango",
                        "guava", "lucerne", "banana", "pineapple", "rooibos",
                        "apple", "pear", "peach", "plum", "grape")
    if not any(p in crop_lower for p in perennial_crops):
        return []
    return [
        {
            "label": "Year 1",
            "title": "Establishment",
            "bullets": [
                f"Programme delivers the season's nutrient targets via the "
                f"applications above.",
                f"Soil re-test in autumn closes the loop and informs Year 2 "
                f"adjustments.",
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


def _build_risk_flags_context(artifact: ProgrammeArtifact) -> list[dict[str, str]]:
    severity_order = {"critical": 0, "warn": 1, "watch": 2, "info": 3}
    severity_label = {
        "critical": "Critical", "warn": "Watch closely",
        "watch": "Monitor", "info": "Note",
    }
    flags = sorted(
        artifact.risk_flags, key=lambda f: severity_order.get(f.severity, 99),
    )
    return [
        {
            "severity": f.severity,
            "severity_label": severity_label.get(f.severity, f.severity.title()),
            "message": _strip_source_refs(f.message),
        }
        for f in flags
    ]


def _build_outstanding_context(artifact: ProgrammeArtifact) -> list[dict[str, str]]:
    return [
        {
            "item": o.item,
            "why_it_matters": _strip_source_refs(o.why_it_matters),
            "impact_if_skipped": (
                _strip_source_refs(o.impact_if_skipped) if o.impact_if_skipped else ""
            ),
        }
        for o in artifact.outstanding_items
    ]


def _build_assumptions_context(artifact: ProgrammeArtifact) -> list[dict[str, str]]:
    return [
        {
            "field": a.field,
            "assumed_value": _strip_source_refs(a.assumed_value),
            "override_guidance": (
                _strip_source_refs(a.override_guidance) if a.override_guidance else ""
            ),
        }
        for a in artifact.assumptions
    ]
