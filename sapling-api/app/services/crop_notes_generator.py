"""Crop note generator — produces qualitative agronomy notes per block.

Inputs: crop name + crop_calc_flags row + crop_requirements row.
Output: list of `CropNote` (matching `programme_artifact.CropNote`)
ready to render in the new-direction report's Notes section.

Why this exists separately:
  * `crop_calc_flags` schema currently only has `skip_cation_ratio_path`,
    but agronomic reality has many more flags (no_chloride_fertilisers,
    sulfur_critical, acid_intolerant, photoperiod_sensitive,
    high_ca_demand_for_quality, n_protein_cap, etc.). Until the schema
    extends, we infer those flags from a hardcoded crop knowledge base
    here — sourced from research-agent findings + memory entries.
  * The same notes feed the future product selector as hard filters:
    `kind='no_chloride_fertilisers'` → drop KCl/MOP from candidates,
    `kind='sulfur_critical'` → enforce minimum S in blend.

Sources for the per-crop entries below are cited inline in the
`CropNote.source_citation` field — every entry traces to a specific
T1/T2/T3 reference.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CropNoteData:
    """Internal note shape — converted to the Pydantic CropNote at the
    artifact boundary."""
    kind: str
    headline: str
    detail: str
    severity: str = "info"  # 'info' | 'watch' | 'warn'
    source_citation: Optional[str] = None


# ── Knowledge base ───────────────────────────────────────────────────


# Per-crop notes keyed by canonical crop name. Cultivar variants
# inherit from genus unless they have their own entry.
CROP_NOTE_KB: dict[str, list[CropNoteData]] = {
    # ── Subtropical / tropical fruit ────────────────────────────────
    "Avocado": [
        CropNoteData(
            kind="chloride_sensitive",
            headline="Avocado is acutely chloride-sensitive.",
            detail=(
                "Avoid KCl/MOP as a K source — leaf Cl > 0.25% causes "
                "leaf burn and yield loss. Use SOP (potassium sulphate) "
                "or KNO3 instead. Verify irrigation water Cl."
            ),
            severity="warn",
            source_citation="Köhne 1990 SAAGA YB 13 + Storey & Walker 1999 SAJEV. T1.",
        ),
    ],
    "Macadamia": [
        CropNoteData(
            kind="elevated_zn_b_demand",
            headline="Macadamia has elevated Zn + B requirements vs typical orchard crops.",
            detail=(
                "B deficiency causes blank nuts and poor set; Zn deficiency "
                "limits early-season vegetative vigour. Foliar Zn + B at "
                "flowering and again at nut set is canonical SA practice."
            ),
            severity="info",
            source_citation="FERTASA 5.8.1 + Schoeman 2017 SAMAC. T1.",
        ),
    ],
    "Pecan": [
        CropNoteData(
            kind="elevated_zn_b_demand",
            headline="Pecan shares mac's elevated Zn + B requirement.",
            detail=(
                "Zn deficiency is the most common pecan nutritional disorder. "
                "Foliar Zn at bud break and 6 weeks later. B for nut fill."
            ),
            severity="info",
            source_citation="FERTASA 5.8.2 Schmidt 2021 + NMSU H-658. T1+T2.",
        ),
    ],

    # ── Berry / niche ───────────────────────────────────────────────
    "Kiwi": [
        CropNoteData(
            kind="no_chloride_fertilisers",
            headline="Kiwi is acutely chloride-sensitive — do not apply KCl/MOP.",
            detail=(
                "KCl/MOP damages kiwifruit roots within weeks of application. "
                "Use SOP (potassium sulphate) for K. Source background Cl from "
                "irrigation water only — kiwi paradoxically requires Cl in "
                "leaf tissue but cannot tolerate fertiliser-form Cl."
            ),
            severity="warn",
            source_citation="OSU PNW 507 p.12 + Smith/Clark/Holland 1987 NZJCHS. T1+T3.",
        ),
        CropNoteData(
            kind="acid_preferring",
            headline="Kiwi prefers slightly acidic soil (pH 5.5-6.5 H2O).",
            detail=(
                "Mn toxicity below pH 5.2; Mn deficiency above pH 6.8. "
                "Avoid over-liming. Cation-ratio path skipped for this crop."
            ),
            severity="info",
            source_citation="Hill Labs Kiwifruit Crop Guide. T1.",
        ),
    ],
    "Blueberry": [
        CropNoteData(
            kind="no_chloride_fertilisers",
            headline="Blueberry is acutely chloride-sensitive.",
            detail=(
                "Avoid KCl/MOP — Cl-bearing fertilisers damage blueberry "
                "roots. Use SOP (potassium sulphate). Blueberry is calcifuge — "
                "low pH (4.5-5.5 H2O) is the operating envelope."
            ),
            severity="warn",
            source_citation="MSU E2011 + BC Ministry Blueberry Production Guide 2017. T2.",
        ),
        CropNoteData(
            kind="acid_intolerant_to_high_ph",
            headline="Blueberry requires acid soil (pH 4.5-5.5 H2O / 4.0-4.5 KCl).",
            detail=(
                "Above pH 5.5, Fe-deficiency chlorosis sets in and the stand "
                "declines. Lime to raise pH is normally CONTRAINDICATED."
            ),
            severity="warn",
            source_citation="MSU E2011. T2.",
        ),
    ],
    "Rooibos": [
        CropNoteData(
            kind="acid_obligate",
            headline="Rooibos is fynbos — acid soil obligate (pH 4.5-5.5 KCl).",
            detail=(
                "Aspalathus linearis cannot tolerate pH > 6.5. Lime is "
                "actively damaging. Engine zero-input rule applies — N/P/K "
                "applications are agronomically contraindicated."
            ),
            severity="warn",
            source_citation="SARC 2020 + Hawkins & Lambers 2011. T1.",
        ),
        CropNoteData(
            kind="n_fixation_active",
            headline="Rooibos fixes its own nitrogen via fynbos Rhizobium.",
            detail=(
                "Crotalarieae legume — applied N is unnecessary and "
                "competes with the symbiosis. BNF cap ~50 kg N/ha/yr."
            ),
            severity="info",
            source_citation="Spriggs & Dakora 2009 Symbiosis. T1.",
        ),
    ],
    "Honeybush": [
        CropNoteData(
            kind="acid_obligate",
            headline="Honeybush is fynbos — acid obligate, similar to rooibos.",
            detail=(
                "Cyclopia genus tolerates pH 4.0-5.5 KCl. Lime damages "
                "stand. Zero-input rule applies."
            ),
            severity="warn",
            source_citation="DAFF Honeybush Production Guide 2019. T1.",
        ),
        CropNoteData(
            kind="n_fixation_active",
            headline="Honeybush fixes its own nitrogen.",
            detail="Cyclopia legume with effective Rhizobium symbiosis.",
            severity="info",
            source_citation="Joubert et al. 2008 Genet. Resour. Crop Evol. T1.",
        ),
    ],

    # ── Vegetables ──────────────────────────────────────────────────
    "Garlic": [
        CropNoteData(
            kind="sulfur_critical",
            headline="Garlic is high-sulfur — S drives both yield and flavour.",
            detail=(
                "Ensure ≥30 kg S/ha applied. Allicin biosynthesis depends "
                "directly on S supply. Optimum response zone is 30-45 kg S/ha; "
                "75 kg S/ha gave maximum bulb yield in cited trials."
            ),
            severity="warn",
            source_citation="Nguyen et al. 2022 Plants 11:2571 + Reddy 2017. T2+T3.",
        ),
        CropNoteData(
            kind="acid_intolerant",
            headline="Garlic requires near-neutral soil (pH > 6.0 H2O).",
            detail="Below pH 5.5 (KCl 4.9), yield declines sharply.",
            severity="watch",
            source_citation="UC ANR Garlic Production + Graceland SA. T2.",
        ),
    ],
    "Onion": [
        CropNoteData(
            kind="photoperiod_sensitive",
            headline="Onion cultivar must match the latitude — short-day vs intermediate.",
            detail=(
                "SA growers should select the right photoperiod class for "
                "their planting date. Short-day cultivars bulb under 11-12 hr "
                "light; intermediates under 13-14 hr."
            ),
            severity="info",
            source_citation="DAFF Onion Production Guide. T1.",
        ),
    ],
    "Potato": [
        CropNoteData(
            kind="acid_for_quality",
            headline="Potato benefits from low pH (4.8-5.5 KCl) for scab suppression.",
            detail=(
                "Streptomyces scabies (common scab) is suppressed below "
                "pH 5.5 KCl. Avoid liming above this band on scab-prone soils."
            ),
            severity="info",
            source_citation="Potatoes SA + ARC LNR Roodeplaat. T1.",
        ),
    ],
    "Tomato": [
        CropNoteData(
            kind="high_ca_demand_for_quality",
            headline="Tomato is Ca-critical — blossom end rot is the canonical disorder.",
            detail=(
                "Foliar Ca during fruit cell expansion + sustained transpiration "
                "(stable irrigation) prevent BER. Soil-Ca alone is insufficient — "
                "the problem is Ca PARTITION to the fruit, not soil supply."
            ),
            severity="warn",
            source_citation="UF/IFAS HS739 + UC ANR Tomato Production. T2.",
        ),
    ],
    "Pepper (Bell)": [
        CropNoteData(
            kind="high_ca_demand_for_quality",
            headline="Bell pepper shares tomato's BER risk profile.",
            detail="Same Ca-partition mechanism. Foliar Ca during fruit cell expansion.",
            severity="warn",
            source_citation="UF/IFAS HS732. T2.",
        ),
    ],
    "Lettuce": [
        CropNoteData(
            kind="ca_critical_quality",
            headline="Lettuce tipburn is Ca-deficiency in the youngest leaves.",
            detail=(
                "Stable irrigation + foliar Ca during head formation "
                "prevent tipburn. Soil-Ca is rarely the bottleneck — "
                "Ca partition to the rapidly-expanding inner leaves is."
            ),
            severity="warn",
            source_citation="UC ANR Lettuce Production. T2.",
        ),
    ],
    "Carrot": [
        CropNoteData(
            kind="boron_narrow_band",
            headline="Carrot has a narrow B band (0.5-1.0 ppm hot-water).",
            detail=(
                "Below 0.5 ppm causes cavity spot; above 2 ppm causes "
                "root cracking and splitting. Don't over-apply B."
            ),
            severity="warn",
            source_citation="UC ANR Carrot Production. T2.",
        ),
        CropNoteData(
            kind="chloride_sensitive_at_planting",
            headline="Avoid KCl/MOP at carrot planting.",
            detail=(
                "Pre-plant KCl depresses carrot germination. Apply K as "
                "K-sulphate or K-nitrate, or top-dress KCl after stand established."
            ),
            severity="watch",
            source_citation="Starke Ayres Carrot 2019. T1.",
        ),
    ],

    # ── Cereals + grains ────────────────────────────────────────────
    "Barley": [
        CropNoteData(
            kind="n_protein_cap",
            headline="Malting barley has a hard N ceiling for protein quality.",
            detail=(
                "SAB Maltings spec: grain protein 9.5-11.5%. N applications "
                "above ~80 kg N/ha pre-anthesis push protein over spec — "
                "load downgraded to feed barley, ~30% price loss. "
                "Stop N applications by Z37 (flag-leaf emergence)."
            ),
            severity="warn",
            source_citation="SAB Maltings Producer Guide + ARC-SGI Barley Guideline. T1.",
        ),
    ],

    # ── Industrial / fibre ──────────────────────────────────────────
    "Tobacco": [
        CropNoteData(
            kind="chloride_sensitive_critical",
            headline="Tobacco is acutely Cl-sensitive — Cl destroys leaf burn quality.",
            detail=(
                "Avoid KCl/MOP; use SOP only. Soil-Cl > 30 mg/kg already "
                "compromises flue-cured leaf burn. Verify irrigation water Cl."
            ),
            severity="warn",
            source_citation="FERTASA 5.11 + NC State Tobacco Production. T1+T2.",
        ),
        CropNoteData(
            kind="nitrate_form_required",
            headline="Tobacco N must be in nitrate form by topping.",
            detail=(
                "FERTASA 5.11: at least 50% basic N as nitrate; ALL "
                "top-dressings as nitrate. Ammoniacal/urea N persisting "
                "into topping degrades cure quality."
            ),
            severity="warn",
            source_citation="FERTASA 5.11. T1.",
        ),
    ],

    # ── Wine grape (low-K-target rule) ──────────────────────────────
    "Wine Grape": [
        CropNoteData(
            kind="low_K_target_for_quality",
            headline="Wine grape K is capped TIGHT for wine quality.",
            detail=(
                "Excess K raises juice pH, damaging wine acidity, colour, "
                "and ageability. Soil K target 60-100 mg/kg max (region-"
                "specific). Tighter than table grape because juice pH "
                "matters for wine. Avoid luxury K consumption."
            ),
            severity="warn",
            source_citation="Raath SATI Ch 3 + Conradie SAJEV. T1.",
        ),
    ],

    # ── Legumes (universal n_fixation, plus crop-specifics) ─────────
    "Soybean": [
        CropNoteData(
            kind="n_fixation_active",
            headline="Soybean fixes its own N once nodulated.",
            detail=(
                "Bradyrhizobium japonicum inoculation mandatory in first "
                "soybean rotation. After nodulation, applied N suppresses "
                "fixation — engine should not auto-add starter N at high "
                "yields beyond a small starter dose."
            ),
            severity="info",
            source_citation="FERTASA 5.5.5 + Grain SA Soybean Guide. T1.",
        ),
        CropNoteData(
            kind="mo_responsive",
            headline="Soybean Mo seed treatment standard SA practice.",
            detail=(
                "Sodium molybdate seed treatment 35 g per 50 kg seed when "
                "soil Mo < 0.1 mg/kg or pH (KCl) < 5.5."
            ),
            severity="info",
            source_citation="FERTASA 5.5.5. T1.",
        ),
    ],
    "Bean (Dry)": [
        CropNoteData(
            kind="n_fixation_active",
            headline="Dry bean fixes its own N.",
            detail="Inoculate at planting; do not auto-apply N beyond starter.",
            severity="info",
            source_citation="FERTASA 5.5.2. T1.",
        ),
        CropNoteData(
            kind="boron_sensitive",
            headline="Dry bean is B-toxic — DO NOT apply soil B.",
            detail=(
                "FERTASA 5.5.2: 'B applications NOT recommended' — dry "
                "bean has narrowest B tolerance of any SA legume. Hard "
                "ceiling 1.5 mg/kg soil hot-water B."
            ),
            severity="warn",
            source_citation="FERTASA 5.5.2. T1.",
        ),
        CropNoteData(
            kind="no_n_at_flowering",
            headline="No N applications during dry-bean flowering — induces flower drop.",
            detail="FERTASA 5.5.2 explicit. Stop N by R5.",
            severity="warn",
            source_citation="FERTASA 5.5.2. T1.",
        ),
    ],
    "Groundnut": [
        CropNoteData(
            kind="n_fixation_active",
            headline="Groundnut fixes its own N.",
            detail="Bradyrhizobium inoculation; no applied N beyond starter.",
            severity="info",
            source_citation="FERTASA 5.5.3. T1.",
        ),
        CropNoteData(
            kind="ca_critical_pegging",
            headline="Groundnut needs Ca in the pegging zone for kernel quality.",
            detail=(
                "Apply 200-300 kg gypsum/ha at flowering (start of pegging) "
                "to lift pegging-zone Ca above 500 mg/kg. Critical for "
                "shell fill, popping, and blanchability."
            ),
            severity="warn",
            source_citation="FERTASA 5.5.3 + Manson 2013 SAJPS. T1.",
        ),
    ],
    "Lucerne": [
        CropNoteData(
            kind="n_fixation_active",
            headline="Lucerne fixes its own N — applied N stimulates grass competition.",
            detail=(
                "FERTASA 5.12.2: 0% applied N on established stands. "
                "Year-1 establishment can take 25-55 kg N/ha starter; "
                "after that, no N."
            ),
            severity="warn",
            source_citation="FERTASA 5.12.2. T1.",
        ),
        CropNoteData(
            kind="k_luxury_consumer",
            headline="Lucerne luxury-consumes K — caps the rate, not the response.",
            detail=(
                "Removes ~21 kg K/t DM at unlimited supply — replenish "
                "after every cut. Higher-than-typical K demand."
            ),
            severity="info",
            source_citation="FERTASA 5.12.2 + UC ANR 8287. T1+T2.",
        ),
    ],
}


def _note_from_flag(
    crop: str,
    column: str,
    value: object,
    row: dict,
) -> Optional[CropNoteData]:
    """Generate a fallback CropNote from a single flag column when the
    hardcoded KB doesn't already cover this kind for the crop.

    Used for crops where an agronomist sets a flag in the DB but no
    rich KB entry exists yet — the report still surfaces the rule,
    just with shorter prose."""
    src = str(row.get("source", "") or "")
    section = str(row.get("source_section", "") or "")
    citation = (src + (f" §{section}" if section else "")).strip() or None

    # Boolean flag → templated note
    if column == "no_chloride_fertilisers" and value is True:
        return CropNoteData(
            kind="no_chloride_fertilisers",
            headline=f"{crop} is acutely chloride-sensitive.",
            detail="Avoid KCl/MOP. Use SOP (potassium sulphate) or KNO3.",
            severity="warn", source_citation=citation,
        )
    if column == "chloride_sensitive" and value is True:
        return CropNoteData(
            kind="chloride_sensitive",
            headline=f"{crop} is chloride-sensitive at moderate levels.",
            detail="Verify irrigation water Cl + soil-Cl below the published threshold; minimise chloride-bearing fertiliser sources.",
            severity="watch", source_citation=citation,
        )
    if column == "sulfur_critical" and value is True:
        return CropNoteData(
            kind="sulfur_critical",
            headline=f"{crop} is high-sulphur — ensure adequate S supply.",
            detail="S drives both yield and quality. Confirm soil-S ≥ published threshold; supplement if low.",
            severity="warn", source_citation=citation,
        )
    if column == "acid_intolerant" and value is True:
        return CropNoteData(
            kind="acid_intolerant",
            headline=f"{crop} is acid-intolerant.",
            detail="Below pH (KCl) ≈ 5.0 yield declines sharply. Lime to pH target before establishment.",
            severity="watch", source_citation=citation,
        )
    if column == "acid_obligate" and value is True:
        return CropNoteData(
            kind="acid_obligate",
            headline=f"{crop} is acid-obligate — do not lime.",
            detail="pH > target actively damages stand. Engine excludes lime recommendations for this crop.",
            severity="warn", source_citation=citation,
        )
    if column == "salt_tolerant" and value is True:
        return CropNoteData(
            kind="salt_tolerant",
            headline=f"{crop} is salt-tolerant.",
            detail="Tolerates high Na / Cl in irrigation + soil compared to typical crops; salinity penalties relaxed.",
            severity="info", source_citation=citation,
        )
    if column == "n_fixation_active" and value is True:
        return CropNoteData(
            kind="n_fixation_active",
            headline=f"{crop} fixes its own nitrogen once nodulated.",
            detail="Engine should not auto-apply N beyond a small starter dose; applied N can suppress fixation.",
            severity="info", source_citation=citation,
        )
    if column == "mo_responsive" and value is True:
        return CropNoteData(
            kind="mo_responsive",
            headline=f"{crop} is Mo-responsive.",
            detail="Sodium molybdate seed treatment recommended on acid soils (pH KCl < 5.5).",
            severity="info", source_citation=citation,
        )
    if column == "inoculant_required" and value is True:
        return CropNoteData(
            kind="inoculant_required",
            headline=f"{crop} requires Rhizobium inoculation.",
            detail="Inoculate seed with the species-specific strain before planting on first rotation; otherwise nodulation fails and N-fixation is dormant.",
            severity="warn", source_citation=citation,
        )
    if column == "boron_sensitive" and value is True:
        return CropNoteData(
            kind="boron_sensitive",
            headline=f"{crop} is boron-toxic at moderate levels.",
            detail="Do not auto-apply soil B. Foliar B only if leaf-tissue test confirms deficiency.",
            severity="warn", source_citation=citation,
        )
    if column == "boron_critical_for_set" and value is True:
        return CropNoteData(
            kind="boron_critical_for_set",
            headline=f"{crop} requires B at flowering for fruit/pod set.",
            detail="Soil + foliar B essential during flowering. Below leaf-B threshold, set fails regardless of N supply.",
            severity="watch", source_citation=citation,
        )
    if column == "nitrate_form_required" and value is True:
        return CropNoteData(
            kind="nitrate_form_required",
            headline=f"{crop} requires N as nitrate, not ammonium / urea.",
            detail="Top-dress N applications must be in nitrate form. Ammoniacal N persisting into late season degrades quality.",
            severity="warn", source_citation=citation,
        )
    if column == "photoperiod_sensitive" and value is True:
        return CropNoteData(
            kind="photoperiod_sensitive",
            headline=f"{crop} is photoperiod-sensitive — match cultivar to latitude.",
            detail="Cultivar choice (short / intermediate / long-day) must match planting date and latitude.",
            severity="info", source_citation=citation,
        )
    if column == "alternate_bearing_risk" and value is True:
        return CropNoteData(
            kind="alternate_bearing_risk",
            headline=f"{crop} shows alternate-bearing tendency.",
            detail="High-yield 'on' years are followed by low-yield 'off' years. Crop-load thinning + balanced nutrition smooth the cycle.",
            severity="info", source_citation=citation,
        )
    if column == "ca_quality_critical" and value is True:
        return CropNoteData(
            kind="ca_quality_critical",
            headline=f"{crop} is Ca-quality-critical.",
            detail="Foliar Ca during fruit cell expansion + stable irrigation prevent Ca-partition disorders (BER, bitter pit, tipburn). Soil-Ca alone is insufficient.",
            severity="warn", source_citation=citation,
        )
    if column == "k_luxury_consumer" and value is True:
        return CropNoteData(
            kind="k_luxury_consumer",
            headline=f"{crop} is a K-luxury consumer.",
            detail="Removes higher-than-typical K per ton. Replenish after every harvest cycle.",
            severity="info", source_citation=citation,
        )
    # Numeric ceilings
    if column == "n_protein_cap_kg_ha" and isinstance(value, (int, float)) and value > 0:
        return CropNoteData(
            kind="n_protein_cap",
            headline=f"{crop} has a hard N ceiling for grain quality.",
            detail=f"Total pre-anthesis N must stay below {value:g} kg/ha. Above this, grain protein exceeds spec → load downgraded.",
            severity="warn", source_citation=citation,
        )
    if column == "n_rate_ceiling_kg_per_ha" and isinstance(value, (int, float)) and value > 0:
        return CropNoteData(
            kind="n_rate_ceiling",
            headline=f"{crop} N rate capped at {value:g} kg/ha for quality.",
            detail=f"Total-season N above {value:g} kg/ha damages crop quality (colour, sugar, brix). Engine enforces this ceiling.",
            severity="warn", source_citation=citation,
        )
    if column == "cec_floor_cmol" and isinstance(value, (int, float)) and value > 0:
        return CropNoteData(
            kind="cec_floor",
            headline="Skip cation-ratio path on low-CEC soils.",
            detail=f"Below CEC {value:g} cmol/kg, the cation-ratio path is statistically unstable; engine falls through to absolute soil-test sufficiency.",
            severity="info", source_citation=citation,
        )
    return None


# Columns that drive a fallback note when the KB doesn't cover the kind
_DB_FLAG_COLUMNS = [
    "no_chloride_fertilisers", "chloride_sensitive", "sulfur_critical",
    "acid_intolerant", "acid_obligate", "salt_tolerant",
    "n_fixation_active", "mo_responsive", "inoculant_required",
    "boron_sensitive", "boron_critical_for_set",
    "nitrate_form_required", "photoperiod_sensitive",
    "alternate_bearing_risk", "ca_quality_critical", "k_luxury_consumer",
    "n_protein_cap_kg_ha", "n_rate_ceiling_kg_per_ha", "cec_floor_cmol",
]


def generate_crop_notes(
    crop: str,
    crop_calc_flags_row: Optional[dict] = None,
) -> list[CropNoteData]:
    """Produce per-block crop notes for the given crop name.

    Strategy:
      1. Start with the hardcoded KB entries for the crop (rich content,
         citations, agronomic detail). Cultivar variants fall back to
         the parent genus's KB notes.
      2. Layer DB-driven notes on top — for any flag set in the live
         `crop_calc_flags` row that the KB hasn't already covered for
         this crop, generate a templated fallback note. This makes the
         DB the source of truth: an agronomist who sets a flag in the
         DB sees it surface in the report even if no KB entry exists.

    The notes feed two surfaces:
      * Renderer: 'Crop notes — agronomic context' section in the
        nutrient-requirements report and soil report.
      * Product selector (future): hard filters via `note.kind`
        (e.g. `kind='no_chloride_fertilisers'` → drop KCl/MOP).
    """
    out: list[CropNoteData] = list(CROP_NOTE_KB.get(crop, []))

    # Cultivar fallback to genus for the KB layer
    if not out and "(" in crop:
        base_crop = crop.split("(")[0].strip()
        out = list(CROP_NOTE_KB.get(base_crop, []))

    if not crop_calc_flags_row:
        return out

    # Ratio-path override flag — surface as a note when active and not
    # already covered by the KB (Kiwi has skip_cation_ratio_path=True
    # AND a KB entry; Blueberry has the flag without a KB entry — the
    # second case wants the templated note added).
    existing_kinds = {n.kind for n in out}
    if (
        crop_calc_flags_row.get("skip_cation_ratio_path")
        and "skip_cation_ratio_path" not in existing_kinds
    ):
        out.append(
            CropNoteData(
                kind="skip_cation_ratio_path",
                headline=f"{crop} bypasses the cation-ratio path.",
                detail=(
                    "Universal FERTASA cation-ratio targets (60-70% Ca base "
                    "saturation) don't fit this crop's biology. Engine uses "
                    "absolute soil-test sufficiency only."
                ),
                severity="info",
                source_citation=str(crop_calc_flags_row.get("source", "") or "") or None,
            )
        )
        existing_kinds.add("skip_cation_ratio_path")

    # Layer the DB-driven flags on top of the KB
    for col in _DB_FLAG_COLUMNS:
        val = crop_calc_flags_row.get(col)
        if not val:
            continue
        # Skip if KB already covered this kind for the crop
        # (boolean cols use the column name as the kind; numeric cols
        # have specific kind names — do an explicit check)
        kind_name = col
        if col == "n_protein_cap_kg_ha":
            kind_name = "n_protein_cap"
        elif col == "n_rate_ceiling_kg_per_ha":
            kind_name = "n_rate_ceiling"
        elif col == "cec_floor_cmol":
            kind_name = "cec_floor"
        if kind_name in existing_kinds:
            continue
        note = _note_from_flag(crop, col, val, crop_calc_flags_row)
        if note:
            out.append(note)
            existing_kinds.add(note.kind)

    return out
