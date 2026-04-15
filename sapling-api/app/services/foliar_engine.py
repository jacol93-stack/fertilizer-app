"""Foliar spray recommendation engine.

Takes a nutrient deficit and matches it against the product catalog.
Calculates application rates, dilution, and spray volumes.
"""

NUTRIENTS = ["n", "p", "k", "ca", "mg", "s", "fe", "b", "mn", "zn", "mo", "cu"]


def recommend_foliar_products(
    deficit: dict[str, float],
    products: list[dict],
    crop: str | None = None,
    max_products: int = 3,
) -> list[dict]:
    """Match nutrient deficit to catalog products.

    Args:
        deficit: nutrient requirements in kg/ha
            e.g. {"n": 50, "p": 10, "k": 30, "zn": 2}
        products: from liquid_products table (foliar type)
        crop: optional crop name for crop-specific matching
        max_products: max number of products to recommend

    Returns:
        List of recommended products, each with:
        - product info, coverage %, application rate, what's covered/remaining
    """
    if not deficit or not products:
        return []

    # Filter to relevant products
    candidates = []
    for prod in products:
        if prod.get("product_type") not in ("foliar", "fertigation"):
            continue

        # Score: how well does this product cover the deficit?
        score = _score_product(prod, deficit)
        if score > 0:
            candidates.append({"product": prod, "score": score})

    # If crop specified, boost crop-specific products
    if crop:
        crop_lower = crop.lower()
        for c in candidates:
            target_crops = c["product"].get("target_crops") or []
            if any(crop_lower in tc.lower() for tc in target_crops):
                c["score"] *= 1.5  # 50% boost for crop match

    # Sort by score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    # Build recommendations — greedy: pick best, subtract coverage, repeat
    remaining = dict(deficit)
    recommendations = []

    for c in candidates:
        if len(recommendations) >= max_products:
            break

        prod = c["product"]
        coverage = _calculate_coverage(prod, remaining)
        if coverage["coverage_pct"] < 5:
            continue  # Skip if it barely covers anything

        # Calculate application rate to cover the primary deficit nutrient
        rate = _calculate_application_rate(prod, remaining)
        if not rate:
            continue

        actual_rate = rate["rate_kg_ha"]

        # If rate was capped, recalculate coverage at the actual (capped) rate
        if rate.get("rate_was_capped"):
            capped_delivered = {}
            capped_covered = []
            capped_remaining = []
            total_needs = 0
            total_covered = 0
            for nut in NUTRIENTS:
                need = remaining.get(nut, 0)
                if need <= 0:
                    continue
                total_needs += 1
                prod_conc = float(prod.get(nut, 0))
                delivered = actual_rate * prod_conc / 1000
                capped_delivered[nut] = round(delivered, 3)
                if delivered >= need * 0.5:
                    capped_covered.append(nut.upper())
                    total_covered += 1
                else:
                    capped_remaining.append(nut.upper())
            coverage_pct = round((total_covered / total_needs * 100) if total_needs > 0 else 0, 1)
            delivered_kg_ha = capped_delivered
            nutrients_covered = capped_covered
            nutrients_remaining = capped_remaining
        else:
            coverage_pct = coverage["coverage_pct"]
            delivered_kg_ha = coverage["delivered_kg_ha"]
            nutrients_covered = coverage["covered"]
            nutrients_remaining = coverage["remaining"]

        rec = {
            "product_name": prod["name"],
            "product_type": prod.get("product_type"),
            "analysis_unit": prod.get("analysis_unit", "g/kg"),
            "coverage_pct": coverage_pct,
            "nutrients_covered": nutrients_covered,
            "nutrients_remaining": nutrients_remaining,
            "application_rate_kg_ha": actual_rate,
            "application_rate_l_ha": rate.get("rate_l_ha"),
            "dilution": rate.get("dilution"),
            "spray_volume_l_ha": rate.get("spray_volume_l_ha"),
            "notes": prod.get("notes", ""),
        }
        if rate.get("rate_was_capped"):
            rec["rate_capped"] = True
        recommendations.append(rec)

        # Subtract what this product actually delivers
        for nut, delivered in delivered_kg_ha.items():
            if nut in remaining:
                remaining[nut] = max(0, remaining[nut] - delivered)

        # Remove fully covered nutrients
        remaining = {k: v for k, v in remaining.items() if v > 0.01}
        if not remaining:
            break

    # Add final remaining deficit summary
    return {
        "recommendations": recommendations,
        "remaining_deficit": remaining,
        "fully_covered": len(remaining) == 0,
    }


def _score_product(product: dict, deficit: dict) -> float:
    """Score how well a product covers a deficit. Higher = better match."""
    score = 0
    total_deficit_nutrients = 0

    for nut in NUTRIENTS:
        need = deficit.get(nut, 0)
        if need <= 0:
            continue
        total_deficit_nutrients += 1

        # Product concentration (g/kg or g/l)
        has = float(product.get(nut, 0))
        if has > 0:
            score += 1  # covers this nutrient
            # Bonus for higher concentration
            score += min(has / 100, 0.5)

    # Penalize if product has nutrients the deficit doesn't need (waste)
    waste = 0
    for nut in NUTRIENTS:
        if deficit.get(nut, 0) <= 0 and float(product.get(nut, 0)) > 1:
            waste += 1
    score -= waste * 0.2

    return score


def _calculate_coverage(product: dict, deficit: dict) -> dict:
    """Calculate what percentage of the deficit this product covers at optimal rate."""
    covered = []
    remaining = []
    delivered_kg_ha = {}

    # Find the optimal application rate — enough to cover the primary deficit
    primary_nut = max(deficit, key=lambda k: deficit[k]) if deficit else None
    if not primary_nut:
        return {"coverage_pct": 0, "covered": [], "remaining": [], "delivered_kg_ha": {}}

    conc = float(product.get(primary_nut, 0))  # g/kg or g/l
    need_kg = deficit[primary_nut]

    if conc <= 0:
        # Product doesn't have the primary nutrient — use a different target
        for nut in NUTRIENTS:
            if deficit.get(nut, 0) > 0 and float(product.get(nut, 0)) > 0:
                primary_nut = nut
                conc = float(product.get(nut, 0))
                need_kg = deficit[nut]
                break

    if conc <= 0:
        return {"coverage_pct": 0, "covered": [], "remaining": [], "delivered_kg_ha": {}}

    # Rate in kg product per ha to deliver the needed amount of primary nutrient
    rate_kg_ha = need_kg / (conc / 1000)  # conc is g/kg, so /1000 = kg/kg

    # What does this rate deliver for all nutrients?
    total_needs = 0
    total_covered = 0

    for nut in NUTRIENTS:
        need = deficit.get(nut, 0)
        if need <= 0:
            continue
        total_needs += 1

        prod_conc = float(product.get(nut, 0))
        delivered = rate_kg_ha * prod_conc / 1000  # kg/ha delivered
        delivered_kg_ha[nut] = round(delivered, 3)

        if delivered >= need * 0.5:  # At least 50% covered
            covered.append(nut.upper())
            total_covered += 1
        else:
            remaining.append(nut.upper())

    coverage_pct = round((total_covered / total_needs * 100) if total_needs > 0 else 0, 1)

    return {
        "coverage_pct": coverage_pct,
        "covered": covered,
        "remaining": remaining,
        "delivered_kg_ha": delivered_kg_ha,
    }


def _calculate_application_rate(product: dict, deficit: dict) -> dict | None:
    """Calculate the practical application rate for a product."""
    # Find the best nutrient to optimize rate for
    best_nut = None
    best_ratio = 0

    for nut in NUTRIENTS:
        need = deficit.get(nut, 0)
        conc = float(product.get(nut, 0))
        if need > 0 and conc > 0:
            # Ratio of concentration to need — higher means more efficient
            ratio = conc / need
            if ratio > best_ratio:
                best_ratio = ratio
                best_nut = nut

    if not best_nut:
        return None

    conc = float(product.get(best_nut, 0))  # g/kg or g/l
    need_kg = deficit[best_nut]

    # kg of product per ha
    rate_kg_ha = round(need_kg / (conc / 1000), 2)

    # Cap at reasonable foliar spray rates — applies to all product types
    # since this engine is specifically for foliar application
    rate_was_capped = False
    if rate_kg_ha > 30:
        rate_kg_ha = 30  # Max 30 kg/ha for any foliar spray
        rate_was_capped = True

    result = {
        "rate_kg_ha": rate_kg_ha,
        "primary_nutrient": best_nut.upper(),
        "rate_was_capped": rate_was_capped,
    }

    # Liquid rate
    sg = product.get("sg")
    if sg and float(sg) > 0:
        result["rate_l_ha"] = round(rate_kg_ha / float(sg), 2)

    # Typical spray volumes and dilution
    spray_vol = product.get("spray_volume_l_ha")
    if spray_vol and float(spray_vol) > 0:
        result["spray_volume_l_ha"] = float(spray_vol)
        result["dilution"] = f"{rate_kg_ha:.1f} kg in {int(spray_vol)} L water/ha"
    else:
        # Default spray volumes by product type
        if product.get("product_type") == "foliar":
            default_vol = 500  # L/ha typical foliar spray volume
            result["spray_volume_l_ha"] = default_vol
            result["dilution"] = f"{rate_kg_ha:.1f} kg in {default_vol} L water/ha"

    return result
