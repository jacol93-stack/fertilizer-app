"""Tests for the soil-values canonicaliser.

Covers the four shapes data arrives in:
  1. Lab-with-unit-suffix labels (Anton's NViroTek format) — "K (mg/kg)".
  2. Lab-with-saturation columns — "K Saturation (%)".
  3. Canonical labels straight through ("K", "Ca").
  4. Manual entry with an explicit unit override (form picked unit
     from a dropdown).

Plus regressions for past bugs: ESP unit confusion, classification
miss on unit-suffixed keys, P-method discrimination.
"""
from __future__ import annotations

import pytest

from app.services.soil_canonicaliser import (
    CANONICAL_PARAMETERS,
    canonicalise_parameter_name,
    canonicalise_soil_values,
    list_canonical_parameters,
)


# ── Anton-shape labs (mg/kg + saturations) ─────────────────────────


def test_anton_full_lab_row_canonicalises_correctly():
    """The exact shape that broke the first programme build today."""
    raw = {
        "pH (KCl)": 5.29,
        "K (mg/kg)": 263.0,
        "Ca (mg/kg)": 944.0,
        "Mg (mg/kg)": 175.0,
        "Na (mg/kg)": 26.0,
        "S (mg/kg)": 26.94,
        "P (Bray-1) (mg/kg)": 61.0,
        "CEC (cmol/kg)": 6.94,
        "K Saturation (%)": 9.7,
        "Ca Saturation (%)": 67.98,
        "Mg Saturation (%)": 20.67,
        "Na Saturation (%)": 1.65,
        "Acid Saturation (%)": 0.0,
        "Bulk Density (g/ml)": 1.3,
        "Exchangeable Acid (cmol/kg)": 0.0,
        "Mg:K": 2.13,
        "Na:K": 0.17,
        "Ca:Mg": 3.29,
        "(Ca+Mg)/K": 9.13,
    }
    result = canonicalise_soil_values(raw, source="lab_pdf")

    # Every key normalised.
    assert result.values["pH (KCl)"] == 5.29
    assert result.values["K"] == 263.0
    assert result.values["Ca"] == 944.0
    assert result.values["Mg"] == 175.0
    assert result.values["Na"] == 26.0
    assert result.values["P (Bray-1)"] == 61.0
    assert result.values["CEC"] == 6.94
    assert result.values["K Saturation"] == 9.7
    assert result.values["Na Saturation"] == 1.65

    # Magnitude all in plausible ranges → no warnings.
    warnings = [d for d in result.diagnostics if d.severity == "warn"]
    assert warnings == [], f"unexpected warnings: {[w.message for w in warnings]}"


def test_anton_data_passes_engine_classifier_keys():
    """After canonicalisation the keys match `soil_sufficiency.parameter`
    (verified against the schema as of migration 070+). This is what
    fixes the silent-classification-miss bug."""
    raw = {"K (mg/kg)": 263.0, "Ca (mg/kg)": 944.0, "P (Bray-1) (mg/kg)": 61.0}
    result = canonicalise_soil_values(raw)
    # These are the exact strings the classifier looks up.
    assert "K" in result.values
    assert "Ca" in result.values
    assert "P (Bray-1)" in result.values


# ── Unit conversions ───────────────────────────────────────────────


def test_K_in_cmol_converts_to_canonical_mgkg():
    """Lab reports K in cmol_c/kg → canonicaliser converts to mg/kg
    using the equivalent weight (1 cmol_c/kg K = 391 mg/kg)."""
    raw = {"K (cmol/kg)": 0.67}  # ~263 mg/kg
    result = canonicalise_soil_values(raw)
    # 0.67 × 391 ≈ 262
    assert abs(result.values["K"] - (0.67 * 391)) < 0.5


def test_ca_in_cmol_converts_to_canonical_mgkg():
    raw = {"Ca (cmol/kg)": 4.71}  # ~944 mg/kg via Ca eq weight
    result = canonicalise_soil_values(raw)
    assert abs(result.values["Ca"] - (4.71 * 200.4)) < 1.0


def test_explicit_unit_override_wins_over_label():
    """Manual entry: user typed 'K' as the parameter and picked
    'cmol_c/kg' from the unit dropdown. The label has no unit hint;
    the explicit_units arg drives the conversion."""
    raw = {"K": 0.67}
    result = canonicalise_soil_values(
        raw, explicit_units={"K": "cmol_c/kg"},
    )
    assert abs(result.values["K"] - (0.67 * 391)) < 0.5


def test_explicit_unit_overrides_parsed_label():
    """Even when the label LOOKS like mg/kg, an explicit unit override
    takes priority — the user knows what the lab gave them."""
    raw = {"K (mg/kg)": 0.67}
    result = canonicalise_soil_values(
        raw, explicit_units={"K (mg/kg)": "cmol_c/kg"},
    )
    # Treated as cmol → converted up
    assert abs(result.values["K"] - (0.67 * 391)) < 0.5


def test_canonical_label_passthrough():
    """Already-canonical inputs stay numerically identical."""
    raw = {"K": 263.0, "Ca": 944.0, "pH (KCl)": 5.29}
    result = canonicalise_soil_values(raw)
    assert result.values["K"] == 263.0
    assert result.values["Ca"] == 944.0
    assert result.values["pH (KCl)"] == 5.29


# ── ESP regression ─────────────────────────────────────────────────


def test_esp_canonical_path_uses_lab_saturation_directly():
    """Regression: the 374 % ESP bug. Lab gives Na (mg/kg) AND Na
    Saturation (%) directly — engine should pick up Na Saturation
    after canonicalisation."""
    raw = {
        "Na (mg/kg)": 26.0,
        "Na Saturation (%)": 1.65,
        "CEC (cmol/kg)": 6.94,
    }
    result = canonicalise_soil_values(raw)
    assert result.values["Na"] == 26.0
    assert result.values["Na Saturation"] == 1.65
    assert result.values["CEC"] == 6.94


# ── Tolerances + error handling ────────────────────────────────────


def test_string_values_with_european_decimals():
    raw = {"K (mg/kg)": "263,5", "pH (KCl)": "5,29"}
    result = canonicalise_soil_values(raw)
    assert result.values["K"] == 263.5
    assert result.values["pH (KCl)"] == 5.29


def test_string_values_with_detection_limit_prefix():
    raw = {"S (mg/kg)": "< 5"}
    result = canonicalise_soil_values(raw)
    assert result.values["S"] == 5.0


def test_unparseable_value_drops_with_warning():
    raw = {"K (mg/kg)": "n/a"}
    result = canonicalise_soil_values(raw)
    assert "K" not in result.values
    assert any("Couldn't parse" in d.message for d in result.diagnostics)


def test_none_and_empty_values_dropped_silently():
    raw = {"K (mg/kg)": None, "Ca (mg/kg)": "", "Mg (mg/kg)": 175.0}
    result = canonicalise_soil_values(raw)
    assert result.values == {"Mg": 175.0}
    # No diagnostic — None is a normal "not measured" state, not an error.
    error_count = len([d for d in result.diagnostics if d.severity == "warn"])
    assert error_count == 0


def test_unknown_parameter_passes_through_with_info_diagnostic():
    raw = {"Custom Lab Column": 42.0, "K (mg/kg)": 263.0}
    result = canonicalise_soil_values(raw)
    assert result.values["K"] == 263.0
    assert result.values["Custom Lab Column"] == 42.0
    assert any(
        "Unknown parameter" in d.message and d.severity == "info"
        for d in result.diagnostics
    )


def test_magnitude_warning_fires_when_value_outside_range():
    """K=10000 mg/kg is implausibly high (max plausible = 5000).
    Likely the user typed it in cmol_c/kg but didn't pick the unit."""
    raw = {"K": 10000.0}
    result = canonicalise_soil_values(raw)
    assert "K" in result.values  # still stored
    assert any(
        d.parameter == "K" and "outside the plausible range" in d.message
        for d in result.diagnostics
    )


def test_duplicate_input_keeps_first_warns_on_second():
    """Lab gives both 'K' and 'K (mg/kg)' — keep first, flag second."""
    raw = {"K": 100.0, "K (mg/kg)": 200.0}
    result = canonicalise_soil_values(raw)
    assert result.values["K"] == 100.0
    assert any("Duplicate" in d.message for d in result.diagnostics)


# ── Saturations ────────────────────────────────────────────────────


def test_esp_aliases_map_to_na_saturation():
    """Several lab forms for ESP all map to canonical 'Na Saturation'."""
    for label in ("ESP", "Na base sat %", "Na_base_sat_pct"):
        result = canonicalise_soil_values({label: 14.7})
        assert result.values["Na Saturation"] == 14.7


def test_acid_saturation_aliases():
    for label in ("Acid Saturation (%)", "Al saturation", "Al_saturation_pct"):
        result = canonicalise_soil_values({label: 5.0})
        assert result.values["Acid Saturation"] == 5.0


# ── Phosphorus methods ─────────────────────────────────────────────


def test_p_methods_kept_distinct():
    """Bray-1 and Citric acid extractions aren't interchangeable —
    they produce different numbers and have different sufficiency
    bands. The canonicaliser must NOT collapse them."""
    raw = {"P (Bray-1) (mg/kg)": 30.0, "P (Citric acid) (mg/kg)": 50.0}
    result = canonicalise_soil_values(raw)
    assert result.values["P (Bray-1)"] == 30.0
    assert result.values["P (Citric acid)"] == 50.0


# ── Org C / Org M derivation ───────────────────────────────────────


def test_org_c_derived_from_org_m_when_only_om_provided():
    """Lab reported Organic Matter only → derive Org C via Van Bemmelen."""
    raw = {"Org M": 3.45}  # 3.45 / 1.724 ≈ 2.0
    result = canonicalise_soil_values(raw)
    assert "Org M" in result.values
    assert "Org C" in result.values
    assert abs(result.values["Org C"] - 2.0) < 0.05


def test_org_c_directly_provided_skips_derivation():
    raw = {"Org C": 1.5, "Org M": 3.45}
    result = canonicalise_soil_values(raw)
    # Direct Org C wins over the derived path.
    assert result.values["Org C"] == 1.5


# ── Raw + metadata + provenance ────────────────────────────────────


def test_raw_input_preserved_verbatim():
    raw = {"K (mg/kg)": 263.0, "Ca (mg/kg)": 944.0}
    result = canonicalise_soil_values(raw)
    assert result.raw == raw


def test_metadata_records_original_label_and_unit():
    raw = {"K (cmol/kg)": 0.67}
    result = canonicalise_soil_values(raw, source="lab_pdf")
    meta = result.metadata["K"]
    assert meta["original_label"] == "K (cmol/kg)"
    assert meta["original_unit"] == "cmol/kg"
    assert meta["original_value"] == 0.67
    assert meta["source"] == "lab_pdf"
    assert meta["canonical"] is True


# ── UI helper ──────────────────────────────────────────────────────


def test_list_canonical_parameters_includes_every_registered_key():
    listing = list_canonical_parameters()
    listed_keys = {row["canonical_key"] for row in listing}
    assert listed_keys == set(CANONICAL_PARAMETERS.keys())


def test_listing_includes_accepted_units_for_K():
    listing = list_canonical_parameters()
    k_row = next(r for r in listing if r["canonical_key"] == "K")
    # Manual-entry form populates a unit dropdown from this list.
    assert "mg/kg" in k_row["accepted_units"]
    assert "cmol_c/kg" in k_row["accepted_units"]


# ── Empty / degenerate cases ───────────────────────────────────────


def test_empty_dict_returns_empty_canonical():
    result = canonicalise_soil_values({})
    assert result.values == {}
    assert result.diagnostics == []


def test_only_unparseable_inputs_returns_empty_with_warnings():
    result = canonicalise_soil_values({"K (mg/kg)": "??"})
    assert result.values == {}
    assert len(result.diagnostics) == 1


# ── canonicalise_parameter_name (public helper) ────────────────────


def test_canonicalise_parameter_name_collapses_exchangeable_aliases():
    # Citrus override row was keyed "K (exchangeable)" while generic
    # soil_sufficiency uses "K" — silently disabled the override. Lock
    # in the alias so future merges collapse them onto the same key.
    assert canonicalise_parameter_name("K (exchangeable)") == "K"
    assert canonicalise_parameter_name("Ca (exchangeable)") == "Ca"
    assert canonicalise_parameter_name("Mg (exchangeable)") == "Mg"
    assert canonicalise_parameter_name("Na (exchangeable)") == "Na"


def test_canonicalise_parameter_name_keeps_method_qualifiers_distinct():
    # pH (KCl) and pH (H2O) ARE different parameters — different scales.
    # Don't collapse them to a generic "pH".
    assert canonicalise_parameter_name("pH (KCl)") == "pH (KCl)"
    assert canonicalise_parameter_name("pH (H2O)") == "pH (H2O)"
    # Same for P-extraction methods.
    assert canonicalise_parameter_name("P (Bray-1)") == "P (Bray-1)"
    assert canonicalise_parameter_name("P (Olsen)") == "P (Olsen)"


def test_canonicalise_parameter_name_handles_word_aliases():
    assert canonicalise_parameter_name("Potassium") == "K"
    assert canonicalise_parameter_name("Exchangeable K") == "K"
    assert canonicalise_parameter_name("Magnesium") == "Mg"


def test_canonicalise_parameter_name_passes_unknown_through():
    # Custom lab columns survive without being dropped.
    assert canonicalise_parameter_name("Custom Index") == "Custom Index"
    assert canonicalise_parameter_name("") == ""
