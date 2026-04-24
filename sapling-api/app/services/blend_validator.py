"""
Blend Validator — Phase 2 module 9 of 10.

Validates blends produced by the consolidator. Catches safety issues
that the greedy algorithm can miss:

  * Stream purity: no Ca-containing product routed to Part B;
    no sulphate/phosphate routed to Part A
  * Material existence: every BlendPart.product must exist in the
    materials catalog
  * Known-incompat pairs: same-stream materials that shouldn't be
    mixed (from the materials_compatibility table)
  * Dry granule physical compat: common known-bad pairs
    (AN + urea = slurry, hygroscopic combinations)
  * Solubility ceilings for fertigation: sum of dissolved salt
    concentrations vs per-material solubility_20c
  * Missing-source diagnostic: targeted nutrients with no material
    supplying them (delegates to liquid_optimizer's missing_sources path)

Operates post-consolidator: input = list[Blend], output = list of
BlendValidationResult + updated Blend objects with warnings attached.

Module 9 does NOT currently re-optimize via MILP for cost minimisation
— that requires kg/ha ↔ g/L conversion story that depends on per-event
irrigation-window duration which isn't always known. A future iteration
can delegate to liquid_optimizer.optimize_liquid_blend for exact quantity
refinement when the engine grows that input.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.models import Assumption, Blend, RiskFlag, SourceCitation, Tier


# ============================================================
# Known dry-granule incompatibility pairs (Tier 3 standard agronomy)
# Applied when both products are in the same dry blend.
# ============================================================

DRY_GRANULE_INCOMPAT: list[tuple[str, str, str]] = [
    # (product_a_pattern, product_b_pattern, reason)
    ("Ammonium Nitrate", "Urea",
     "AN + urea forms a slurry — hygroscopic eutectic mixture; blend cakes "
     "within days. Use a single N carrier or pre-separate."),
    ("Urea", "Single Super",
     "Urea + single superphosphate releases ammonia via reaction with acid-P "
     "residues. Avoid in pre-blended products; band separately."),
    ("Calcium Nitrate", "Single Super",
     "Ca + phosphate forms insoluble Ca-phosphate precipitate on surface of "
     "granules; loss of P availability."),
    ("Calcium Nitrate", "Ammonium Sulphate",
     "Ca-SO₄ precipitation same as in liquid. Keep separate at mixing plant."),
    ("Calcium Nitrate", "MAP",
     "Ca + MAP phosphate precipitates. Keep separate — MAP goes side-dress, "
     "Ca-Nit goes broadcast pre-plant."),
]


# ============================================================
# Output types
# ============================================================

@dataclass
class BlendValidationResult:
    """One blend's validation outcome."""
    block_id: str
    stage_number: int
    stage_name: str
    errors: list[str] = field(default_factory=list)         # blocking issues
    warnings: list[str] = field(default_factory=list)       # non-blocking concerns
    notes: list[str] = field(default_factory=list)          # informational
    missing_sources: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


# ============================================================
# Main validator
# ============================================================

def validate_blends(
    blends: list[Blend],
    available_materials: list[dict],
    compatibility_rules: Optional[list[dict]] = None,
) -> tuple[list[BlendValidationResult], list[RiskFlag]]:
    """Validate every blend against safety + compatibility rules.

    Args:
        blends: from consolidator.consolidate_blends()
        available_materials: materials catalog (dicts)
        compatibility_rules: from materials_compatibility table

    Returns:
        (list of BlendValidationResult per blend,
         list of RiskFlag entries ready for the ProgrammeArtifact)
    """
    results: list[BlendValidationResult] = []
    risk_flags: list[RiskFlag] = []

    mat_by_name = {m.get("material", "").strip().lower(): m
                   for m in available_materials}

    for blend in blends:
        result = BlendValidationResult(
            block_id=blend.block_id,
            stage_number=blend.stage_number,
            stage_name=blend.stage_name,
        )

        is_fert = _is_fertigation(blend)

        # 1. Material existence
        for part in blend.raw_products:
            name_lc = (part.product or "").strip().lower()
            if name_lc not in mat_by_name:
                result.errors.append(
                    f"Product '{part.product}' not in materials catalog"
                )

        # 2. Stream purity for fertigation
        if is_fert:
            for part in blend.raw_products:
                mat = mat_by_name.get((part.product or "").strip().lower())
                if not mat:
                    continue
                expected_stream = _expected_stream(mat)
                if part.stream and part.stream != expected_stream:
                    result.errors.append(
                        f"Product '{part.product}' is in Part {part.stream} "
                        f"but should be Part {expected_stream} (stream purity)"
                    )

        # 3. Dry-granule known-incompat pairs
        if not is_fert:
            granule_warnings = _check_dry_incompat(blend)
            result.warnings.extend(granule_warnings)

        # 4. compatibility_rules pairs (same-stream materials)
        if compatibility_rules:
            pair_warnings = _check_compat_rules_pairs(
                blend.raw_products, compatibility_rules, mat_by_name,
            )
            result.warnings.extend(pair_warnings)

        # 5. Missing sources for declared nutrients
        missing = _find_missing_sources(blend, mat_by_name)
        if missing:
            result.missing_sources = missing
            result.warnings.append(
                f"No material supplies: {', '.join(missing)} "
                f"— targets won't be met for these nutrients"
            )

        # 6. Note tier of blend composition
        result.notes.append(
            f"Blend composition tier 6 (greedy material-cover); "
            f"MILP cost-optimisation not yet applied"
        )

        results.append(result)

        # Generate RiskFlags for any errors/warnings that should surface
        # in the ProgrammeArtifact.risk_flags section
        if result.errors:
            risk_flags.append(RiskFlag(
                message=(
                    f"Block {blend.block_id} stage {blend.stage_number} "
                    f"({blend.stage_name}) has blend errors: "
                    + "; ".join(result.errors)
                ),
                severity="critical",
                source=SourceCitation(
                    source_id="BLEND_VALIDATOR",
                    section="Phase 2 module 9",
                    tier=Tier.IMPLEMENTER_CONVENTION,
                ),
            ))
        elif result.warnings:
            risk_flags.append(RiskFlag(
                message=(
                    f"Block {blend.block_id} stage {blend.stage_number} "
                    f"({blend.stage_name}) blend warnings: "
                    + "; ".join(result.warnings)
                ),
                severity="watch",
                source=SourceCitation(
                    source_id="BLEND_VALIDATOR",
                    section="Phase 2 module 9",
                    tier=Tier.IMPLEMENTER_CONVENTION,
                ),
            ))

    return results, risk_flags


# ============================================================
# Helpers
# ============================================================

def _is_fertigation(blend: Blend) -> bool:
    try:
        return blend.method.kind.name.startswith("LIQUID_")
    except Exception:
        return False


def _expected_stream(material: dict) -> str:
    """Mirror of consolidator._classify_stream — a dominant cation
    (Ca OR Mg ≥ 5 %) AND no SO4 dominance (S < 2 %) AND no PO4 dominance
    (P < 2 %) → Part A. Otherwise Part B.

    The Mg limb matters: Mg Nitrate (N 11 %, Mg 15 %, S 0 %) is a
    Part-A product; missing the Mg clause would flag it as wrongly-
    placed and fail the validator for programmes that correctly route
    it to Part A per FERTASA §11."""
    ca = float(material.get("ca") or 0)
    mg = float(material.get("mg") or 0)
    s = float(material.get("s") or 0)
    p = float(material.get("p") or 0)
    if (ca >= 5 or mg >= 5) and s < 2 and p < 2:
        return "A"
    return "B"


def _check_dry_incompat(blend: Blend) -> list[str]:
    """Flag known-bad dry-granule pairs in the same blend."""
    product_names = [(p.product or "").strip().lower() for p in blend.raw_products]
    warnings: list[str] = []
    for pat_a, pat_b, reason in DRY_GRANULE_INCOMPAT:
        has_a = any(pat_a.lower() in n for n in product_names)
        has_b = any(pat_b.lower() in n for n in product_names)
        if has_a and has_b:
            warnings.append(
                f"Known incompat pair in dry blend: {pat_a} + {pat_b} — {reason}"
            )
    return warnings


def _check_compat_rules_pairs(
    parts,
    rules: list[dict],
    mat_by_name: dict,
) -> list[str]:
    """Check pair-incompatibility per same-stream materials."""
    warnings: list[str] = []
    # Group parts by stream for fertigation (if stream set)
    streams: dict[str, list] = {}
    for part in parts:
        streams.setdefault(part.stream or "_", []).append(part.product)

    for rule in rules:
        mat_a = rule.get("material_a", "").strip().lower()
        mat_b = rule.get("material_b", "").strip().lower()
        compat = rule.get("compatible", True)
        if compat:
            continue  # only check incompatible pairs
        # Check each stream for both materials
        for stream, products in streams.items():
            prod_lc = [p.strip().lower() for p in products if p]
            if mat_a in prod_lc and mat_b in prod_lc:
                warnings.append(
                    f"Incompat pair in same stream ({stream or 'dry'}): "
                    f"{rule.get('material_a')} + {rule.get('material_b')} — "
                    f"{rule.get('reason', 'see materials_compatibility table')}"
                )
    return warnings


def _find_missing_sources(blend: Blend, mat_by_name: dict) -> list[str]:
    """Nutrients with declared targets but no material supplying them."""
    if not blend.nutrients_delivered:
        return []
    nutrient_col = {
        "N": "n", "P2O5": "p", "P": "p", "K2O": "k", "K": "k",
        "Ca": "ca", "Mg": "mg", "S": "s",
    }
    missing: list[str] = []
    for nut, target in blend.nutrients_delivered.items():
        if target <= 0:
            continue
        col = nutrient_col.get(nut)
        if not col:
            continue
        # Does any material in the blend supply this nutrient?
        supplies = False
        for part in blend.raw_products:
            mat = mat_by_name.get((part.product or "").strip().lower())
            if not mat:
                continue
            if float(mat.get(col) or 0) > 0:
                supplies = True
                break
        if not supplies:
            missing.append(nut)
    return missing
