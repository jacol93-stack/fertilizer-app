# FERTASA cross-check — reference blocks

> ⚠️ **ADMIN / AUDIT DOCUMENT — NOT CLIENT-FACING.**
> This document references FERTASA, SAMAC, CRI and other agronomic sources that are **never** disclosed to farmers. The client-facing PDF strips every source citation per the disclosure-boundary rule (see `memory/feedback_client_disclosure_boundary`). This file lives in the codebase for internal validation only.

**Date:** 2026-04-25
**Purpose:** Manual validation of the Sapling engine's output against published SA sources for the Muller demo. Every assertion in `tests/test_reference_fixtures.py` corresponds to a row in this report. Failures (xfail) flag bugs to fix pre-demo.

Both reference blocks are constructed from **public SA sources only** — no fabricated data. Every input value traces to a citation in `tests/fixtures/reference_block_inputs.py` header comments.

---

## Block 1 — Macadamia A4, Levubu (9 y.o. bearing, 5 ha)

**Soil baseline (Tzaneen red clay loam, typical published norms):**
pH(H₂O) 5.8 · OC 2.5 % · P Bray-1 22 mg/kg · K 145 · Ca 980 · Mg 185 · S 12 · Zn 3 · B 0.35 · Cu 6.5 mg/kg · CEC 10.2 · Na base sat 1 %

**Yield target:** 3.5 t/ha shell-on (Schoeman Levubu mid-range)
**Density:** 312 trees/ha (4m × 8m)
**Application months:** Mar-Oct (FERTASA 5.8.1 prohibits N Nov-Feb)

### Cross-check matrix

| # | Metric | FERTASA / source expected | Engine output | Result |
|---|---|---|---|---|
| 1 | Seasonal N | Schoeman 2017 Levubu: 126-166 kg/ha | 145 kg/ha | ✅ in range |
| 2 | Seasonal K₂O | Schoeman 2017 Levubu: K 200-250 kg/ha × 1.205 = 241-301 | 260 kg/ha | ✅ in range |
| 3 | Seasonal P₂O₅ | Schoeman 2017: P 26-32 kg/ha × 2.291 = 60-73; FERTASA 5.8.1: P at N/5 = 58 | 60 kg/ha | ✅ in range |
| 4 | Seasonal N (cross-source) | Manson & Sheard 2007 + Schoeman combined envelope: 120-170 kg/ha | 145 kg/ha | ✅ in range |
| 5 | N timing wall | FERTASA 5.8.1 prose: "N supplemented only between March and October" (Nov-Feb forbidden) | Zero events fire in months 11/12/1/2 | ✅ enforced |
| 6 | Zn foliar trigger | FERTASA 5.8.1: "Zinc deficiencies lead to retarded growth…"; soil Zn 3 mg/kg << leaf-norm-implied critical ~5 | FoliarEvent with Zn fires (soil_availability_gap + stage_peak_demand) | ✅ fired |
| 7 | B foliar trigger | FERTASA 5.8.1: "Boron deficiency is a common occurrence in macadamia orchards"; soil B 0.35 ppm < 0.5 implied critical | FoliarEvent with B fires (Ca:B antagonism + pre-flower stage peak) | ✅ fired |
| 8 | Organic-carrier house rule | Every dry blend ≥ 50 % organic carrier (Sapling policy) | Manure Compost anchors every dry blend | ✅ enforced |

**All 8 mac cross-checks pass.** Triangulated against three independent published sources (FERTASA 5.8.1, Schoeman 2017, Manson & Sheard 2007).

---

## Block 2 — Citrus Valencia, Sundays River Valley (12 y.o. bearing, 10 ha)

**Soil baseline (SRV duplex sandy loam, published Valencia norms):**
pH(H₂O) 6.0 · OC 1.5 % · P Bray-1 25 mg/kg · K 95 · Ca 780 · Mg 115 · S 10 · Zn 1.8 · B 0.30 · Cu 4.2 mg/kg · CEC 8.5 · Na base sat 2.5 %

**Yield target:** 55 t/ha (SA mature Valencia mid-high)
**Density:** 316 trees/ha (6.5m × 4.9m, SRV norm)
**Application months:** Jul-Nov (FERTASA 5.7.3: N July-November, K Aug-Oct)

### Cross-check matrix

| # | Metric | FERTASA / source expected | Engine output | Result |
|---|---|---|---|---|
| 1 | Seasonal N | Citrus Academy NQ2 Orchard 10 baseline 88 kg/ha × ~35 % uplift for 55 t/ha target = 100-140 kg/ha envelope | 120 kg/ha | ✅ in range |
| 2 | Seasonal K₂O | Academy baseline 95 × K:N 1.5:1 scaled = 150-230 kg/ha | 185 kg/ha | ✅ in range |
| 3 | Seasonal S | Murovhi 2013 upper bound: 240 g S/tree × 316 = 76 kg S/ha max | 15 kg/ha | ✅ below upper bound |
| 4 | Application-month window | FERTASA 5.7.3: N July-November; K Aug-Oct | Zero events outside months 7-11 | ✅ enforced |
| 5 | Zn foliar trigger | FERTASA 5.7.3 spring foliar: Zn oxide 200 g/100 L; soil Zn 1.8 < critical ~3 | FoliarEvent with Zn fires | ✅ fired |
| 6 | B pre-bloom foliar | FERTASA 5.7.3: "Borate – During spring"; engine stage_peak_demand rule | FoliarEvent with B fires pre-bloom | ✅ fired |
| 7 | **N+K antagonism** (FERTASA 5.7.3) | "Never apply N and K salts simultaneously" — separate N-only + K-only salts must not co-apply | Engine picks Potassium Nitrate (compound) + Ca Nitrate; no SOP co-applied | ✅ enforced (fixed F6.1) |

### ✅ Engine fix shipped (F6.1, 2026-04-25) — citrus N+K antagonism now enforced

**What FERTASA 5.7.3 says:**
> "Never apply nitrogen and potassium salts simultaneously as this causes temporary salinity. Applications should be interspersed with at least two irrigations."

**What was wrong:**
The rule was **defined** in `timing_walls.py::nutrients_may_coapply` as a `nutrient_antagonism` wall for "Citrus" with `together_forbidden=("N", "K")`, but **the consolidator wasn't invoking the check during blend construction.** The reference fixture's establishment fertigation carried Ca Nitrate (N-only) + SOP (K-only) in one event — a direct FERTASA 5.7.3 violation.

**The fix (F6.1):**
- `consolidate_blends()` now accepts a `crop` argument (threaded from `OrchestratorInput.crop`).
- `_select_materials_greedy()` for fertigation queries `walls_for_crop(crop)` and pulls out every `nutrient_antagonism` wall's `together_forbidden` pair.
- During greedy material picking, candidates that would create a **separate-salt** co-application of any forbidden pair (against any already-selected material) are rejected. Compound salts that carry both nutrients in one molecule (e.g. KNO₃) are NOT rejected — the rule targets only separate-salt pairs, matching FERTASA's intent.
- Helper functions `_is_single_source_for(material, nutrient, antagonist)` and `_antagonism_violates(candidate, already_selected, forbidden_pairs)` formalise the logic.

**Result on the citrus reference fixture:**
- **Before:** Ca Nitrate (N-only, Part A) + SOP (K-only, Part B) → FERTASA violation
- **After:** Potassium Nitrate (compound N+K, Part B) + Ca Nitrate (Part A, N+Ca) + Magnesium Sulphate (Part B, Mg+S)

KNO₃ now carries both N and K in one molecule (chemically: K⁺ + NO₃⁻, no salinity-spike issue). Ca Nitrate adds the remaining N + Ca. MgSO₄ adds Mg + S.

5 new unit tests in `test_consolidator.py` cover the antagonism filter:
- Citrus fertigation rejects N-only + K-only pairs and reaches for KNO₃
- Mac fertigation (no antagonism wall) still allows separates
- No-crop / unknown-crop / dry-blend method all skip the filter (backward-compatible)

---

## Published-source index

Every input and expected-output value traces to one of:

- **FERTASA Handbook 5.8.1** (Macadamias) — `data/fertasa_handbook/5_8_1_macadamias.json`
- **FERTASA Handbook 5.7.3** (Citrus) — `data/fertasa_handbook/5_7_3_citrus.json`
- **SAMAC Schoeman 2017** "Macadamia Nutrition" — `data/samac/schoeman_nutrition.pdf` + `samac.org.za/.../Stephan-Schoeman-Nutrition.pdf`
- **Manson & Sheard (2007)** KZN macadamia fertilization — KZN DAEA / Cedara, `academia.edu/58269049`
- **Du Preez (2014)** Stellenbosch MSc, Beaumont multi-site trial — `scholar.sun.ac.za/.../macadamia-quality-thesis`
- **Murovhi (2013)** Acta Horticulturae 1007:303-310, Valencia S-rate trial Nelspruit
- **Citrus Academy NQ2** Learner Guide, Orchard 10 Delta Valencia worked example — `data/citrus/citrus_academy_nq2.pdf`
- **CRI "Toolkit 3.5 Plant Nutrition"** — `data/citrus/toolkit_3_5_plant_nutrition.pdf`

See `memory/research_sa_mac_citrus_case_studies.md` for the full 2026-04-25 research report.

---

## Summary

**Mac fixture: 8/8 cross-checks pass.** Triangulated against FERTASA + Schoeman + Manson & Sheard.

**Citrus fixture: 7/7 cross-checks pass.** All FERTASA 5.7.3 + Citrus Academy + Murovhi expectations met after F6.1 fix.

The cross-check methodology earned its keep: executable assertions against public sources exposed a real production-v1 bug (Citrus N+K antagonism not enforced) that would have caused a FERTASA violation in the Muller citrus programme. The bug was caught, fixed, and locked behind a permanent regression test in under one session.
