"""Programme engine: orchestrates multi-block season programme generation.

Takes a programme with blocks (each having a soil analysis and crop), generates
feeding plans per block, groups blocks by similar NPK profiles, and runs the
blend optimizer for each group.
"""

from app.services.feeding_engine import generate_feeding_plan, validate_methods
from app.services.soil_corrections import calculate_corrective_targets
from app.services.foliar_engine import recommend_foliar_products
from app.supabase_client import get_supabase_admin

# Methods that should use foliar product recommendations
FOLIAR_METHODS = {"foliar", "foliar_spray"}
# Methods that use the dry blend optimizer
DRY_METHODS = {"broadcast", "band_place", "side_dress", "topdress"}


def build_programme(
    programme_id: str,
    blocks: list[dict],
    agent_id: str,
) -> dict:
    """Generate feeding plans and blend groups for all blocks in a programme.

    Args:
        programme_id: the programme UUID
        blocks: list of block dicts, each must have:
            - id, crop, yield_target, yield_unit, tree_age, pop_per_ha, area_ha
            - nutrient_targets: list of {Nutrient, Target_kg_ha}
        agent_id: the agent who owns the programme

    Returns:
        dict with:
            - blocks: updated blocks with feeding_plan items and blend_group
            - blend_groups: dict of group_letter -> {crops, total_area, applications}
    """
    sb = get_supabase_admin()

    # Generate feeding plan for each block
    block_plans = []
    for block in blocks:
        crop = block["crop"]
        targets = block.get("nutrient_targets", [])
        if not targets:
            block_plans.append({"block": block, "items": [], "npk_profile": (0, 0, 0)})
            continue

        # Load growth stages for this crop (try exact match, then base crop name)
        base_crop = crop.split("(")[0].strip() if "(" in crop else crop
        stages_result = (
            sb.table("crop_growth_stages")
            .select("*")
            .eq("crop", crop)
            .order("stage_order")
            .execute()
        )
        growth_stages = stages_result.data or []

        if not growth_stages and base_crop != crop:
            stages_result = (
                sb.table("crop_growth_stages")
                .select("*")
                .eq("crop", base_crop)
                .order("stage_order")
                .execute()
            )
            growth_stages = stages_result.data or []

        if not growth_stages:
            block_plans.append({"block": block, "items": [], "npk_profile": (0, 0, 0)})
            continue

        # Load age factors for perennials (try exact crop, then base name)
        age_factors = None
        crop_req = sb.table("crop_requirements").select("crop_type").eq("crop", crop).limit(1).execute()
        crop_type = "annual"
        if crop_req.data:
            crop_type = crop_req.data[0].get("crop_type", "annual") or "annual"
        elif base_crop != crop:
            crop_req = sb.table("crop_requirements").select("crop_type").eq("crop", base_crop).limit(1).execute()
            if crop_req.data:
                crop_type = crop_req.data[0].get("crop_type", "annual") or "annual"

        if crop_type == "perennial" and block.get("tree_age"):
            af_result = sb.table("perennial_age_factors").select("*").eq("crop", crop).execute()
            if not af_result.data and base_crop != crop:
                af_result = sb.table("perennial_age_factors").select("*").eq("crop", base_crop).execute()
            age_factors = af_result.data or None

        # Calculate corrective build-up targets from linked soil analysis
        corrective_items = None
        soil_analysis_id = block.get("soil_analysis_id")
        if soil_analysis_id:
            try:
                sa = sb.table("soil_analyses").select(
                    "soil_values, norms_snapshot"
                ).eq("id", soil_analysis_id).limit(1).execute()
                if sa.data:
                    soil_values = sa.data[0].get("soil_values") or {}
                    snapshot = sa.data[0].get("norms_snapshot") or {}
                    suff_rows = snapshot.get("sufficiency") or []
                    param_rows = (
                        sb.table("soil_parameter_map").select("*").execute().data or []
                    )
                    crop_overrides = snapshot.get("crop_overrides") or []
                    ct = calculate_corrective_targets(
                        soil_values=soil_values,
                        nutrient_targets=targets,
                        sufficiency_rows=suff_rows,
                        param_map_rows=param_rows,
                        crop_override_rows=crop_overrides or None,
                    )
                    corrective_items = ct.get("corrective_items") or None
            except Exception:
                pass  # Non-critical — proceed without corrections

        # Generate feeding plan
        items = generate_feeding_plan(
            nutrient_targets=targets,
            growth_stages=growth_stages,
            crop_type=crop_type,
            tree_age=block.get("tree_age"),
            age_factors=age_factors,
            field_area_ha=block.get("area_ha"),
            corrective_items=corrective_items,
        )

        # Load field data for method/irrigation constraints
        field_data = None
        if block.get("field_id"):
            try:
                field_result = sb.table("fields").select(
                    "accepted_methods, irrigation_type, fertigation_months"
                ).eq("id", block["field_id"]).execute()
                if field_result.data:
                    field_data = field_result.data[0]
            except Exception:
                pass

        # Build infrastructure list from field irrigation_type
        infrastructure = None
        farmer_methods = None
        if field_data:
            irr = field_data.get("irrigation_type")
            if irr and irr != "none":
                infrastructure = [irr]
            elif irr == "none":
                infrastructure = []
            farmer_methods = field_data.get("accepted_methods") or None

        # Validate methods (try exact crop, then base name)
        try:
            cam_result = sb.table("crop_application_methods").select("*").eq("crop", crop).execute()
            if not cam_result.data and base_crop != crop:
                cam_result = sb.table("crop_application_methods").select("*").eq("crop", base_crop).execute()
            if cam_result.data:
                items = validate_methods(
                    items, cam_result.data,
                    infrastructure=infrastructure,
                    accepted_methods=farmer_methods,
                )
        except Exception:
            pass

        # Constrain fertigation to available months
        if field_data and field_data.get("fertigation_months"):
            fert_months = set(field_data["fertigation_months"])
            for item in items:
                if item.get("method") == "fertigation":
                    target_month = item.get("month_target")
                    if target_month and target_month not in fert_months:
                        available = item.get("available_methods", [])
                        fallback = "broadcast" if "broadcast" in available else (available[0] if available else "broadcast")
                        item["method"] = fallback
                        item["method_note"] = f"Fertigation unavailable in month {target_month}, using {fallback}"

        # Enrich foliar items with product recommendations
        items = _enrich_with_product_recommendations(items, crop, sb)

        # Calculate NPK profile for grouping (only dry/fertigation items)
        total_n = sum(item.get("n_kg_ha", 0) for item in items if item.get("method") not in FOLIAR_METHODS)
        total_p = sum(item.get("p_kg_ha", 0) for item in items if item.get("method") not in FOLIAR_METHODS)
        total_k = sum(item.get("k_kg_ha", 0) for item in items if item.get("method") not in FOLIAR_METHODS)

        block_plans.append({
            "block": block,
            "items": items,
            "crop_type": crop_type,
            "npk_profile": (total_n, total_p, total_k),
        })

    # Group blocks by similar NPK profile
    groups = _group_blocks_by_npk(block_plans)

    # Assign group letters to blocks
    for group_letter, group_blocks in groups.items():
        for bp in group_blocks:
            bp["block"]["blend_group"] = group_letter

    # Build summary per group
    blend_groups = {}
    for group_letter, group_blocks in groups.items():
        crops = list(set(bp["block"]["crop"] for bp in group_blocks))
        total_area = sum(bp["block"].get("area_ha", 0) or 0 for bp in group_blocks)
        block_names = [bp["block"]["name"] for bp in group_blocks]

        # Aggregate applications across blocks in this group
        # Use the first block's plan as template for timing
        template_items = group_blocks[0]["items"] if group_blocks else []

        blend_groups[group_letter] = {
            "group": group_letter,
            "crops": crops,
            "block_names": block_names,
            "total_area_ha": round(total_area, 2),
            "num_applications": len(template_items),
            "template_items": template_items,
        }

    return {
        "block_plans": block_plans,
        "blend_groups": blend_groups,
    }


def _enrich_with_product_recommendations(
    items: list[dict],
    crop: str,
    sb,
) -> list[dict]:
    """For items with foliar method, attach product recommendations.

    Loads the product catalog once and matches each foliar item's nutrient
    profile to the best products. Non-foliar items pass through unchanged.
    """
    foliar_items = [it for it in items if it.get("method") in FOLIAR_METHODS]
    if not foliar_items:
        return items

    # Load product catalog once
    try:
        products_result = sb.table("liquid_products").select("*").execute()
        products = products_result.data or []
    except Exception:
        return items  # If catalog unavailable, skip enrichment

    if not products:
        return items

    for item in items:
        if item.get("method") not in FOLIAR_METHODS:
            continue

        # Build deficit from item's nutrient values
        deficit = {}
        for nut_key in ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]:
            val = item.get(f"{nut_key}_kg_ha", 0)
            if val and float(val) > 0.001:
                deficit[nut_key] = float(val)

        if not deficit:
            continue

        # Get recommendations
        result = recommend_foliar_products(
            deficit=deficit,
            products=products,
            crop=crop,
            max_products=2,
        )

        if result and result.get("recommendations"):
            item["foliar_recommendations"] = result["recommendations"]
            item["foliar_fully_covered"] = result.get("fully_covered", False)
            item["foliar_remaining"] = result.get("remaining_deficit", {})
            item["application_type"] = "foliar_product"
        else:
            item["application_type"] = "foliar_custom"  # No matching product found

    return items


def _group_blocks_by_npk(block_plans: list[dict], margin: float = 0.15) -> dict[str, list[dict]]:
    """Group blocks that have similar NPK profiles (within margin proportional difference).

    Blocks with the same crop and similar NPK ratios can share blends.

    Args:
        block_plans: list of block plan dicts with npk_profile
        margin: proportional difference threshold (default 0.15 = 15%)

    Returns: dict of group_letter -> list of block_plan dicts
    """
    if not block_plans:
        return {}

    groups: list[list[dict]] = []

    for bp in block_plans:
        n, p, k = bp["npk_profile"]
        total = n + p + k
        if total < 0.01:
            groups.append([bp])
            continue

        n_prop = n / total
        p_prop = p / total
        k_prop = k / total
        crop = bp["block"]["crop"]

        placed = False
        for g in groups:
            ref = g[0]
            # Must be same crop to share a blend
            if ref["block"]["crop"] != crop:
                continue

            ref_n, ref_p, ref_k = ref["npk_profile"]
            ref_total = ref_n + ref_p + ref_k
            if ref_total < 0.01:
                continue

            ref_n_prop = ref_n / ref_total
            ref_p_prop = ref_p / ref_total
            ref_k_prop = ref_k / ref_total

            diff = abs(n_prop - ref_n_prop) + abs(p_prop - ref_p_prop) + abs(k_prop - ref_k_prop)
            if diff < margin:
                g.append(bp)
                placed = True
                break

        if not placed:
            groups.append([bp])

    result = {}
    for i, g in enumerate(groups):
        letter = chr(65 + i)  # A, B, C...
        result[letter] = g

    return result


def generate_block_plans(blocks: list[dict], sb=None) -> list[dict]:
    """Generate feeding plans for blocks without saving. Used by preview-schedule.

    Returns list of block_plan dicts, each with:
        block, items (feeding items), crop_type, npk_profile
    """
    if sb is None:
        sb = get_supabase_admin()

    block_plans = []
    for block in blocks:
        crop = block["crop"]
        targets = block.get("nutrient_targets", [])
        if not targets:
            block_plans.append({"block": block, "items": [], "npk_profile": (0, 0, 0), "crop_type": "annual"})
            continue

        # Load growth stages
        base_crop = crop.split("(")[0].strip() if "(" in crop else crop
        stages_result = sb.table("crop_growth_stages").select("*").eq("crop", crop).order("stage_order").execute()
        growth_stages = stages_result.data or []
        if not growth_stages and base_crop != crop:
            stages_result = sb.table("crop_growth_stages").select("*").eq("crop", base_crop).order("stage_order").execute()
            growth_stages = stages_result.data or []

        if not growth_stages:
            block_plans.append({
                "block": block, "items": [], "npk_profile": (0, 0, 0),
                "crop_type": "annual", "missing_stages": True,
            })
            continue

        # Crop type
        crop_req = sb.table("crop_requirements").select("crop_type").eq("crop", crop).limit(1).execute()
        crop_type = "annual"
        if crop_req.data:
            crop_type = crop_req.data[0].get("crop_type", "annual") or "annual"
        elif base_crop != crop:
            crop_req = sb.table("crop_requirements").select("crop_type").eq("crop", base_crop).limit(1).execute()
            if crop_req.data:
                crop_type = crop_req.data[0].get("crop_type", "annual") or "annual"

        # Age factors
        age_factors = None
        if crop_type == "perennial" and block.get("tree_age"):
            af_result = sb.table("perennial_age_factors").select("*").eq("crop", crop).execute()
            if not af_result.data and base_crop != crop:
                af_result = sb.table("perennial_age_factors").select("*").eq("crop", base_crop).execute()
            age_factors = af_result.data or None

        # Calculate corrective build-up targets from linked soil analysis
        corrective_items = None
        soil_analysis_id = block.get("soil_analysis_id")
        if soil_analysis_id:
            try:
                sa = sb.table("soil_analyses").select(
                    "soil_values, norms_snapshot"
                ).eq("id", soil_analysis_id).limit(1).execute()
                if sa.data:
                    soil_values = sa.data[0].get("soil_values") or {}
                    snapshot = sa.data[0].get("norms_snapshot") or {}
                    suff_rows = snapshot.get("sufficiency") or []
                    param_rows = (
                        sb.table("soil_parameter_map").select("*").execute().data or []
                    )
                    crop_overrides = snapshot.get("crop_overrides") or []
                    ct = calculate_corrective_targets(
                        soil_values=soil_values,
                        nutrient_targets=targets,
                        sufficiency_rows=suff_rows,
                        param_map_rows=param_rows,
                        crop_override_rows=crop_overrides or None,
                    )
                    corrective_items = ct.get("corrective_items") or None
            except Exception:
                pass

        # Generate feeding plan
        items = generate_feeding_plan(
            nutrient_targets=targets,
            growth_stages=growth_stages,
            crop_type=crop_type,
            tree_age=block.get("tree_age"),
            age_factors=age_factors,
            field_area_ha=block.get("area_ha"),
            corrective_items=corrective_items,
        )

        # Load field constraints
        field_data = None
        if block.get("field_id"):
            try:
                field_result = sb.table("fields").select(
                    "accepted_methods, irrigation_type, fertigation_months"
                ).eq("id", block["field_id"]).execute()
                if field_result.data:
                    field_data = field_result.data[0]
            except Exception:
                pass

        infrastructure = None
        farmer_methods = None
        if field_data:
            irr = field_data.get("irrigation_type")
            if irr and irr != "none":
                infrastructure = [irr]
            elif irr == "none":
                infrastructure = []
            farmer_methods = field_data.get("accepted_methods") or None

        # Validate methods
        try:
            cam_result = sb.table("crop_application_methods").select("*").eq("crop", crop).execute()
            if not cam_result.data and base_crop != crop:
                cam_result = sb.table("crop_application_methods").select("*").eq("crop", base_crop).execute()
            if cam_result.data:
                items = validate_methods(
                    items, cam_result.data,
                    infrastructure=infrastructure,
                    accepted_methods=farmer_methods,
                )
        except Exception:
            pass

        # Constrain fertigation months
        if field_data and field_data.get("fertigation_months"):
            fert_months = set(field_data["fertigation_months"])
            for item in items:
                if item.get("method") == "fertigation":
                    target_month = item.get("month_target")
                    if target_month and target_month not in fert_months:
                        available = item.get("available_methods", [])
                        fallback = "broadcast" if "broadcast" in available else (available[0] if available else "broadcast")
                        item["method"] = fallback
                        item["method_note"] = f"Fertigation unavailable in month {target_month}, using {fallback}"

        # NPK profile
        total_n = sum(item.get("n_kg_ha", 0) for item in items if item.get("method") not in FOLIAR_METHODS)
        total_p = sum(item.get("p_kg_ha", 0) for item in items if item.get("method") not in FOLIAR_METHODS)
        total_k = sum(item.get("k_kg_ha", 0) for item in items if item.get("method") not in FOLIAR_METHODS)

        block_plans.append({
            "block": block,
            "items": items,
            "crop_type": crop_type,
            "npk_profile": (total_n, total_p, total_k),
        })

    return block_plans


def optimize_blend_for_group(template_items: list[dict], materials_df, batch_size: float, c_idx: int, min_pct: float) -> dict | None:
    """Run the LP optimizer for a blend group's average nutrient profile.

    Takes the template items for a group, averages their nutrient profile,
    converts to percentage targets, and runs the optimizer.

    Returns dict with recipe, nutrients, cost_per_ton, sa_notation, or None if infeasible.
    """
    from app.services.optimizer import run_optimizer, find_closest_blend
    from app.services.notation import pct_to_sa_notation
    from app.services.material_loader import build_recipe, build_nutrients, DB_TO_UPPER

    if not template_items:
        return None

    # Calculate average nutrient kg/ha across template items (non-foliar only)
    non_foliar = [it for it in template_items if it.get("method") not in FOLIAR_METHODS]
    if not non_foliar:
        return None

    # Total nutrients across all applications in this group
    total_nutrients = {}
    for nut in ["n", "p", "k", "ca", "mg", "s"]:
        total_nutrients[nut] = sum(item.get(f"{nut}_kg_ha", 0) or 0 for item in non_foliar)

    # Convert kg/ha to percentage targets for a 1000kg blend
    # We need to figure out the application rate first
    total_nutrient_kg = sum(total_nutrients.values())
    if total_nutrient_kg < 0.1:
        return None

    # Estimate blend rate: typical blends are 20-35% total nutrients
    # Use 25% as default → rate = total_nutrients / 0.25
    rate_kg_ha = round(total_nutrient_kg / 0.25)

    # Convert to percentage targets
    targets = {}
    for nut, kg in total_nutrients.items():
        if kg > 0.01:
            pct = kg / rate_kg_ha * 100
            targets[DB_TO_UPPER.get(nut, nut.upper())] = round(pct, 3)

    if not targets:
        return None

    # Run optimizer
    try:
        res = run_optimizer(targets, materials_df, batch_size, c_idx, min_pct)
        exact = True
        scale = 1.0
        if not res.success:
            exact = False
            res, scale = find_closest_blend(targets, materials_df, batch_size, c_idx, min_pct)
            if res is None or not res.success:
                return None

        amounts = res.x.tolist()
        recipe = build_recipe(materials_df, amounts, batch_size)
        nutrients = build_nutrients(materials_df, amounts, targets, batch_size)
        cost_per_ton = sum(r["cost"] for r in recipe) / (batch_size / 1000) if batch_size else 0

        npk = {r["nutrient"]: r["actual"] for r in nutrients if r["nutrient"] in ("N", "P", "K")}
        secondary = {r["nutrient"]: r["actual"] for r in nutrients if r["nutrient"] not in ("N", "P", "K") and targets.get(r["nutrient"], 0) > 0}
        sa_notation, international = pct_to_sa_notation(
            npk.get("N", 0), npk.get("P", 0), npk.get("K", 0),
            secondary_pcts=secondary if secondary else None,
        )

        return {
            "recipe": recipe,
            "nutrients": nutrients,
            "cost_per_ton": round(cost_per_ton, 2),
            "sa_notation": sa_notation,
            "international_notation": international,
            "rate_kg_ha": rate_kg_ha,
            "exact": exact,
            "scale": round(scale, 4),
        }
    except Exception:
        return None
