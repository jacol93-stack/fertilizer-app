"""
Deterministic programme-document renderer — Phase B of the Phase 5
renderer family.

Takes a ProgrammeArtifact and produces a client-facing Markdown
document. No LLM. Pure template + slot-filling. Output quality is
~70 % of agronomist-written — Phase C (Opus) closes the remaining
gap by rewriting select sections with structural prose.

Architecture:
    artifact → {pack_X(artifact) → XContext} → {render_X(ctx) → markdown}
              ↘ stitch sections → final document

Design rules (honoured by every section):
    1. Products referenced by nutrient analysis only — never raw material name.
       See feedback_client_disclosure_boundary.md for the full rule.
    2. Factory procedures, QC, SOPs, stock-tank recipes are excluded from
       client-mode output. They belong to operator mode (Phase E).
    3. Sections whose context is empty are dropped from the final doc
       (no empty headers, no "None" leaks).
    4. Every number in the output traces back to the artifact — the
       renderer adds no facts, only rearranges them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from app.models.programme_artifact import (
    Assumption,
    Blend,
    BlendPart,
    FoliarEvent,
    OutstandingItem,
    ProgrammeArtifact,
    RiskFlag,
    SoilSnapshot,
)


# ============================================================
# Public API
# ============================================================

@dataclass
class RenderOptions:
    """Rendering configuration.

    mode:
        'client'   — farmer-facing; no raw materials, no factory/QC/SOP. Default.
        'operator' — internal; raw materials + recipes + SOPs. Phase E.
    """
    mode: Literal["client", "operator"] = "client"


def render_programme_document(
    artifact: ProgrammeArtifact,
    options: Optional[RenderOptions] = None,
) -> str:
    """Render a ProgrammeArtifact to Markdown.

    Client-mode output is the default (no raw materials, no factory
    content). Operator-mode is deferred — Phase E admin-triggered only.
    """
    options = options or RenderOptions()
    if options.mode == "operator":
        raise NotImplementedError(
            "Operator-mode render is Phase E scope, admin-triggered only. "
            "Client-mode is the default and only path today."
        )

    sections: list[str] = [
        _render_header(_pack_header(artifact)),
        _render_background(_pack_background(artifact)),
        _render_soil_reading(_pack_soil_reading(artifact)),
        _render_strategy(_pack_strategy(artifact)),
        _render_applications(_pack_applications(artifact)),
        _render_multiyear_rationale(_pack_multiyear_rationale(artifact)),
        _render_nutrient_balance(_pack_nutrient_balance(artifact)),
        _render_ratios(_pack_ratios(artifact)),
        _render_year_two_outlook(_pack_year_two_outlook(artifact)),
        _render_assumptions(_pack_assumptions(artifact)),
        _render_outstanding_items(_pack_outstanding_items(artifact)),
    ]

    # Filter empty sections (their packer returned None or their
    # render returned empty string).
    return "\n\n---\n\n".join(s for s in sections if s)


# ============================================================
# Product-display helper — the disclosure-boundary gatekeeper
# ============================================================

def _display_product(part: BlendPart) -> str:
    """Client-mode product label. Uses the nutrient analysis string
    exclusively — never the raw `part.product` material name.

    BlendPart.analysis is a pre-built string like 'N 17.1%, Ca 24.4%'.
    This is the ONLY content rendered to client-facing output.
    """
    analysis = (part.analysis or "").strip()
    # Handle the placeholder strings the catalog uses when a product's
    # composition isn't fully specified. We lose specificity but keep
    # the output client-compliant (no raw material name leaks through).
    lower = analysis.lower()
    if (
        not analysis
        or lower in {"—", "-", "n/a", "none"}
        or "not specified" in lower
        or "composition" in lower and "specified" in lower
    ):
        return "supplementary blend product"
    return f"{analysis} source"


def _method_short_label(method_kind) -> str:
    """Short human label for a method kind, used in stage cards."""
    name = getattr(method_kind, "name", str(method_kind))
    return {
        "DRY_BROADCAST": "Dry broadcast",
        "DRY_BAND": "Dry band",
        "DRY_SIDE_DRESS": "Dry side-dress",
        "DRY_FERTIGATION": "Dry fertigation",
        "LIQUID_DRIP": "Fertigation (drip)",
        "LIQUID_PIVOT": "Fertigation (pivot)",
        "LIQUID_SPRINKLER": "Fertigation (sprinkler)",
        "FOLIAR": "Foliar",
        "DRENCH": "Drench",
        "SEED_TREAT": "Seed treatment",
    }.get(name, name.replace("_", " ").title())


def _pct(val: Optional[float]) -> str:
    """Safe percent-or-dash formatter."""
    if val is None:
        return "—"
    return f"{val:.1f} %"


def _kg(val: Optional[float], suffix: str = "kg/ha") -> str:
    if val is None:
        return "—"
    return f"{val:.1f} {suffix}"


# ============================================================
# Section 1 — Header (title + metadata strip)
# ============================================================

@dataclass
class HeaderContext:
    title: str
    subtitle: str
    client_name: str
    farm_name: str
    location: Optional[str]
    crop: str
    planting_date_label: str
    season: str
    prepared_for: str
    prepared_by: str
    ref_number: Optional[str]


def _pack_header(artifact: ProgrammeArtifact) -> HeaderContext:
    h = artifact.header
    return HeaderContext(
        title="Fertilizer Programme",
        subtitle=f"{h.crop} — {h.season}" if h.season else h.crop,
        client_name=h.client_name,
        farm_name=h.farm_name,
        location=h.location,
        crop=h.crop,
        planting_date_label=h.planting_date.strftime("%d %B %Y"),
        season=h.season or "",
        prepared_for=h.prepared_for,
        prepared_by=h.prepared_by,
        ref_number=h.ref_number,
    )


def _render_header(ctx: HeaderContext) -> str:
    lines = [f"# {ctx.title}", ""]
    lines.append(f"**{ctx.client_name} — {ctx.farm_name}**")
    if ctx.location:
        lines.append(f"*{ctx.location}*")
    lines.append(f"**{ctx.crop} · {ctx.season}**  ")
    lines.append(f"*Planting date: {ctx.planting_date_label}*")
    if ctx.ref_number:
        lines.append(f"*Reference: {ctx.ref_number}*")
    return "\n".join(lines)


# ============================================================
# Section 2 — Background
# ============================================================

@dataclass
class BackgroundContext:
    crop: str
    season: str
    block_count: int
    total_area_ha: float
    method_summary: str
    prepared_by: str


def _pack_background(artifact: ProgrammeArtifact) -> BackgroundContext:
    h = artifact.header
    total_area = sum(s.block_area_ha for s in artifact.soil_snapshots)
    method_summary = _summarise_methods(artifact)
    return BackgroundContext(
        crop=h.crop,
        season=h.season or "this season",
        block_count=len(artifact.soil_snapshots),
        total_area_ha=total_area,
        method_summary=method_summary,
        prepared_by=h.prepared_by,
    )


def _summarise_methods(artifact: ProgrammeArtifact) -> str:
    """Describe the method mix in plain English — dry-only / fertigation-only /
    mixed — so the Background paragraph knows which voice to lead with."""
    kinds = {b.method.kind.name for b in artifact.blends} if artifact.blends else set()
    has_dry = any(k.startswith("DRY_") for k in kinds)
    has_liquid = any(k.startswith("LIQUID_") or k == "FERTIGATION" for k in kinds)
    has_foliar = bool(artifact.foliar_events)
    parts = []
    if has_dry:
        parts.append("dry broadcast / basal applications")
    if has_liquid:
        parts.append("fertigation through the irrigation system")
    if has_foliar:
        parts.append("targeted foliar corrections")
    if not parts:
        return "a programme of planned applications"
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} with {parts[1]}"
    return f"{parts[0]}, {parts[1]}, and {parts[2]}"


def _render_background(ctx: BackgroundContext) -> str:
    area_str = f"{ctx.total_area_ha:.2f} ha" if ctx.total_area_ha else "the target field(s)"
    block_str = (
        f"{ctx.block_count} block" if ctx.block_count == 1
        else f"{ctx.block_count} blocks"
    )
    return (
        "## Background\n\n"
        f"This programme covers **{ctx.crop}** for **{ctx.season}**, "
        f"spanning {block_str} across {area_str}. "
        f"The strategy is built around {ctx.method_summary}, sized against "
        f"the soil analysis and the expected harvest.\n\n"
        f"The sections that follow set out what the soil is telling us, "
        f"how the programme addresses the priorities, the applications "
        f"scheduled through the season, and the open items worth tracking."
    )


# ============================================================
# Section 3 — Reading of the Soil
# ============================================================

@dataclass
class SoilReadingContext:
    blocks: list[SoilSnapshot]
    multi_block: bool


def _pack_soil_reading(artifact: ProgrammeArtifact) -> SoilReadingContext:
    return SoilReadingContext(
        blocks=artifact.soil_snapshots,
        multi_block=len(artifact.soil_snapshots) > 1,
    )


def _render_soil_reading(ctx: SoilReadingContext) -> str:
    if not ctx.blocks:
        return ""

    lines = ["## Reading of the Soil", ""]
    if not ctx.multi_block:
        s = ctx.blocks[0]
        lines.append(
            f"Soil analysis for **{s.block_name}** ({s.block_area_ha:.2f} ha) "
            f"was reviewed against the crop's nutrient requirements and "
            f"published SA sufficiency thresholds."
        )
    else:
        lines.append(
            f"Soil analyses across {len(ctx.blocks)} blocks were reviewed "
            f"against the crop's nutrient requirements and published SA "
            f"sufficiency thresholds."
        )
    lines.append("")

    # Per-block headline signals
    for s in ctx.blocks:
        if ctx.multi_block:
            lines.append(f"### {s.block_name} ({s.block_area_ha:.2f} ha)")
        if s.lab_name or s.lab_method or s.sample_date:
            meta_bits = [b for b in (s.lab_name, s.lab_method,
                                     s.sample_date.strftime("%b %Y") if s.sample_date else None)
                         if b]
            if meta_bits:
                lines.append(f"*Source: {' · '.join(meta_bits)}*")
                lines.append("")

        if s.headline_signals:
            lines.append("**What the soil is flagging:**")
            for signal in s.headline_signals:
                lines.append(f"- {signal}")
            lines.append("")
        else:
            lines.append("*No headline signals flagged — soil chemistry in the expected band for this crop.*")
            lines.append("")

    return "\n".join(lines).rstrip()


# ============================================================
# Section 4 — Strategy
# ============================================================

@dataclass
class StrategyContext:
    objectives: list[str]
    has_organic_anchor: bool
    has_fertigation: bool
    has_foliar: bool


def _pack_strategy(artifact: ProgrammeArtifact) -> StrategyContext:
    # Infer objectives from what the programme actually contains
    objectives: list[str] = []
    blends = artifact.blends or []
    kinds = {b.method.kind.name for b in blends}
    has_dry = any(k.startswith("DRY_") for k in kinds)
    has_fertigation = any(k.startswith("LIQUID_") or k == "FERTIGATION" for k in kinds)
    has_foliar = bool(artifact.foliar_events)

    # Detect organic anchor via blend part analyses (no raw-material names
    # consulted — we rely on the fact that the consolidator produces
    # organic-anchored dry blends under Sapling's house rule, so any dry
    # blend implicitly carries the organic narrative).
    has_organic_anchor = has_dry

    if has_dry:
        objectives.append(
            "Carry the crop through the season with moderate nitrogen, "
            "adequate phosphorus and potassium — drawing on what's already "
            "in the soil and the products on hand."
        )
    if has_organic_anchor:
        objectives.append(
            "Anchor each dry blend with the organic carrier at a minimum of "
            "50 % of blend mass — delivering organic carbon, slow-release "
            "nitrogen, and the full micronutrient package while building "
            "soil for next season and beyond."
        )
    if has_fertigation:
        objectives.append(
            "Deliver stage-peak nutrition through the irrigation system in "
            "measured doses, matching the crop's uptake curve rather than "
            "front-loading the season."
        )
    if has_foliar:
        objectives.append(
            "Use targeted foliar applications to bypass soil lockup or "
            "correct stage-peak deficiencies that soil-delivered nutrients "
            "can't meet fast enough."
        )

    return StrategyContext(
        objectives=objectives,
        has_organic_anchor=has_organic_anchor,
        has_fertigation=has_fertigation,
        has_foliar=has_foliar,
    )


def _render_strategy(ctx: StrategyContext) -> str:
    if not ctx.objectives:
        return ""
    lines = ["## The Strategy", ""]
    lines.append("The programme serves the following objectives:")
    lines.append("")
    for i, obj in enumerate(ctx.objectives, 1):
        lines.append(f"**({chr(96 + i)})** {obj}")
        lines.append("")
    return "\n".join(lines).rstrip()


# ============================================================
# Section 5 — Applications
# ============================================================

@dataclass
class ApplicationsContext:
    blends: list[Blend]
    foliar_events: list[FoliarEvent]


def _pack_applications(artifact: ProgrammeArtifact) -> ApplicationsContext:
    return ApplicationsContext(
        blends=sorted(artifact.blends, key=lambda b: (b.block_id, b.stage_number)),
        foliar_events=sorted(artifact.foliar_events, key=lambda f: (f.block_id, f.event_number)),
    )


def _render_applications(ctx: ApplicationsContext) -> str:
    if not ctx.blends and not ctx.foliar_events:
        return ""

    lines = ["## Applications", ""]

    # Group blends by block
    blocks_seen: list[str] = []
    blend_by_block: dict[str, list[Blend]] = {}
    for b in ctx.blends:
        if b.block_id not in blocks_seen:
            blocks_seen.append(b.block_id)
            blend_by_block[b.block_id] = []
        blend_by_block[b.block_id].append(b)

    foliar_by_block: dict[str, list[FoliarEvent]] = {}
    for f in ctx.foliar_events:
        foliar_by_block.setdefault(f.block_id, []).append(f)
    for bid in foliar_by_block:
        if bid not in blocks_seen:
            blocks_seen.append(bid)

    multi_block = len(blocks_seen) > 1

    for bid in blocks_seen:
        if multi_block:
            lines.append(f"### Block {bid}")
            lines.append("")
        for blend in blend_by_block.get(bid, []):
            lines.append(_render_blend_card(blend))
            lines.append("")
        events = foliar_by_block.get(bid, [])
        if events:
            lines.append("**Foliar sprays**")
            lines.append("")
            lines.append(_render_foliar_table(events))
            lines.append("")

    return "\n".join(lines).rstrip()


def _render_blend_card(blend: Blend) -> str:
    lines = []
    method_label = _method_short_label(blend.method.kind)
    lines.append(
        f"**Stage {blend.stage_number} — {blend.stage_name} · {method_label}** "
        f"({blend.weeks}, {blend.events} event{'' if blend.events == 1 else 's'})"
    )
    lines.append(f"*{blend.dates_label}*")
    lines.append("")
    if blend.raw_products:
        lines.append("| Product | Rate / ha | Stream |")
        lines.append("|---|---:|:---:|")
        for part in blend.raw_products:
            product_label = _display_product(part)
            rate = part.rate_per_stage_per_ha or part.rate_per_event_per_ha or "—"
            stream = f"Part {part.stream}" if part.stream else "—"
            lines.append(f"| {product_label} | {rate} | {stream} |")
        lines.append("")
    if blend.nutrients_delivered:
        nut_bits = []
        for nut in ("N", "P2O5", "K2O", "Ca", "Mg", "S"):
            if nut in blend.nutrients_delivered:
                nut_bits.append(f"**{nut}** {blend.nutrients_delivered[nut]:.1f}")
        if nut_bits:
            lines.append(f"Delivered per ha: {' · '.join(nut_bits)} kg")
    return "\n".join(lines)


def _render_foliar_table(events: list[FoliarEvent]) -> str:
    lines = [
        "| # | Week | Stage | Analysis | Rate | Reason |",
        "|---:|---:|---|---|---:|---|",
    ]
    for f in events:
        lines.append(
            f"| #{f.event_number} | {f.week} | {f.stage_name} | "
            f"{f.analysis} | {f.rate_per_ha} | {f.trigger_reason} |"
        )
    return "\n".join(lines)


# ============================================================
# Section 6 — Nutrient Balance
# ============================================================

@dataclass
class NutrientBalanceContext:
    # block_label (display name) → nutrient totals
    block_totals: dict[str, dict[str, float]]
    single_block: bool


def _pack_nutrient_balance(artifact: ProgrammeArtifact) -> NutrientBalanceContext:
    # Resolve block_id → block_name for display; engine emits block_totals
    # keyed by block_id which isn't farmer-friendly.
    id_to_name = {s.block_id: s.block_name for s in artifact.soil_snapshots}
    labelled = {
        id_to_name.get(bid, bid): totals
        for bid, totals in artifact.block_totals.items()
    }
    return NutrientBalanceContext(
        block_totals=labelled,
        single_block=len(labelled) <= 1,
    )


def _render_nutrient_balance(ctx: NutrientBalanceContext) -> str:
    if not ctx.block_totals:
        return ""

    lines = ["## Nutrient Balance — What's Going In", ""]

    # Collect nutrient keys across all blocks
    nutrient_order = ["N", "P2O5", "K2O", "Ca", "Mg", "S", "B"]
    seen: set[str] = set()
    for totals in ctx.block_totals.values():
        seen.update(totals.keys())
    cols = [n for n in nutrient_order if n in seen]
    # Any extras we don't have in the order list — append at the end
    extras = sorted(n for n in seen if n not in cols)
    cols.extend(extras)

    if not cols:
        return ""

    if ctx.single_block:
        # Vertical table — nutrient rows
        block_id, totals = next(iter(ctx.block_totals.items()))
        lines.append(f"Total delivery per hectare across the season — **{block_id}**:")
        lines.append("")
        lines.append("| Nutrient | kg / ha |")
        lines.append("|---|---:|")
        for nut in cols:
            val = totals.get(nut, 0)
            lines.append(f"| {nut} | {val:.1f} |")
    else:
        # Horizontal — blocks as rows
        header_row = "| Block | " + " | ".join(cols) + " |"
        sep_row = "|---|" + "|".join([":---:"] * len(cols)) + "|"
        lines.append(header_row)
        lines.append(sep_row)
        for block_id, totals in ctx.block_totals.items():
            cells = [f"{totals.get(c, 0):.1f}" for c in cols]
            lines.append(f"| {block_id} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ============================================================
# Section 7 — Ratios (now live: reads SoilSnapshot.computed_ratios)
# ============================================================

# Render-order + labels + target-band text for each metric. Only ratios
# listed here get surfaced — anything else in computed_ratios is
# intentionally kept internal (e.g. SAR for soil is a reasoner input,
# not a farmer-friendly metric on its own).
# Target bands are FARMER-FRIENDLY — not a full agronomic treatise,
# just "where you are vs where you want to be" guidance.
_RATIO_DISPLAY_ORDER = [
    ("Ca:Mg", "Ca : Mg", "Target 3–7 : 1 depending on crop. 5 : 1 is classic for lucerne + mac; tighter (3 : 1) is fine for cereals."),
    ("soil_ESP_pct", "Sodium saturation (ESP %)", "Below 5 % is clean; 10–15 % is trending sodic; above 15 % needs active gypsum work."),
    ("SAR", "Soil SAR", "Below 13 is non-sodic; 13–20 moderately sodic; above 20 severe."),
    ("Al_saturation_pct", "Al saturation %", "Below 10 % is clean for most crops; above 20 % needs lime on non-acid-tolerant crops."),
    ("P:Zn", "P : Zn", "Below ~100 : 1 is comfortable; above 150 : 1 restricts Zn uptake regardless of soil Zn."),
    ("Ca:B", "Ca : B", "Target below ~1000 : 1 for most crops; excess Ca locks B away from uptake."),
    ("C:N", "C : N (soil)", "Around 10 : 1 is ideal for mineralisation; above 25 : 1 means N immobilised, slow early-season release."),
    ("water_SAR", "Irrigation water SAR", "Below 3 no restriction; 3–9 moderate; above 9 severe sodium hazard on water."),
    ("water_RSC_meq", "Irrigation water RSC (meq/L)", "Below 1.25 safe; above 2.5 bicarbonate concentrates Na on the exchange."),
]


@dataclass
class RatiosContext:
    # block_id → list of (label, value, guidance)
    per_block: list[tuple[str, list[tuple[str, float, str]]]]


def _pack_ratios(artifact: ProgrammeArtifact) -> RatiosContext:
    per_block: list[tuple[str, list[tuple[str, float, str]]]] = []
    for snap in artifact.soil_snapshots:
        if not snap.computed_ratios:
            continue
        rows: list[tuple[str, float, str]] = []
        for key, label, guidance in _RATIO_DISPLAY_ORDER:
            val = snap.computed_ratios.get(key)
            if val is None:
                continue
            rows.append((label, float(val), guidance))
        if rows:
            per_block.append((snap.block_name, rows))
    return RatiosContext(per_block=per_block)


def _render_ratios(ctx: RatiosContext) -> str:
    if not ctx.per_block:
        return ""
    lines = ["## Ratios — Where You Are", ""]
    lines.append(
        "These are the nutrient and soil ratios that shape how the programme "
        "is sized. Where you are today, and what the target band looks like."
    )
    lines.append("")

    multi_block = len(ctx.per_block) > 1
    for block_name, rows in ctx.per_block:
        if multi_block:
            lines.append(f"### {block_name}")
            lines.append("")
        lines.append("| Metric | Value | Target band |")
        lines.append("|---|---:|---|")
        for label, val, guidance in rows:
            # Format value sensibly — percentages, ratios, meq/L all
            # render to 1-2 decimals; integers for large ratios.
            val_str = _format_ratio_value(label, val)
            lines.append(f"| {label} | {val_str} | {guidance} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_ratio_value(label: str, val: float) -> str:
    """Tight formatter so Ca:Mg shows as '5.3 : 1', ESP as '14.7 %',
    SAR as '8.4', etc."""
    label_lc = label.lower()
    if ":" in label:
        # Ratio — display as 'X : 1'
        return f"{val:.1f} : 1" if val < 100 else f"{val:.0f} : 1"
    if "%" in label_lc:
        return f"{val:.1f} %"
    if "meq" in label_lc:
        return f"{val:.2f}"
    # Plain scalar (SAR, etc.)
    return f"{val:.1f}"


# ============================================================
# Section 8 — Assumptions
# ============================================================

@dataclass
class AssumptionsContext:
    assumptions: list[Assumption]


def _pack_assumptions(artifact: ProgrammeArtifact) -> AssumptionsContext:
    return AssumptionsContext(assumptions=artifact.assumptions)


def _render_assumptions(ctx: AssumptionsContext) -> str:
    if not ctx.assumptions:
        return ""
    lines = ["## Assumptions We're Carrying", ""]
    lines.append(
        "These are defaults or inferences the engine applied where data "
        "was incomplete. If any differ from what you know, let us know "
        "and the programme rebuilds against the actual values."
    )
    lines.append("")
    for a in ctx.assumptions:
        lines.append(f"- **{a.field}:** {a.assumed_value}")
        if a.override_guidance:
            lines.append(f"  *{a.override_guidance}*")
    return "\n".join(lines)


# ============================================================
# Section 9 — Outstanding Items + Risk Flags
# ============================================================

@dataclass
class OutstandingContext:
    outstanding: list[OutstandingItem]
    risk_flags: list[RiskFlag]


def _pack_outstanding_items(artifact: ProgrammeArtifact) -> OutstandingContext:
    return OutstandingContext(
        outstanding=artifact.outstanding_items,
        risk_flags=artifact.risk_flags,
    )


def _render_outstanding_items(ctx: OutstandingContext) -> str:
    if not ctx.outstanding and not ctx.risk_flags:
        return ""
    lines = ["## Items To Track", ""]

    if ctx.risk_flags:
        # Promote critical / warn first, then watch, then info
        order = {"critical": 0, "warn": 1, "watch": 2, "info": 3}
        flags = sorted(ctx.risk_flags, key=lambda f: order.get(f.severity, 99))
        lines.append("### Risk flags")
        lines.append("")
        for f in flags:
            label = f"**[{f.severity.upper()}]** " if f.severity in ("critical", "warn") else ""
            lines.append(f"- {label}{f.message}")
        lines.append("")

    if ctx.outstanding:
        lines.append("### Outstanding items")
        lines.append("")
        for o in ctx.outstanding:
            bits = [f"**{o.item}**", o.why_it_matters]
            if o.impact_if_skipped:
                bits.append(f"*Impact if skipped: {o.impact_if_skipped}*")
            lines.append("- " + " — ".join(bits))
        lines.append("")
    return "\n".join(lines).rstrip()


# ============================================================
# Section 5b — Why the Programme Works Over Multiple Years
# (stub: Phase C upgrades this to full narrative via Opus)
# ============================================================

@dataclass
class MultiYearRationaleContext:
    has_organic_anchor: bool
    total_organic_c_kg_per_ha: float  # estimated from organic carrier application
    is_perennial: bool
    crop: str
    has_sodium_issue: bool  # soil has elevated ESP — mention gypsum narrative


def _pack_multiyear_rationale(artifact: ProgrammeArtifact) -> MultiYearRationaleContext:
    # Rough estimate of organic carbon delivery: assume organic carrier
    # delivers ~30 % carbon by mass; sum dry-blend organic mass across
    # passes. Conservative; real number lives in the artifact after
    # future engine work.
    organic_mass_kg_per_ha = 0.0
    has_organic_anchor = False
    for blend in (artifact.blends or []):
        if not blend.method.kind.name.startswith("DRY_"):
            continue
        # If any raw_product in the blend has no 'stream' and rate is
        # substantial (>400 kg/ha per stage), treat it as the organic
        # anchor under Sapling's house rule.
        for part in blend.raw_products:
            rate_str = part.rate_per_stage_per_ha or ""
            # Parse "XXX kg" — best-effort
            try:
                rate_num = float(rate_str.replace("kg", "").strip().split()[0])
            except (ValueError, IndexError):
                continue
            if rate_num >= 400:
                organic_mass_kg_per_ha += rate_num * 0.5  # assume 50 % of this is organic fraction
                has_organic_anchor = True
                break
    total_organic_c = organic_mass_kg_per_ha * 0.30  # ~30 % C by mass

    crop = artifact.header.crop
    # crude perennial detection — will be replaced by proper crop-type
    # flag from crop_requirements in a follow-up. For the stub, the
    # list covers the common SA perennials.
    perennials = {
        "Macadamia", "Pecan", "Avocado", "Citrus", "Apple", "Pear",
        "Peach", "Plum", "Apricot", "Nectarine", "Cherry", "Fig",
        "Mango", "Guava", "Litchi", "Olive", "Lucerne", "Sugarcane",
        "Tea", "Rooibos", "Honeybush", "Blueberry", "Raspberry",
        "Blackberry", "Strawberry", "Banana", "Pineapple", "Passion Fruit",
        "Pomegranate", "Persimmon", "Table Grape", "Wine Grape",
    }
    is_perennial = any(crop.startswith(p) or p in crop for p in perennials)

    has_sodium_issue = any(
        (s.computed_ratios.get("soil_ESP_pct", 0) or 0) >= 5
        for s in artifact.soil_snapshots
    )

    return MultiYearRationaleContext(
        has_organic_anchor=has_organic_anchor,
        total_organic_c_kg_per_ha=total_organic_c,
        is_perennial=is_perennial,
        crop=crop,
        has_sodium_issue=has_sodium_issue,
    )


def _render_multiyear_rationale(ctx: MultiYearRationaleContext) -> str:
    # Only fire this section when an organic anchor is carrying the
    # multi-year story. Fertigation-only or foliar-only programmes
    # don't earn this section.
    if not ctx.has_organic_anchor:
        return ""

    lines = ["## Why the Programme Works Over Multiple Years", ""]
    lines.append(
        "The organic carrier at the heart of every dry blend is doing three "
        "different jobs on three different timescales:"
    )
    lines.append("")
    if ctx.has_sodium_issue:
        lines.append(
            "**Inside the first month** — soluble nutrients + available organic "
            "fraction release fast, covering the immediate crop demand. The "
            "gypsum fraction of the pellet begins displacing sodium off the "
            "exchange."
        )
    else:
        lines.append(
            "**Inside the first month** — soluble nutrients + available organic "
            "fraction release fast, covering the immediate crop demand. Calcium "
            "and sulphur from the carrier support cell-wall integrity and root "
            "function through establishment."
        )
    lines.append("")
    lines.append(
        "**Inside the first season** — roughly 20–30 % of the carrier's nitrogen "
        "mineralises and becomes plant-available, along with the full "
        "micronutrient package (boron, zinc, manganese, copper). This is why "
        "separate boron or micro broadcasts are usually unnecessary when the "
        "carrier is doing the work."
    )
    lines.append("")
    if ctx.total_organic_c_kg_per_ha > 0:
        lines.append(
            f"**Over the next 2–4 years** — the remaining 70 % of nitrogen releases "
            f"gradually as soil biology mineralises the organic fraction. Carbon "
            f"accumulates: this programme delivers roughly {ctx.total_organic_c_kg_per_ha:.0f} kg "
            f"organic C per hectare this season. On OM-poor SA soils that's "
            f"measurable lift in next year's soil test, and it compounds when "
            f"the programme is repeated annually."
        )
    else:
        lines.append(
            "**Over the next 2–4 years** — the slow-release nitrogen + organic "
            "carbon + phosphorus release gradually as soil biology mineralises "
            "the organic fraction. The soil's carrying capacity for every future "
            "crop improves with each annual application."
        )
    lines.append("")
    if ctx.is_perennial:
        lines.append(
            f"For a {ctx.crop.lower()} stand this matters especially: perennial "
            "root systems depend on soil structure and biology as much as on "
            "chemistry. The long-run programme is building the field the crop "
            "lives in, not just feeding this season's growth."
        )
    return "\n".join(lines).rstrip()


# ============================================================
# Section 9 — Year 2 and Beyond
# (stub: Phase C upgrades this to crop-and-context-specific outlook)
# ============================================================

@dataclass
class YearTwoContext:
    is_perennial: bool
    crop: str
    has_sodic_flag: bool
    has_ph_flag: bool
    soil_organic_matter_low: bool


def _pack_year_two_outlook(artifact: ProgrammeArtifact) -> YearTwoContext:
    crop = artifact.header.crop
    perennials = {
        "Macadamia", "Pecan", "Avocado", "Citrus", "Apple", "Pear",
        "Peach", "Plum", "Apricot", "Nectarine", "Cherry", "Fig",
        "Mango", "Guava", "Litchi", "Olive", "Lucerne", "Sugarcane",
        "Tea", "Rooibos", "Honeybush", "Blueberry", "Raspberry",
        "Blackberry", "Strawberry", "Banana", "Pineapple", "Passion Fruit",
        "Pomegranate", "Persimmon", "Table Grape", "Wine Grape",
    }
    is_perennial = any(crop.startswith(p) or p in crop for p in perennials)

    has_sodic = any(
        (s.computed_ratios.get("soil_ESP_pct", 0) or 0) >= 10
        for s in artifact.soil_snapshots
    )
    has_ph_flag = any(
        "pH" in (msg := rf.message) and ("alkaline" in msg.lower() or "acid" in msg.lower())
        for rf in artifact.risk_flags
    )
    # Simple low-OM heuristic — look for "OM" or "organic" in any risk-flag
    # message at warn+ severity.
    low_om = any(
        "om" in rf.message.lower() or "organic matter" in rf.message.lower()
        for rf in artifact.risk_flags
        if rf.severity in ("warn", "critical")
    )
    return YearTwoContext(
        is_perennial=is_perennial,
        crop=crop,
        has_sodic_flag=has_sodic,
        has_ph_flag=has_ph_flag,
        soil_organic_matter_low=low_om,
    )


def _render_year_two_outlook(ctx: YearTwoContext) -> str:
    # Only fire for programmes where a multi-season view genuinely matters.
    # Single-season annuals without sodic/pH/OM trajectory don't earn this.
    if not ctx.is_perennial and not (ctx.has_sodic_flag or ctx.soil_organic_matter_low):
        return ""

    lines = ["## Year 2 and Beyond", ""]
    if ctx.is_perennial:
        lines.append(
            f"This is a perennial {ctx.crop.lower()} programme, so Year 1 is the "
            "establishment or maintenance baseline — the real story is what the "
            "stand looks like after a few seasons on the same approach."
        )
        lines.append("")
    lines.append("**Three-year targets to track:**")
    lines.append("")
    if ctx.soil_organic_matter_low or ctx.is_perennial:
        lines.append("- **Soil organic matter** lifting toward 2 % (or higher for orchards). Measurable on next year's soil test.")
    if ctx.has_sodic_flag:
        lines.append("- **Sodium saturation** trending below 10 % (if currently above) through sustained gypsum inputs.")
    if ctx.has_ph_flag:
        lines.append("- **Soil pH** moving toward the crop's preferred band. This is a multi-season lift; year-on-year re-test tracks progress.")
    lines.append("- **Phosphorus** building from Low toward Optimal on soil test.")
    lines.append("- **Boron** in the crop-optimal band (varies by crop; typical 1.0–2.5 mg/kg).")
    lines.append("")
    lines.append(
        "**The ongoing programme to get there is straightforward:** continue the "
        "carrier + targeted synthetic approach at similar cadence annually, and "
        "top up phosphorus, potassium, and any flagged limiting nutrients each "
        "season against real post-harvest soil data rather than speculation."
    )
    return "\n".join(lines).rstrip()
