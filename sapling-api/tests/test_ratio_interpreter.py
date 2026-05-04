"""Tests for ratio_interpreter — the smart ratio-by-ratio interpretation engine.

Locks in the contract that:
  * Every defined ratio gets an interpretation row when a value is present
  * In-band values produce 'in_range' state with no bound nutrients
  * Out-of-band values surface the right effect + bound nutrients
  * Holistic summary correctly aggregates nutrients-at-risk
"""
from __future__ import annotations

from app.services.ratio_interpreter import (
    interpret_ratio,
    interpret_all_ratios,
    summarise_ratios,
    RATIO_RULES,
)


def test_ca_mg_in_range_returns_no_bound_nutrients():
    interp = interpret_ratio("Ca:Mg", 4.5)
    assert interp is not None
    assert interp.state == "in_range"
    assert interp.bound_nutrients == []
    assert interp.severity == "info"


def test_ca_mg_too_high_flags_mg_bound():
    interp = interpret_ratio("Ca:Mg", 9.0)
    assert interp.state == "high"
    assert interp.severity == "warn"
    assert "Mg" in interp.bound_nutrients
    assert "interveinal chlorosis" in interp.direct_effect
    assert interp.recommended_action is not None


def test_ca_mg_too_low_flags_k_and_ca_bound():
    interp = interpret_ratio("Ca:Mg", 1.5)
    assert interp.state == "low"
    assert "Ca" in interp.bound_nutrients
    assert "K" in interp.bound_nutrients
    assert "gypsum" in (interp.recommended_action or "").lower()


def test_acid_saturation_critical_severity_when_high():
    # >5% acid saturation is critical for non-acid-tolerant crops
    interp = interpret_ratio("Acid Saturation", 12.0)
    assert interp.severity == "critical"
    assert "P" in interp.bound_nutrients
    assert "Ca" in interp.bound_nutrients


def test_k_saturation_high_locks_ca_and_mg():
    interp = interpret_ratio("K Saturation", 8.0)
    assert interp.state == "high"
    assert "Ca" in interp.bound_nutrients
    assert "Mg" in interp.bound_nutrients


def test_p_zn_antagonism_only_high_side_matters():
    # P:Zn 50 is fine
    low = interpret_ratio("P:Zn", 50)
    assert low.state == "in_range" or low.state == "low"
    # P:Zn 200 locks Zn
    high = interpret_ratio("P:Zn", 200)
    assert high.state == "high"
    assert "Zn" in high.bound_nutrients


def test_unknown_ratio_returns_none():
    assert interpret_ratio("Made-up:Thing", 5.0) is None


def test_interpret_all_ratios_skips_missing_values():
    # Only Ca:Mg present — should produce 1 entry, not 11
    interps = interpret_all_ratios(soil_values={}, computed_ratios={"Ca:Mg": 4.0})
    assert len(interps) == 1
    assert interps[0].name == "Ca:Mg"


def test_interpret_all_ratios_reads_lab_keys_for_saturations():
    # Lab data may have 'K Saturation' directly without engine-computed ratios
    interps = interpret_all_ratios(
        soil_values={"K Saturation": 8.0, "Ca Saturation": 65.0},
        computed_ratios={},
    )
    names = {i.name for i in interps}
    assert "K base saturation" in names
    assert "Ca base saturation" in names


def test_holistic_summary_in_band_says_no_concerns():
    interps = [interpret_ratio("Ca:Mg", 4.0), interpret_ratio("Mg:K", 3.0)]
    summary = summarise_ratios(interps)
    assert summary.nutrients_at_risk == []
    assert summary.key_concerns == []
    assert "within their published bands" in summary.summary


def test_holistic_summary_aggregates_bound_nutrients_in_severity_order():
    # Ca:Mg 9.0 → Mg bound (warn). Acid Saturation 15 → P, Ca, Mg bound (critical).
    # Critical should come first; nutrients deduplicated.
    interps = [
        interpret_ratio("Ca:Mg", 9.0),
        interpret_ratio("Acid Saturation", 15.0),
    ]
    summary = summarise_ratios([i for i in interps if i is not None])
    # Acid Saturation is critical → should be first concern
    assert "Acid saturation" in summary.key_concerns[0]
    # Bound nutrients dedupe across both interpretations
    assert "Mg" in summary.nutrients_at_risk
    assert "P" in summary.nutrients_at_risk


def test_every_rule_has_required_fields():
    """Lock structural completeness — every rule has the prose fields the
    artifact needs."""
    for name, rule in RATIO_RULES.items():
        assert rule.what_it_measures, f"{name} missing what_it_measures"
        assert rule.low_effect, f"{name} missing low_effect"
        assert rule.high_effect, f"{name} missing high_effect"
        assert rule.in_range_effect, f"{name} missing in_range_effect"
        assert rule.source, f"{name} missing source"
        assert rule.ideal_low <= rule.ideal_high, f"{name} bad band order"
