"""Unit tests for the shared multi-sample aggregation primitive.

These lock in the contract that both Level 1 (samples → block) and
Level 2 (block-requirements → programme) depend on. If the shape of
AggregationResult changes, the two call sites in
`routers/soil.py` / `routers/programmes.py` / `services/programme_engine.py`
must be updated together.
"""

from __future__ import annotations

import math

import pytest

from app.services.aggregation import aggregate_samples


def test_single_sample_passthrough():
    res = aggregate_samples([{"P": 20.0, "K": 150.0}])
    assert res.values == {"P": 20.0, "K": 150.0}
    assert res.composition_method == "single"
    assert res.replicate_count == 1
    assert res.weight_strategy == "equal"
    # No CV or outliers meaningful at n=1
    assert res.stats["P"].cv_pct is None
    assert res.stats["P"].outlier_sample_indices == []


def test_equal_weights_arithmetic_mean():
    res = aggregate_samples([{"P": 10}, {"P": 20}, {"P": 30}])
    assert res.values["P"] == pytest.approx(20.0)
    assert res.weight_strategy == "equal"
    assert res.composition_method == "composite_mean"
    assert res.replicate_count == 3


def test_area_weighted_mean():
    # 2 ha block at 10, 8 ha block at 20 → weighted mean 18
    res = aggregate_samples(
        [{"P": 10}, {"P": 20}],
        weights=[2.0, 8.0],
    )
    # n=2, so weight strategy is still area_weighted but we can't
    # compute stats reliably at n<3. Mean still honours weights.
    assert res.values["P"] == pytest.approx(18.0)
    assert res.weight_strategy == "area_weighted"
    assert res.composition_method == "composite_area_weighted"


def test_missing_weight_falls_back_to_equal_for_whole_call():
    """If any sample lacks a positive weight, switch to equal weighting
    for the whole call. Mixing modes would hide bias."""
    res = aggregate_samples(
        [{"P": 10}, {"P": 20}, {"P": 30}],
        weights=[2.0, None, 8.0],  # type: ignore[list-item]
    )
    assert res.values["P"] == pytest.approx(20.0)  # arithmetic mean, not 26
    assert res.weight_strategy == "equal"
    assert res.composition_method == "composite_mean"


def test_zero_or_negative_weight_triggers_fallback():
    res = aggregate_samples(
        [{"P": 10}, {"P": 30}, {"P": 50}],
        weights=[1.0, 0.0, 1.0],
    )
    assert res.values["P"] == pytest.approx(30.0)
    assert res.weight_strategy == "equal"


def test_none_values_skipped_per_parameter():
    """A sample missing a parameter should not drop the whole sample,
    just that one parameter for that sample."""
    res = aggregate_samples([
        {"P": 10, "K": 100},
        {"P": None, "K": 200},
        {"P": 30, "K": 300},
    ])
    assert res.values["P"] == pytest.approx(20.0)   # (10+30)/2
    assert res.stats["P"].n == 2
    assert res.values["K"] == pytest.approx(200.0)  # (100+200+300)/3
    assert res.stats["K"].n == 3


def test_nan_treated_as_missing():
    res = aggregate_samples([
        {"P": 10},
        {"P": float("nan")},
        {"P": 30},
    ])
    assert res.values["P"] == pytest.approx(20.0)
    assert res.stats["P"].n == 2


def test_outlier_detection_at_n_ge_3():
    """A sample >2σ from mean on a given param is flagged, not dropped."""
    res = aggregate_samples([
        {"P": 20},
        {"P": 21},
        {"P": 19},
        {"P": 22},
        {"P": 200},  # outlier — ~8σ from rest
    ])
    # Mean includes the outlier (we flag, we don't silently drop)
    assert res.values["P"] > 50  # mean is pulled up
    assert 4 in res.stats["P"].outlier_sample_indices
    assert len(res.stats["P"].outlier_sample_indices) == 1


def test_no_outliers_when_n_below_threshold():
    res = aggregate_samples([{"P": 10}, {"P": 100}])
    # n=2 is below the stats threshold — no outlier flags even though
    # the values are far apart. We won't false-alarm on too little data.
    assert res.stats["P"].outlier_sample_indices == []
    assert res.stats["P"].cv_pct is None


def test_cv_computed_when_n_ge_3_and_mean_nonzero():
    res = aggregate_samples([{"P": 18}, {"P": 20}, {"P": 22}])
    assert res.stats["P"].cv_pct is not None
    # std ≈ 1.633, mean = 20 → CV ≈ 8.16%
    assert res.stats["P"].cv_pct == pytest.approx(8.16, abs=0.1)


def test_cv_none_when_mean_is_zero():
    res = aggregate_samples([{"P": -1}, {"P": 0}, {"P": 1}])
    assert res.stats["P"].mean == pytest.approx(0.0)
    assert res.stats["P"].cv_pct is None


def test_accepts_values_wrapper_shape():
    """Callers attaching metadata should be able to nest values."""
    res = aggregate_samples([
        {"values": {"P": 10}, "location_label": "north", "weight_ha": 2.0},
        {"values": {"P": 30}, "location_label": "south", "weight_ha": 8.0},
    ], weights=[2.0, 8.0])
    assert res.values["P"] == pytest.approx(26.0)
    assert res.weight_strategy == "area_weighted"


def test_weights_length_mismatch_raises():
    with pytest.raises(ValueError):
        aggregate_samples([{"P": 10}, {"P": 20}], weights=[1.0])


def test_empty_sample_list_raises():
    with pytest.raises(ValueError):
        aggregate_samples([])


def test_stats_as_dict_shape_for_db():
    res = aggregate_samples([{"P": 18}, {"P": 20}, {"P": 22}])
    d = res.stats_as_dict()
    assert d["weight_strategy"] == "equal"
    assert "P" in d
    assert set(d["P"].keys()) == {
        "n", "mean", "variance", "cv_pct", "outlier_sample_indices",
    }


def test_parameter_only_in_some_samples():
    res = aggregate_samples([
        {"P": 10, "K": 100},
        {"P": 20},              # K missing entirely
        {"P": 30, "K": 300},
    ])
    assert res.stats["K"].n == 2
    assert res.values["K"] == pytest.approx(200.0)
    assert res.stats["P"].n == 3


def test_composition_method_single_when_one_sample_even_with_weight():
    res = aggregate_samples([{"P": 10}], weights=[5.0])
    assert res.composition_method == "single"
    assert res.replicate_count == 1


def test_area_weighted_two_samples_still_flagged_as_area_weighted():
    """composition_method tracks *how* samples were combined, not whether
    stats could be computed."""
    res = aggregate_samples(
        [{"P": 10}, {"P": 20}],
        weights=[1.0, 3.0],
    )
    assert res.composition_method == "composite_area_weighted"
    assert res.weight_strategy == "area_weighted"


def test_negative_values_handled_like_positives():
    """Some lab values (e.g. some adjustment targets) can be negative.
    Aggregation should not guard against them."""
    res = aggregate_samples([{"N_balance": -10}, {"N_balance": -20}, {"N_balance": -30}])
    assert res.values["N_balance"] == pytest.approx(-20.0)
