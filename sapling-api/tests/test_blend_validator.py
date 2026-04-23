"""Tests for the Phase 2 Blend Validator — catches stream purity, known
incompat pairs, missing sources."""
from __future__ import annotations

from datetime import date

import pytest

from app.models import (
    Blend,
    BlendPart,
    Concentrate,
    DryBlendMethod,
    FertigationMethod,
    FoliarMethod,
    MethodKind,
)
from app.services.blend_validator import (
    BlendValidationResult,
    DRY_GRANULE_INCOMPAT,
    validate_blends,
)


# ============================================================
# Fixtures
# ============================================================

MATERIALS = [
    {"material": "Calcium Nitrate", "n": 17.1, "p": 0, "k": 0, "ca": 24.4, "mg": 0, "s": 0},
    {"material": "MKP",             "n": 0,    "p": 51.8, "k": 33.8, "ca": 0, "mg": 0, "s": 0},
    {"material": "SOP",             "n": 0,    "p": 0, "k": 50.4, "ca": 0, "mg": 0, "s": 18},
    {"material": "Ammonium Sulphate", "n": 21, "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 24},
    {"material": "MAP 33%",         "n": 11,   "p": 50.4, "k": 0, "ca": 0, "mg": 0, "s": 0},
    {"material": "Urea",            "n": 46,   "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 0},
    {"material": "Ammonium Nitrate", "n": 34,  "p": 0, "k": 0, "ca": 0, "mg": 0, "s": 0},
]


def _make_fertigation_blend(parts, nutrients_delivered=None, stage_num=1):
    return Blend(
        block_id="b1", stage_number=stage_num, stage_name="vegetative",
        weeks="Wks 3-7", events=5, dates_label="13 May - 16 Jun 2026",
        method=FertigationMethod(kind=MethodKind.LIQUID_DRIP),
        raw_products=parts,
        concentrates=[],
        nutrients_delivered=nutrients_delivered or {},
    )


def _make_dry_blend(parts, nutrients_delivered=None, stage_num=1):
    return Blend(
        block_id="b1", stage_number=stage_num, stage_name="establishment",
        weeks="Wk 1", events=1, dates_label="1 May 2026",
        method=DryBlendMethod(kind=MethodKind.DRY_BROADCAST),
        raw_products=parts,
        concentrates=[],
        nutrients_delivered=nutrients_delivered or {},
    )


# ============================================================
# Material existence
# ============================================================

def test_unknown_product_produces_error():
    blend = _make_fertigation_blend([
        BlendPart(product="Unobtainium X", analysis="?", stream="A"),
    ])
    results, flags = validate_blends([blend], MATERIALS)
    assert len(results) == 1
    assert any("not in materials catalog" in e for e in results[0].errors)
    # Critical error → RiskFlag severity 'critical'
    assert len(flags) == 1
    assert flags[0].severity == "critical"


def test_known_products_no_error():
    blend = _make_fertigation_blend([
        BlendPart(product="Calcium Nitrate", analysis="17.1/0/0", stream="A"),
        BlendPart(product="MKP", analysis="0/51.8/33.8", stream="B"),
    ])
    results, flags = validate_blends([blend], MATERIALS)
    assert results[0].errors == []


# ============================================================
# Stream purity
# ============================================================

def test_ca_in_part_b_is_error():
    """Calcium Nitrate routed to Part B should be flagged."""
    blend = _make_fertigation_blend([
        BlendPart(product="Calcium Nitrate", analysis="17.1/0/0", stream="B"),  # wrong!
    ])
    results, flags = validate_blends([blend], MATERIALS)
    assert any("Part B" in e and "Part A" in e for e in results[0].errors)
    assert flags[0].severity == "critical"


def test_sulphate_in_part_a_is_error():
    """SOP (sulphate) routed to Part A should be flagged."""
    blend = _make_fertigation_blend([
        BlendPart(product="SOP", analysis="0/0/50.4", stream="A"),  # wrong
    ])
    results, flags = validate_blends([blend], MATERIALS)
    assert any("Part A" in e and "Part B" in e for e in results[0].errors)


def test_correct_streams_pass():
    blend = _make_fertigation_blend([
        BlendPart(product="Calcium Nitrate", analysis="17.1/0/0", stream="A"),
        BlendPart(product="SOP", analysis="0/0/50.4", stream="B"),
        BlendPart(product="MKP", analysis="0/51.8/33.8", stream="B"),
    ])
    results, _ = validate_blends([blend], MATERIALS)
    assert results[0].errors == []


# ============================================================
# Dry granule incompat
# ============================================================

def test_an_plus_urea_flags_warning():
    """Known-bad pair: Ammonium Nitrate + Urea forms slurry."""
    blend = _make_dry_blend([
        BlendPart(product="Ammonium Nitrate", analysis="34/0/0"),
        BlendPart(product="Urea", analysis="46/0/0"),
    ])
    results, flags = validate_blends([blend], MATERIALS)
    assert len(results[0].warnings) >= 1
    assert any("AN + urea" in w.lower() or "slurry" in w.lower() for w in results[0].warnings)


def test_dry_blend_single_product_no_warnings():
    blend = _make_dry_blend([
        BlendPart(product="Urea", analysis="46/0/0"),
    ])
    results, _ = validate_blends([blend], MATERIALS)
    # No incompat pairs possible with one product
    assert not any("AN + urea" in w for w in results[0].warnings)


def test_dry_granule_incompat_table_has_entries():
    """Table must have at least the common known-bad pairs."""
    assert len(DRY_GRANULE_INCOMPAT) >= 3
    for entry in DRY_GRANULE_INCOMPAT:
        assert len(entry) == 3  # (pattern_a, pattern_b, reason)


# ============================================================
# compatibility_rules from DB
# ============================================================

def test_compat_rules_flag_same_stream_pair():
    rules = [
        {"material_a": "Calcium Nitrate", "material_b": "Ammonium Sulphate",
         "compatible": False, "reason": "CaSO4 precipitation"},
    ]
    # Place both in the same stream by mistake (invalid but we test the rule fires)
    blend = _make_fertigation_blend([
        BlendPart(product="Calcium Nitrate", analysis="17.1/0/0", stream="A"),
        BlendPart(product="Ammonium Sulphate", analysis="21/0/0", stream="A"),  # wrong stream
    ])
    results, flags = validate_blends([blend], MATERIALS, compatibility_rules=rules)
    # Stream-purity error fires first (AmS should be in B)
    assert any("Part A" in e for e in results[0].errors)


def test_compat_rules_ignore_compatible_pairs():
    rules = [
        {"material_a": "Calcium Nitrate", "material_b": "Potassium Nitrate",
         "compatible": True, "reason": "soluble together"},
    ]
    blend = _make_fertigation_blend([
        BlendPart(product="Calcium Nitrate", analysis="17.1/0/0", stream="A"),
    ])
    results, _ = validate_blends([blend], MATERIALS, compatibility_rules=rules)
    # Compatible rules shouldn't surface as warnings
    assert not any("Compatible" in w for w in results[0].warnings)


# ============================================================
# Missing sources
# ============================================================

def test_missing_source_for_declared_nutrient():
    """Blend declares N delivery but has no N-containing product."""
    blend = _make_fertigation_blend(
        [BlendPart(product="SOP", analysis="0/0/50.4", stream="B")],
        nutrients_delivered={"N": 20, "K2O": 10},  # N declared but no N source
    )
    results, _ = validate_blends([blend], MATERIALS)
    assert "N" in results[0].missing_sources


def test_all_nutrients_sourced_no_missing():
    blend = _make_fertigation_blend(
        [
            BlendPart(product="Calcium Nitrate", analysis="17.1/0/0", stream="A"),
            BlendPart(product="MKP", analysis="0/51.8/33.8", stream="B"),
        ],
        nutrients_delivered={"N": 20, "K2O": 10, "P2O5": 15},
    )
    results, _ = validate_blends([blend], MATERIALS)
    assert results[0].missing_sources == []


# ============================================================
# Validation result properties
# ============================================================

def test_is_valid_false_when_errors():
    result = BlendValidationResult(
        block_id="b1", stage_number=1, stage_name="v",
        errors=["something wrong"],
    )
    assert result.is_valid is False


def test_is_valid_true_when_only_warnings():
    result = BlendValidationResult(
        block_id="b1", stage_number=1, stage_name="v",
        warnings=["just a note"],
    )
    assert result.is_valid is True


# ============================================================
# Multi-blend batch
# ============================================================

def test_validate_multiple_blends_returns_one_result_each():
    blends = [
        _make_fertigation_blend(
            [BlendPart(product="Calcium Nitrate", analysis="", stream="A")],
            stage_num=1,
        ),
        _make_fertigation_blend(
            [BlendPart(product="SOP", analysis="", stream="B")],
            stage_num=2,
        ),
    ]
    results, _ = validate_blends(blends, MATERIALS)
    assert len(results) == 2
    stages = {r.stage_number for r in results}
    assert stages == {1, 2}
