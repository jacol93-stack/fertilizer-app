"""Unit tests for the deterministic layers of the narrative pipeline.

Layer 1 — Opus generation — needs the API and isn't covered here.
Layer 2 — fact validator — fully covered.
Layer 3a/b — policeman denylist + rate caps — fully covered.
Layer 3c — Opus critique — needs the API; we verify the wrapper falls
back gracefully when use_opus_critique=False.
"""
from __future__ import annotations

from app.services.narrative.fact_validator import (
    extract_artifact_numbers,
    find_unverified_numbers,
    validate_prose,
)
from app.services.narrative.policeman import (
    Issue,
    PolicemanReport,
    _check_denylist,
    _check_rate_caps,
    _verdict_from_issues,
    audit,
)


# ============================================================
# Fact validator
# ============================================================

def test_validator_traces_artifact_numbers():
    artifact = {
        "soil": {"pH": 4.8, "block_area_ha": 4.5},
        "amendments": [{"rate_t_per_ha": 2.5}],
    }
    nums = extract_artifact_numbers(artifact)
    assert 4.8 in nums
    assert 4.5 in nums
    assert 2.5 in nums


def test_validator_accepts_rounding_within_tolerance():
    artifact = {"rate": 154.7}
    unverified = find_unverified_numbers(
        section="x",
        prose="We will apply 155 kg/ha as the seasonal rate.",
        artifact_numbers=extract_artifact_numbers(artifact),
    )
    assert unverified == []


def test_validator_flags_fabricated_number():
    artifact = {"rate": 100}
    unverified = find_unverified_numbers(
        section="x",
        prose="We will apply 999 kg/ha as the seasonal rate.",
        artifact_numbers=extract_artifact_numbers(artifact),
    )
    assert len(unverified) == 1
    assert unverified[0].value == 999.0


def test_validator_ignores_small_ambient_integers():
    artifact = {"rate": 100}
    unverified = find_unverified_numbers(
        section="x",
        prose="Two of the three blocks need a second pass.",
        artifact_numbers=extract_artifact_numbers(artifact),
    )
    assert unverified == []


def test_validator_handles_percentages():
    artifact = {"al_saturation": 0.22}
    unverified = find_unverified_numbers(
        section="x",
        prose="Aluminium saturation reads 22%, an acid-stress signal.",
        artifact_numbers=extract_artifact_numbers(artifact),
    )
    assert unverified == []


# ============================================================
# Policeman — denylist
# ============================================================

def test_denylist_catches_raw_material_name():
    issues = _check_denylist({"x": "Apply 100 kg/ha of MAP."})
    assert any(i.category == "disclosure" for i in issues)


def test_denylist_catches_source_citation():
    issues = _check_denylist({"x": "Per FERTASA the soil is acid."})
    assert any(i.category == "disclosure" for i in issues)


def test_denylist_catches_handbook_section_number():
    issues = _check_denylist({"x": "See section 5.7.3 for context."})
    assert any("section number" in i.what for i in issues)


def test_denylist_does_not_match_substring_inside_word():
    # 'map' inside 'mapping' should not fire the MAP denylist entry.
    issues = _check_denylist({"x": "We are mapping the orchard zones."})
    assert not any(i.what.startswith("Disclosure") and "MAP" in i.what for i in issues)


def test_denylist_clean_prose_passes():
    issues = _check_denylist(
        {"x": "Trees are at flowering, so this pass leads with calcium and boron."}
    )
    assert issues == []


# ============================================================
# Policeman — rate caps
# ============================================================

def test_rate_caps_flag_excess_foliar_boron():
    artifact = {
        "foliar_events": [
            {"id": "f1", "stage": "bud break", "b_kg_per_ha": 2.0},
        ]
    }
    issues = _check_rate_caps(artifact)
    assert any("boron" in i.what.lower() for i in issues)


def test_rate_caps_pass_safe_foliar_boron():
    artifact = {
        "foliar_events": [
            {"id": "f1", "stage": "bud break", "b_kg_per_ha": 0.4},
        ]
    }
    assert _check_rate_caps(artifact) == []


# ============================================================
# Verdict aggregation
# ============================================================

def test_fail_dominates_warn():
    issues = [
        Issue(severity="warn", category="voice", where="x", what="?"),
        Issue(severity="fail", category="disclosure", where="y", what="?"),
    ]
    assert _verdict_from_issues(issues) == "FAIL"


def test_warn_when_only_warnings():
    issues = [Issue(severity="warn", category="voice", where="x", what="?")]
    assert _verdict_from_issues(issues) == "WARN"


def test_pass_when_no_issues():
    assert _verdict_from_issues([]) == "PASS"


# ============================================================
# audit() integrates layers
# ============================================================

def test_audit_no_opus_returns_pass_on_clean_prose():
    artifact = {"header": {"crop": "macadamia"}, "soil_snapshots": []}
    prose = {
        "background_intro": "Trees are at flowering, so this pass leads with calcium.",
    }
    report = audit(
        artifact_json=artifact,
        rendered_prose=prose,
        client=None,
        use_opus_critique=False,
    )
    assert isinstance(report, PolicemanReport)
    assert report.verdict == "PASS"
    assert report.issues == []


def test_audit_no_opus_fails_on_disclosure_breach():
    artifact = {"header": {"crop": "macadamia"}, "soil_snapshots": []}
    prose = {"background_intro": "Apply 100 kg/ha of MAP at flowering."}
    report = audit(
        artifact_json=artifact,
        rendered_prose=prose,
        client=None,
        use_opus_critique=False,
    )
    assert report.verdict == "FAIL"
    assert any(i.category == "disclosure" for i in report.issues)
