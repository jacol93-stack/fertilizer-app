"""PDF report generation router."""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from typing import Any
from pydantic import BaseModel, Field
from app.auth import CurrentUser, get_current_user
from app.supabase_client import get_supabase_admin
from app.services.pdf_builder import build_pdf, build_liquid_pdf, build_soil_pdf, build_program_pdf, build_comparison_pdf, build_diagnostic_soil_pdf
from app.services.comparison_engine import calculate_crop_impact, generate_recommendations
from app.services.notation import pct_to_sa_notation


class BlendPdfRequest(BaseModel):
    blend_name: str = ""
    client: str = ""
    farm: str = ""
    batch_size: float = 1000
    cost_per_ton: float = 0
    selling_price: float = 0
    sa_notation: str = ""
    exact: bool = True
    scale: float = 1.0
    recipe: list[dict] = []
    nutrients: list[dict] = []
    pricing: dict | None = None

router = APIRouter(tags=["reports"])


# ── Helpers ───────────────────────────────────────────────────────────────

def _audit(sb, user: CurrentUser, action: str, table: str, record_id: str | None = None, detail: dict | None = None):
    """Fire-and-forget audit log via DB RPC."""
    try:
        sb.rpc(
            "log_audit_event",
            {
                "p_event_type": action,
                "p_entity_type": table,
                "p_entity_id": record_id,
                "p_metadata": detail or {},
                "p_user_id": user.id,
            },
        ).execute()
    except Exception:
        pass  # audit failure should never block the request


def _pdf_response(pdf_bytes: bytes, filename: str) -> StreamingResponse:
    """Wrap raw PDF bytes in a StreamingResponse."""
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ── Blend PDF ─────────────────────────────────────────────────────────────

@router.get("/blend/{blend_id}/pdf")
def blend_pdf(blend_id: str, user: CurrentUser = Depends(get_current_user)):
    """Generate and return a blend recipe PDF."""
    sb = get_supabase_admin()

    # Fetch blend record
    result = sb.table("blends").select("*").eq("id", blend_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Blend not found")
    blend = result.data[0]

    # Access control: agents can only see their own blends
    if user.role != "admin" and blend.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Build recipe_data and nutrient_data table rows from stored JSON
    is_agent = user.role != "admin"

    # Fetch user company details for PDF header
    profile = sb.table("profiles").select("company_details").eq("id", user.id).execute()
    company_details = (profile.data[0].get("company_details") or {}) if profile.data else {}

    # ── Liquid blend PDF path ──
    if blend.get("blend_type") == "liquid":
        raw_recipe = blend.get("recipe", []) or []
        recipe_data = []
        for r in raw_recipe:
            row = [
                r.get("material", ""),
                f"{r.get('kg_per_tank', 0):.2f}",
                f"{r.get('g_per_l', 0):.2f}",
            ]
            if not is_agent and r.get("cost"):
                row.append(f"R{r.get('cost', 0):.0f}")
            recipe_data.append(row)

        raw_nutrients = blend.get("nutrients", []) or []
        nutrient_data = [
            [
                n.get("nutrient", ""),
                f"{n.get('target_g_l', 0):.3f}",
                f"{n.get('actual_g_l', 0):.3f}",
                f"{n.get('diff_g_l', 0):+.3f}",
            ]
            for n in raw_nutrients
        ]

        raw_instructions = blend.get("mixing_instructions") or []
        # Pull out the `_meta` dict the save path stashed with SA-notation /
        # Act 36 label data (see blends.save_blend). Strings remain the
        # actual mixing steps for the PDF.
        mixing_instructions: list[str] = []
        liquid_meta: dict = {}
        for entry in raw_instructions:
            if isinstance(entry, dict) and entry.get("_meta") == "sa_notation_label":
                liquid_meta = entry
            elif isinstance(entry, str):
                mixing_instructions.append(entry)

        pdf_bytes = build_liquid_pdf(
            blend_name=blend.get("blend_name", ""),
            client=blend.get("client", ""),
            farm=blend.get("farm", ""),
            tank_volume_l=blend.get("tank_volume_l", 1000) or 1000,
            total_dissolved_kg=sum(r.get("kg_per_tank", 0) for r in raw_recipe),
            sg_estimate=blend.get("sg_estimate", 1.0) or 1.0,
            recipe_data=recipe_data if recipe_data else None,
            nutrient_data=nutrient_data if nutrient_data else None,
            mixing_instructions=mixing_instructions or None,
            company_details=company_details or None,
            sa_notation=liquid_meta.get("sa_notation"),
            international_notation=liquid_meta.get("international_notation"),
            density_kg_per_l=liquid_meta.get("density_kg_per_l"),
            nutrient_composition=liquid_meta.get("nutrient_composition"),
            water_kg=liquid_meta.get("water_kg"),
        )

        _audit(sb, user, "liquid_blend_pdf_download", "blends", blend_id)
        filename = f"liquid_blend_{blend.get('blend_name', blend_id)}.pdf"
        return _pdf_response(pdf_bytes, filename)

    # ── Dry blend PDF path ──
    recipe_data = None
    if not is_agent:
        raw_recipe = blend.get("recipe", [])
        recipe_data = [
            [
                r.get("material", ""),
                r.get("type", ""),
                f"{r.get('kg', 0):.1f}",
                f"{r.get('pct', 0):.1f}",
                f"R{r.get('cost', 0):.0f}",
            ]
            for r in raw_recipe
        ]

    raw_nutrients = blend.get("nutrients", [])
    nutrient_data = [
        [
            n.get("nutrient", ""),
            f"{n.get('target', 0):.2f}",
            f"{n.get('actual', 0):.2f}",
            f"{n.get('diff', 0):+.2f}",
            f"{n.get('kg_per_ton', 0):.1f}",
        ]
        for n in raw_nutrients
    ]

    pricing_suggestion = None if is_agent else blend.get("pricing_suggestion")

    # Compute values the PDF builder needs
    batch_size = blend.get("batch_size", 1000) or 1000
    cost_per_ton = blend.get("cost_per_ton", 0) or 0
    selling_price = blend.get("selling_price", 0) or 0
    total_cost = cost_per_ton * batch_size / 1000
    margin = selling_price - cost_per_ton if selling_price and cost_per_ton else 0

    # Calculate actual compost % from recipe
    raw_recipe = blend.get("recipe", []) or []
    compost_row = next((r for r in raw_recipe if r.get("material") == "Manure Compost"), None)
    compost_pct = compost_row["pct"] if compost_row else 0

    pdf_bytes = build_pdf(
        blend_name=blend.get("blend_name", ""),
        client=blend.get("client", ""),
        farm=blend.get("farm", ""),
        batch=batch_size,
        compost_pct=compost_pct,
        cost_per_ton=cost_per_ton,
        total_cost=total_cost,
        selling_price=selling_price,
        margin=margin,
        is_relaxed=False,
        relaxed_scale=1.0,
        recipe_data=recipe_data,
        nutrient_data=nutrient_data,
        sa_notation=blend.get("sa_notation") or pct_to_sa_notation(
            *[next((n.get("actual", 0) for n in raw_nutrients if n.get("nutrient") == nut), 0) for nut in ("N", "P", "K")]
        )[0],
        pricing_suggestion=pricing_suggestion,
        company_details=company_details,
    )

    _audit(sb, user, "blend_pdf_download", "blends", blend_id)

    filename = f"blend_{blend.get('blend_name', blend_id)}.pdf"
    return _pdf_response(pdf_bytes, filename)


@router.post("/blend/pdf")
def blend_pdf_from_data(body: BlendPdfRequest, user: CurrentUser = Depends(get_current_user)):
    """Generate a blend PDF directly from data (no saved blend needed)."""
    is_agent = user.role != "admin"

    recipe_data = None
    if not is_agent and body.recipe:
        recipe_data = [
            [
                r.get("material", ""),
                r.get("type", ""),
                f"{r.get('kg', 0):.1f}",
                f"{r.get('pct', 0):.1f}",
                f"R{r.get('cost', 0):.0f}",
            ]
            for r in body.recipe
        ]

    nutrient_data = [
        [
            n.get("nutrient", ""),
            f"{n.get('target', 0):.2f}",
            f"{n.get('actual', 0):.2f}",
            f"{n.get('diff', 0):+.2f}",
            f"{n.get('kg_per_ton', 0):.1f}",
        ]
        for n in body.nutrients
    ]

    batch = body.batch_size or 1000
    total_cost = body.cost_per_ton * batch / 1000
    margin = body.selling_price - body.cost_per_ton if body.selling_price else 0

    compost_row = next((r for r in body.recipe if r.get("material") == "Manure Compost"), None)
    compost_pct = compost_row["pct"] if compost_row else 0

    pricing = None if is_agent else body.pricing

    pdf_bytes = build_pdf(
        blend_name=body.blend_name,
        client=body.client,
        farm=body.farm,
        batch=batch,
        compost_pct=compost_pct,
        cost_per_ton=body.cost_per_ton if not is_agent else 0,
        total_cost=total_cost if not is_agent else 0,
        selling_price=body.selling_price if not is_agent else 0,
        margin=margin if not is_agent else 0,
        is_relaxed=not body.exact,
        relaxed_scale=body.scale,
        recipe_data=recipe_data,
        nutrient_data=nutrient_data,
        sa_notation=body.sa_notation,
        pricing_suggestion=pricing,
    )

    sb = get_supabase_admin()

    # Fetch user company details for PDF header
    profile = sb.table("profiles").select("company_details").eq("id", user.id).execute()
    cd = (profile.data[0].get("company_details") or {}) if profile.data else {}
    if cd:
        pdf_bytes = build_pdf(
            blend_name=body.blend_name,
            client=body.client,
            farm=body.farm,
            batch=batch,
            compost_pct=compost_pct,
            cost_per_ton=body.cost_per_ton if not is_agent else 0,
            total_cost=total_cost if not is_agent else 0,
            selling_price=body.selling_price if not is_agent else 0,
            margin=margin if not is_agent else 0,
            is_relaxed=not body.exact,
            relaxed_scale=body.scale,
            recipe_data=recipe_data,
            nutrient_data=nutrient_data,
            sa_notation=body.sa_notation,
            pricing_suggestion=pricing,
            company_details=cd,
        )

    _audit(sb, user, "blend_pdf_download", "blends", None, {"blend_name": body.blend_name})

    filename = f"blend_{body.blend_name or 'draft'}.pdf"
    return _pdf_response(pdf_bytes, filename)


# ── Liquid Blend PDF ──────────────────────────────────────────────────────

class LiquidBlendPdfRequest(BaseModel):
    blend_name: str = ""
    client: str = ""
    farm: str = ""
    tank_volume_l: float = 1000
    total_dissolved_kg: float = 0
    sg_estimate: float = 1.0
    exact: bool = True
    scale: float = 1.0
    recipe: list[dict] = []
    nutrients: list[dict] = []
    mixing_instructions: list[str] = []
    compatibility_warnings: list[str] = []
    cost_per_ton: float = 0
    selling_price: float = 0
    # SA-notation mass-fraction flow (2026-04-18)
    sa_notation: str | None = None
    international_notation: str | None = None
    density_kg_per_l: float | None = None
    nutrient_composition: list[dict] | None = None
    water_kg: float | None = None


@router.post("/blend/liquid/pdf")
def liquid_blend_pdf_from_data(body: LiquidBlendPdfRequest, user: CurrentUser = Depends(get_current_user)):
    """Generate a liquid blend PDF directly from data."""
    is_agent = user.role != "admin"

    recipe_data = []
    for r in body.recipe:
        row = [
            r.get("material", ""),
            f"{r.get('kg_per_tank', 0):.2f}",
            f"{r.get('g_per_l', 0):.2f}",
        ]
        if not is_agent and r.get("cost"):
            row.append(f"R{r.get('cost', 0):.0f}")
        recipe_data.append(row)

    nutrient_data = [
        [
            n.get("nutrient", ""),
            f"{n.get('target_g_l', 0):.3f}",
            f"{n.get('actual_g_l', 0):.3f}",
            f"{n.get('diff_g_l', 0):+.3f}",
        ]
        for n in body.nutrients
    ]

    sb = get_supabase_admin()

    # Fetch user company details for PDF header
    profile = sb.table("profiles").select("company_details").eq("id", user.id).execute()
    cd = (profile.data[0].get("company_details") or {}) if profile.data else {}

    pdf_bytes = build_liquid_pdf(
        blend_name=body.blend_name,
        client=body.client,
        farm=body.farm,
        tank_volume_l=body.tank_volume_l,
        total_dissolved_kg=body.total_dissolved_kg,
        sg_estimate=body.sg_estimate,
        recipe_data=recipe_data if recipe_data else None,
        nutrient_data=nutrient_data if nutrient_data else None,
        mixing_instructions=body.mixing_instructions or None,
        compatibility_warnings=body.compatibility_warnings or None,
        exact=body.exact,
        scale=body.scale,
        cost_per_ton=body.cost_per_ton if not is_agent else 0,
        selling_price=body.selling_price if not is_agent else 0,
        company_details=cd or None,
        sa_notation=body.sa_notation,
        international_notation=body.international_notation,
        density_kg_per_l=body.density_kg_per_l,
        nutrient_composition=body.nutrient_composition,
        water_kg=body.water_kg,
    )

    _audit(sb, user, "liquid_blend_pdf_download", "blends", None, {"blend_name": body.blend_name})

    filename = f"liquid_blend_{body.blend_name or 'draft'}.pdf"
    return _pdf_response(pdf_bytes, filename)


# ── Soil Analysis PDF ─────────────────────────────────────────────────────

@router.get("/soil/{analysis_id}/pdf")
def soil_pdf(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    """Generate and return a soil analysis PDF."""
    sb = get_supabase_admin()

    # Fetch analysis record
    result = sb.table("soil_analyses").select("*").eq("id", analysis_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Soil analysis not found")
    analysis = result.data[0]

    # Access control: agents can only see their own analyses
    if user.role != "admin" and analysis.get("agent_id") != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    pdf_bytes = build_diagnostic_soil_pdf(
        customer=analysis.get("customer", ""),
        farm=analysis.get("farm", ""),
        field=analysis.get("field", ""),
        crop_name=analysis.get("crop", analysis.get("crop_name", "")),
        cultivar=analysis.get("cultivar", ""),
        yield_target=analysis.get("yield_target", 0),
        yield_unit=analysis.get("yield_unit", ""),
        agent_name=analysis.get("agent_name", ""),
        agent_cell=analysis.get("agent_cell", ""),
        agent_email=analysis.get("agent_email", ""),
        lab_name=analysis.get("lab_name", ""),
        analysis_date=analysis.get("analysis_date", ""),
        soil_values=analysis.get("soil_values", {}),
        classifications=analysis.get("classifications", {}),
        ratio_results=analysis.get("ratio_results") or [],
        norms_snapshot=analysis.get("norms_snapshot"),
    )

    _audit(sb, user, "soil_analysis_pdf_download", "soil_analyses", analysis_id)

    filename = f"soil_analysis_{analysis_id}.pdf"
    return _pdf_response(pdf_bytes, filename)


# ── Diagnostic Soil PDF (unsaved analysis) ────────────────────────────────

class DiagnosticPdfRequest(BaseModel):
    customer: str = ""
    farm: str = ""
    field: str = ""
    crop_name: str = ""
    cultivar: str = ""
    yield_target: float | None = None
    yield_unit: str = ""
    agent_name: str = ""
    agent_cell: str = ""
    agent_email: str = ""
    lab_name: str = ""
    analysis_date: str = ""
    soil_values: dict[str, Any] = Field(default_factory=dict)
    classifications: dict[str, str] = Field(default_factory=dict)
    ratio_results: list[dict[str, Any]] = Field(default_factory=list)
    soil_thresholds: dict[str, dict[str, float]] | None = None


@router.post("/soil/diagnostic/pdf")
def diagnostic_soil_pdf(body: DiagnosticPdfRequest, user: CurrentUser = Depends(get_current_user)):
    """Generate a diagnostic soil analysis PDF from unsaved data."""
    # Build norms_snapshot from soil_thresholds if provided
    norms_snapshot = None
    if body.soil_thresholds:
        norms_snapshot = {
            "sufficiency": [
                {
                    "parameter": param,
                    "unit": "",
                    "very_low_max": t.get("very_low_max", 0),
                    "low_max": t.get("low_max", 0),
                    "optimal_max": t.get("optimal_max", 0),
                    "high_max": t.get("high_max", 0),
                }
                for param, t in body.soil_thresholds.items()
            ]
        }

    pdf_bytes = build_diagnostic_soil_pdf(
        customer=body.customer,
        farm=body.farm,
        field=body.field,
        crop_name=body.crop_name,
        cultivar=body.cultivar,
        yield_target=body.yield_target or 0,
        yield_unit=body.yield_unit,
        agent_name=body.agent_name,
        agent_cell=body.agent_cell,
        agent_email=body.agent_email,
        lab_name=body.lab_name,
        analysis_date=body.analysis_date,
        soil_values=body.soil_values,
        classifications=body.classifications,
        ratio_results=body.ratio_results,
        norms_snapshot=norms_snapshot,
    )

    sb = get_supabase_admin()
    _audit(sb, user, "diagnostic_pdf_download", "soil_analyses", None,
           {"customer": body.customer})

    safe_name = (body.customer or "diagnostic").replace(" ", "_")[:30]
    return _pdf_response(pdf_bytes, f"soil_diagnostic_{safe_name}.pdf")


# ── Soil Program PDF (comprehensive report) ──────────────────────────────

class SoilProgramPdfRequest(BaseModel):
    """Request body for the comprehensive soil-analysis + fertilizer-program PDF."""
    # Customer info
    customer: str = ""
    farm: str = ""
    field: str = ""
    crop: str = ""
    cultivar: str = ""
    tree_age: float | None = None
    yield_target: float | None = None
    yield_unit: str = ""
    plants_per_ha: float | None = None
    field_area_ha: float | None = None
    agent_name: str = ""
    agent_email: str = ""
    lab_name: str = ""
    analysis_date: str = ""

    # Soil data
    soil_values: dict[str, Any] = Field(default_factory=dict)
    classifications: dict[str, str] = Field(default_factory=dict)
    ratio_results: list[dict[str, Any]] = Field(default_factory=list)

    # Targets
    nutrient_targets: list[dict[str, Any]] = Field(default_factory=list)

    # Program
    applications: list[dict[str, Any]] = Field(default_factory=list)
    blend_groups: list[dict[str, Any]] = Field(default_factory=list)

    # Costs
    total_cost_ha: float = 0
    total_cost_field: float | None = None
    total_cost_tree: float | None = None


@router.post("/soil-program/pdf")
def soil_program_pdf(body: SoilProgramPdfRequest, user: CurrentUser = Depends(get_current_user)):
    """Generate a comprehensive Fertilizer Recommendation Report PDF.

    Combines soil analysis results, nutrient requirements, the full
    fertilizer program (monthly applications), blend summaries, and cost
    breakdown into a single landscape-A4 PDF.

    Admin users see full recipe breakdowns and per-material costs.
    Agent users see blends as single products with marked-up totals only.
    """
    role = "admin" if user.role == "admin" else "agent"

    pdf_bytes = build_program_pdf(
        customer=body.customer,
        farm=body.farm,
        field=body.field,
        crop=body.crop,
        cultivar=body.cultivar,
        tree_age=body.tree_age,
        yield_target=body.yield_target,
        yield_unit=body.yield_unit,
        plants_per_ha=body.plants_per_ha,
        field_area_ha=body.field_area_ha,
        agent_name=body.agent_name,
        agent_email=body.agent_email,
        lab_name=body.lab_name,
        analysis_date=body.analysis_date,
        soil_values=body.soil_values,
        classifications=body.classifications,
        ratio_results=body.ratio_results,
        nutrient_targets=body.nutrient_targets,
        applications=body.applications,
        blend_groups=body.blend_groups,
        total_cost_ha=body.total_cost_ha,
        total_cost_field=body.total_cost_field,
        total_cost_tree=body.total_cost_tree,
        role=role,
    )

    sb = get_supabase_admin()
    _audit(sb, user, "soil_program_pdf_download", "soil_analyses", None, {
        "customer": body.customer,
        "farm": body.farm,
        "field": body.field,
    })

    safe_name = (body.customer or "report").replace(" ", "_")[:30]
    filename = f"fertilizer_program_{safe_name}.pdf"
    return _pdf_response(pdf_bytes, filename)


# ── Comparison PDF ───────────────────────────────────────────────────────────

class ComparisonPdfRequest(BaseModel):
    analysis_ids: list[str] = Field(..., min_length=2)


@router.post("/soil/compare/pdf")
def comparison_pdf(body: ComparisonPdfRequest, user: CurrentUser = Depends(get_current_user)):
    """Generate a soil comparison PDF report."""
    sb = get_supabase_admin()

    result = sb.table("soil_analyses").select("*").in_("id", body.analysis_ids).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No analyses found")

    analyses = result.data
    if user.role != "admin":
        for a in analyses:
            if a.get("agent_id") != user.id:
                raise HTTPException(status_code=403, detail="Access denied")

    analyses.sort(key=lambda a: a.get("analysis_date") or a.get("created_at", "")[:10])

    # Determine comparison type
    field_ids = set(a.get("field_id") for a in analyses if a.get("field_id"))
    is_same_field = len(field_ids) == 1
    comparison_type = "timeline" if is_same_field else "snapshot"

    # Crop impact (timeline only)
    crop_impacts = []
    if is_same_field:
        try:
            crop_rows = sb.table("crop_requirements").select("*").execute().data or []
        except Exception:
            crop_rows = []
        try:
            param_map_rows = sb.table("soil_parameter_map").select("*").execute().data or []
        except Exception:
            param_map_rows = []

        the_field_id = field_ids.pop() if field_ids else None
        for i in range(len(analyses) - 1):
            crop_history = []
            if the_field_id:
                d1 = analyses[i].get("analysis_date") or analyses[i].get("created_at", "")[:10]
                d2 = analyses[i + 1].get("analysis_date") or analyses[i + 1].get("created_at", "")[:10]
                try:
                    ch = sb.table("field_crop_history").select("*").eq("field_id", the_field_id).gte("date_planted", d1).lte("date_planted", d2).execute()
                    crop_history = ch.data or []
                except Exception:
                    pass
            impact = calculate_crop_impact(analyses[i], analyses[i + 1], crop_rows, param_map_rows, crop_history)
            crop_impacts.append(impact)

    recs = generate_recommendations(analyses, crop_impacts, comparison_type)

    is_agent = user.role != "admin"
    pdf_bytes = build_comparison_pdf(
        analyses=analyses,
        comparison_type=comparison_type,
        crop_impact=crop_impacts,
        recommendations=recs,
        role="sales_agent" if is_agent else "admin",
    )

    _audit(sb, user, "comparison_pdf_download", "soil_analyses", None, {
        "analysis_ids": body.analysis_ids,
        "comparison_type": comparison_type,
    })

    return _pdf_response(pdf_bytes, "soil_comparison.pdf")
