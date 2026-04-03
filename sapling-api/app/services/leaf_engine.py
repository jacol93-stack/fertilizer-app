"""Leaf/sap analysis engine: classify against Fertasa norms, generate recommendations."""

from app.services.foliar_engine import recommend_foliar_products
from app.supabase_client import get_supabase_admin

# Standard leaf analysis elements
LEAF_ELEMENTS = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "Mn", "Zn", "Cu", "B", "Mo"]


def classify_leaf_values(crop: str | None, values: dict[str, float]) -> dict:
    """Classify leaf analysis values against Fertasa norms.

    Args:
        crop: crop name to look up norms (None = return values without classification)
        values: {element: concentration} e.g. {"N": 2.5, "P": 0.18}

    Returns:
        dict with classifications, deficiencies, excesses
    """
    sb = get_supabase_admin()

    norm_data: list[dict] = []
    if crop:
        # Load Fertasa leaf norms for this crop
        norms = sb.table("fertasa_leaf_norms").select("*").ilike("crop", f"%{crop}%").execute()
        norm_data = norms.data or []

        if not norm_data:
            # Try broader match
            norms = sb.table("fertasa_leaf_norms").select("*").execute()
            norm_data = [n for n in (norms.data or []) if crop.lower() in str(n.get("crop", "")).lower()]

    # Build norm lookup
    norm_map = {}
    for row in norm_data:
        element = row.get("element") or row.get("nutrient")
        if element:
            norm_map[element.upper()] = row

    classifications = {}
    deficiencies = []
    excesses = []

    for element, value in values.items():
        if value is None:
            continue

        elem_upper = element.upper()
        norm = norm_map.get(elem_upper)

        if not norm:
            classifications[element] = "No norm"
            continue

        low = float(norm.get("low") or norm.get("deficient_max") or norm.get("sufficient_min") or 0)
        sufficient_low = float(norm.get("sufficient_low") or norm.get("adequate_min") or norm.get("sufficient_min") or low)
        sufficient_high = float(norm.get("sufficient_high") or norm.get("adequate_max") or norm.get("sufficient_max") or 999)
        high = float(norm.get("high") or norm.get("excess_min") or sufficient_high)

        if value < low:
            classifications[element] = "Deficient"
            deficiencies.append({
                "element": element,
                "value": value,
                "norm_low": sufficient_low,
                "shortfall_pct": round((1 - value / max(sufficient_low, 0.001)) * 100, 1),
            })
        elif value < sufficient_low:
            classifications[element] = "Low"
            deficiencies.append({
                "element": element,
                "value": value,
                "norm_low": sufficient_low,
                "shortfall_pct": round((1 - value / max(sufficient_low, 0.001)) * 100, 1),
            })
        elif value <= sufficient_high:
            classifications[element] = "Sufficient"
        elif value <= high:
            classifications[element] = "High"
            excesses.append({"element": element, "value": value, "norm_high": sufficient_high})
        else:
            classifications[element] = "Excess"
            excesses.append({"element": element, "value": value, "norm_high": sufficient_high})

    return {
        "classifications": classifications,
        "deficiencies": deficiencies,
        "excesses": excesses,
        "norms_found": len(norm_map),
    }


def generate_leaf_recommendations(
    crop: str | None,
    classifications: dict,
    deficiencies: list[dict],
    programme_id: str | None = None,
) -> dict:
    """Generate adjustment recommendations from leaf analysis results.

    If deficiencies are found, recommends foliar sprays from the product catalog.
    If linked to a programme, suggests adjustments to the remaining feeding plan.
    """
    sb = get_supabase_admin()

    recommendations = []
    foliar_recs = None

    if deficiencies:
        # Build deficit dict for foliar engine (convert to kg/ha estimate)
        # Leaf deficiency % → rough foliar correction: typically 0.5-5 kg/ha per element
        deficit = {}
        for d in deficiencies:
            elem = d["element"].lower()
            shortfall = d.get("shortfall_pct", 10)
            # Rough estimate: higher shortfall = more kg/ha needed
            if elem in ("n", "k", "ca", "mg"):
                deficit[elem] = round(shortfall * 0.2, 1)  # Macro: 0.2 kg/ha per % shortfall
            elif elem in ("p", "s"):
                deficit[elem] = round(shortfall * 0.1, 1)
            else:
                deficit[elem] = round(shortfall * 0.02, 2)  # Micro: much less

        # Get foliar product recommendations
        products = sb.table("liquid_products").select("*").execute()
        if products.data:
            foliar_recs = recommend_foliar_products(
                deficit=deficit,
                products=products.data,
                crop=crop,
                max_products=3,
            )

        for d in deficiencies:
            rec = {
                "type": "deficiency_correction",
                "element": d["element"],
                "severity": "critical" if d.get("shortfall_pct", 0) > 30 else "moderate",
                "action": f"Apply foliar {d['element']} — current level {d.get('shortfall_pct', 0):.0f}% below sufficient range",
            }
            recommendations.append(rec)

    # Programme adjustment if linked
    programme_adjustment = None
    if programme_id and deficiencies:
        programme_adjustment = {
            "trigger_type": "leaf_analysis",
            "suggested_action": "adjust_remaining_plan",
            "deficient_elements": [d["element"] for d in deficiencies],
            "note": f"Leaf analysis shows deficiencies in {', '.join(d['element'] for d in deficiencies)}. Consider foliar correction and/or increasing rates for remaining applications.",
        }

    return {
        "recommendations": recommendations,
        "foliar_recommendations": foliar_recs,
        "programme_adjustment": programme_adjustment,
    }


def get_sampling_guide(crop: str) -> dict | None:
    """Return Fertasa sampling guide for a crop."""
    sb = get_supabase_admin()
    try:
        result = sb.table("fertasa_sampling_guide").select("*").ilike("crop", f"%{crop}%").execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return None
