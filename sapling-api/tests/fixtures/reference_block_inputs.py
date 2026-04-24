"""Reference block inputs built from published SA sources.

Two reference blocks — macadamia (Levubu) and Valencia citrus (Sundays
River Valley) — each constructed from public FERTASA / SAMAC / Citrus
Academy data. Used by `test_reference_fixtures.py` to run the engine
end-to-end and cross-check the output against published expected values.

Every numeric input traces to a cited source:
  * FERTASA Handbook 5.8.1 (Macadamias)
  * SAMAC Schoeman "Macadamia Nutrition" (2021)
  * FERTASA Handbook 5.7.3 (Citrus)
  * Citrus Academy NQ2 Learner Guide — Orchard 10 Delta Valencia example
  * CRI "Toolkit 3.5 Plant Nutrition"
"""
from __future__ import annotations

from datetime import date

from app.models import MethodAvailability
from app.services.programme_builder_orchestrator import BlockInput, OrchestratorInput


# ============================================================
# Materials catalog — shared between mac + citrus fixtures
# ============================================================
# Standard SA-available products. Compositions from common SA fertilizer
# catalogues; organic carrier from memory's Sapling house-rule section.

REFERENCE_MATERIALS = [
    # N carriers
    {"material": "LAN", "n": 28, "p": 0, "k": 0, "ca": 8, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": False,
     "applicability": "in_season_only"},
    {"material": "Calcium Nitrate", "n": 15.5, "p": 0, "k": 0, "ca": 19, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True,
     "applicability": "in_season_only"},
    {"material": "Urea", "n": 46, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": False,
     "applicability": "in_season_only"},
    # K carriers
    {"material": "KCl", "n": 0, "p": 0, "k": 60, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True,
     "applicability": "in_season_only"},
    {"material": "SOP", "n": 0, "p": 0, "k": 50, "ca": 0, "mg": 0, "s": 18,
     "form": "solid", "liquid_compatible": True,
     "applicability": "in_season_only"},
    {"material": "Potassium Nitrate", "n": 13, "p": 0, "k": 46, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True,
     "applicability": "in_season_only"},
    # P carriers
    {"material": "MAP", "n": 11, "p": 51, "k": 0, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True,
     "applicability": "both"},
    {"material": "MKP", "n": 0, "p": 52, "k": 34, "ca": 0, "mg": 0, "s": 0,
     "form": "solid", "liquid_compatible": True,
     "applicability": "in_season_only"},
    {"material": "SSP", "n": 0, "p": 10, "k": 0, "ca": 18, "mg": 0, "s": 11,
     "form": "solid", "liquid_compatible": False,
     "applicability": "both"},
    # Mg / S
    {"material": "Magnesium Nitrate", "n": 11, "p": 0, "k": 0, "ca": 0, "mg": 15, "s": 0,
     "form": "solid", "liquid_compatible": True,
     "applicability": "in_season_only"},
    {"material": "Magnesium Sulphate", "n": 0, "p": 0, "k": 0, "ca": 0, "mg": 10, "s": 13,
     "form": "solid", "liquid_compatible": True,
     "applicability": "in_season_only"},
    # Micros — mostly foliar
    {"material": "Solubor", "n": 0, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 0, "b": 20,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": True,
     "applicability": "in_season_only"},
    {"material": "Zinc Oxide", "n": 0, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 0, "zn": 70,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": True,
     "applicability": "in_season_only"},
    {"material": "Manganese Sulphate", "n": 0, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 19, "mn": 31,
     "form": "solid", "liquid_compatible": True, "foliar_compatible": True,
     "applicability": "in_season_only"},
    # Organic carrier (satisfies Sapling ≥50% dry-blend rule)
    {"material": "Manure Compost", "n": 2.1, "p": 1.0, "k": 1.6,
     "ca": 2.2, "mg": 1.0, "s": 0.7,
     "type": "Organic", "form": "solid", "c": 35,
     "applicability": "both",
     "reaction_time_months_min": 2, "reaction_time_months_max": 12,
     "soil_improvement_purpose": "OM + slow N"},
    # Pre-season amendments
    {"material": "Calcitic Lime", "n": 0, "p": 0, "k": 0, "ca": 38, "mg": 0, "s": 0,
     "form": "solid",
     "applicability": "pre_season_only",
     "reaction_time_months_min": 4, "reaction_time_months_max": 12,
     "soil_improvement_purpose": "pH lift + Ca"},
    {"material": "Dolomitic Lime", "n": 0, "p": 0, "k": 0, "ca": 22, "mg": 11, "s": 0,
     "form": "solid",
     "applicability": "pre_season_only",
     "reaction_time_months_min": 4, "reaction_time_months_max": 12,
     "soil_improvement_purpose": "pH lift + Ca + Mg"},
    {"material": "Gypsum", "n": 0, "p": 0, "k": 0, "ca": 23, "mg": 0, "s": 18,
     "form": "solid",
     "applicability": "pre_season_only",
     "reaction_time_months_min": 3, "reaction_time_months_max": 12,
     "soil_improvement_purpose": "Ca + S (no pH shift)"},
]


# ============================================================
# Macadamia reference block — Levubu
# ============================================================
# A4 cultivar, 9 y.o., 312 trees/ha (4m × 8m), 5 ha.
# Tzaneen red-clay-loam baseline. Target 3.5 t/ha shell-on (Schoeman mid
# range, bearing orchard).
#
# Sources:
#   * FERTASA 5.8.1 — soil norms (Table 5.8.1.2), N timing (Mar-Oct only),
#     per-tree rates (25-50 g N/tree per year of age, capped at 500 g/tree
#     from year 10; K at 1.25-1.5× N from year 5; P at 1/5 of N).
#   * SAMAC Schoeman 2021 — Levubu regional application norms:
#       N 126-166 kg/ha · K 200-250 kg K/ha (= 241-301 kg K2O/ha)
#       · P 26-32 kg/ha (= 60-73 kg P2O5/ha) · S 0.18-0.25% leaf norm
#       → ~18-25 kg S/ha recycled back via removal math.
#
# Expected engine output to verify (cross-check asserts):
#   N seasonal  ≈ 140-160 kg/ha    (Schoeman mid)
#   P2O5        ≈  55-75 kg/ha
#   K2O         ≈ 230-300 kg/ha
#   Timing wall: no N delivered Nov, Dec, Jan, Feb (FERTASA 5.8.1 prose)
#   Foliar trigger: Zn fires (soil Zn 3 mg/kg << leaf-norm-implied
#       critical ~5 mg/kg; FERTASA 5.8.1 warns Zn deficiency common)
#   Foliar trigger: B fires (soil B 0.35 ppm typical deficiency)
#   Organic carrier anchor on any dry blend (house rule)

def reference_mac_levubu_block() -> BlockInput:
    """9 y.o. A4 Macadamia, Levubu, 5 ha Tzaneen red-clay-loam baseline."""
    return BlockInput(
        block_id="mac-levubu-ref",
        block_name="Reference Block A4 (Levubu)",
        block_area_ha=5.0,
        lab_name="Reference block (published norms)",
        lab_method="Mehlich-3",
        sample_date=date(2026, 3, 1),
        sample_id="REF-MAC-LEVUBU-001",
        soil_parameters={
            # Published SA Levubu red-clay-loam baseline for mac orchards.
            # pH below FERTASA ideal 6.0 → pre-season lime recommended.
            # Ca:Mg = 3.2:1 (acceptable), Zn + B below critical → foliar
            # triggers fire. P (Bray-1) 22 below 30 ideal → light
            # replenishment. OC 2.5% above warning 1.5% → OK.
            # Na_base_sat_pct provided directly (avoids ESP % unit
            # mismatch from raw Na mg/kg → cmol conversion).
            "pH (H2O)": 5.8,
            "Organic C (%)": 2.5,
            "P (Bray-1)": 22.0,
            "K": 145.0,
            "Ca": 980.0,
            "Mg": 185.0,
            "Na_base_sat_pct": 1.0,
            "S": 12.0,
            "Zn": 3.0,
            "B": 0.35,
            "Mn": 180.0,
            "Fe": 95.0,
            "Cu": 6.5,
            "Al": 0.0,
            "CEC": 10.2,
            "Acid_sat_pct": 0.0,
        },
        # Targets derived from Schoeman Levubu mid-range for 9 y.o. A4
        # at 3.5 t/ha shell-on. See header comment for traceability.
        season_targets={
            "N": 145,
            "P2O5": 60,
            "K2O": 260,
            "Ca": 0,     # soil Ca sufficient; pre-season lime handles pH
            "Mg": 0,     # soil Mg sufficient
            "S": 22,
        },
        pop_per_ha=312.0,  # 4m × 8m spacing, standard Levubu A4
    )


def reference_mac_levubu_input() -> OrchestratorInput:
    # For a BEARING perennial, `planting_date` is treated as the
    # current-season start (not the original orchard-establishment year)
    # so the stage-splitter + month-allocator produce a 12-month programme
    # aligned with the current season. Actual tree age (9 y.o.) is
    # captured in the narrative metadata, not the engine timeline.
    return OrchestratorInput(
        client_name="Reference Block — Macadamia",
        farm_name="Levubu Reference",
        prepared_for="Demo / validation",
        crop="Macadamia",
        planting_date=date(2026, 3, 1),    # current-season start for bearing orchard
        build_date=date(2026, 4, 25),
        location="Levubu, Limpopo",
        ref_number="REF-MAC-2026",
        season="2026/27",
        expected_harvest_date=date(2027, 2, 28),
        method_availability=MethodAvailability(
            has_drip=True,
            has_sprinkler=True,
            has_foliar_sprayer=True,
            has_granular_spreader=True,
            has_fertigation_injectors=True,
        ),
        blocks=[reference_mac_levubu_block()],
        available_materials=REFERENCE_MATERIALS,
        stage_count=5,
        # Typical mac grower schedule: monthly applications Mar-Oct
        # (FERTASA 5.8.1 prohibits N Nov-Feb — timing wall fires).
        application_months=[3, 4, 5, 6, 7, 8, 9, 10],
        has_recent_leaf_analysis=False,
        has_irrigation_water_test=False,
    )


# ============================================================
# Citrus reference block — Sundays River Valley Valencia
# ============================================================
# Delta / Midknight Valencia on C35 citrange, 12 y.o., 316 trees/ha
# (6.5m × 4.9m Patensie/SRV norm), 10 ha. Duplex sandy loam.
# Target 55 t/ha (SA mature Valencia mid-high range).
#
# Sources:
#   * FERTASA 5.7.3 — N July–Nov, K Aug/Sep/Oct, lime after last N, B spring;
#     NEVER apply N + K together (≥ 2 irrigations between; engine's
#     Citrus N–K antagonism wall enforces).
#   * Citrus Academy NQ2 — Orchard 10 Delta Valencia 3 ha / 316 trees/ha:
#     500+250+250 g LAN/tree (Jul/Aug/Sep) = ~88 kg N/ha seasonal;
#     500 g KCl/tree Sep = ~95 kg K2O/ha; Dolomitic Lime 4000 g/tree Oct;
#     foliar Urea + Mn + Solubor spring.
#   * Industry rule-of-thumb: mature bearing Valencia ~1.2-2.0 kg N/ton
#     fruit. At 55 t/ha target → 66-110 kg N/ha. We scale the Academy
#     baseline up ~35% to 120 kg N/ha for the higher target.
#
# Expected engine output to verify:
#   N seasonal     ≈ 110-130 kg/ha   (scaled Academy baseline)
#   P2O5           ≈  20- 35 kg/ha   (soil P moderate)
#   K2O            ≈ 160-210 kg/ha
#   N+K antagonism: no single blend carries both N-rich + K-rich product
#       in fertigation (engine's Citrus FERTASA_5_7_3 wall).
#   N timing: applications only Jul-Nov per FERTASA 5.7.3
#       (allowed_months=[7,8,9,10,11]); no Dec-Feb.
#   Foliar trigger: pre-bloom B + Zn fires (FERTASA 5.7.3 + citrus
#       stage_peak_demand rule already seeded in engine).

def reference_citrus_svr_block() -> BlockInput:
    """12 y.o. Valencia on C35, Sundays River Valley, 10 ha duplex sandy loam."""
    return BlockInput(
        block_id="citrus-svr-ref",
        block_name="Reference Block Valencia (SRV)",
        block_area_ha=10.0,
        lab_name="Reference block (published norms)",
        lab_method="Mehlich-3",
        sample_date=date(2026, 3, 1),
        sample_id="REF-CITRUS-SVR-001",
        soil_parameters={
            # SRV duplex sandy loam, Valencia-typical. pH 6.0 FERTASA
            # target; Ca:Mg = 4.1:1 (slightly Mg-lean, Dolomitic lime
            # keeps Mg topped up); K 95 slightly below FERTASA ideal 260
            # but citrus is K-sensitive to high rates (salinity). Zn + B
            # below critical → spring foliar fires per FERTASA 5.7.3.
            "pH (H2O)": 6.0,
            "Organic C (%)": 1.5,
            "P (Bray-1)": 25.0,
            "K": 95.0,
            "Ca": 780.0,
            "Mg": 115.0,
            "Na_base_sat_pct": 2.5,  # SRV duplex sandy loam typical
            "S": 10.0,
            "Zn": 1.8,
            "B": 0.30,
            "Mn": 65.0,
            "Fe": 110.0,
            "Cu": 4.2,
            "Al": 0.0,
            "CEC": 8.5,
            "Acid_sat_pct": 0.0,
        },
        season_targets={
            "N": 120,
            "P2O5": 28,
            "K2O": 185,
            "Ca": 0,     # soil Ca sufficient; dolomitic lime pre-season if needed
            "Mg": 0,     # soil Mg sufficient
            "S": 15,
        },
        pop_per_ha=316.0,  # 6.5m × 4.9m SRV norm (Citrus Academy Orchard 10)
    )


def reference_citrus_svr_input() -> OrchestratorInput:
    return OrchestratorInput(
        client_name="Reference Block — Citrus Valencia",
        farm_name="Sundays River Valley Reference",
        prepared_for="Demo / validation",
        crop="Citrus (Valencia)",
        planting_date=date(2026, 7, 1),    # current-season start for bearing orchard
        build_date=date(2026, 4, 25),
        location="Sundays River Valley, Eastern Cape",
        ref_number="REF-CITRUS-2026",
        season="2026/27",
        expected_harvest_date=date(2027, 5, 31),
        method_availability=MethodAvailability(
            has_drip=True,
            has_sprinkler=True,
            has_foliar_sprayer=True,
            has_granular_spreader=True,
            has_fertigation_injectors=True,
        ),
        blocks=[reference_citrus_svr_block()],
        available_materials=REFERENCE_MATERIALS,
        stage_count=5,
        # FERTASA 5.7.3: N July-Nov; K Aug-Oct. Farmer's operational
        # window typically covers Jul-Nov. Any month outside this range
        # triggers OutstandingItems if stages need to fall there.
        application_months=[7, 8, 9, 10, 11],
        has_recent_leaf_analysis=False,
        has_irrigation_water_test=False,
    )
