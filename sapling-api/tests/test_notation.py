"""Golden-case tests for notation.py — SA notation <-> percentage conversion.

These lock in current behavior of pct_to_sa_notation / sa_notation_to_pct
and the private _format_secondaries helper. Audit-flagged quirks are
encoded as tests so fixes have a target to change.
"""

from __future__ import annotations

import pytest

from app.services.notation import (
    _format_secondaries,
    pct_to_sa_notation,
    sa_notation_to_pct,
)


class TestSaNotationToPct:
    @pytest.mark.golden
    def test_basic_2_3_2_at_22(self):
        n, p, k = sa_notation_to_pct(2, 3, 2, 22)
        assert n == pytest.approx(6.2857, abs=0.001)
        assert p == pytest.approx(9.4286, abs=0.001)
        assert k == pytest.approx(6.2857, abs=0.001)

    @pytest.mark.golden
    def test_5_1_5_at_30(self):
        n, p, k = sa_notation_to_pct(5, 1, 5, 30)
        assert n + p + k == pytest.approx(30.0)

    @pytest.mark.golden
    def test_zero_ratio_sum_returns_zeros(self):
        assert sa_notation_to_pct(0, 0, 0, 30) == (0.0, 0.0, 0.0)

    @pytest.mark.golden
    def test_preserves_total(self):
        n, p, k = sa_notation_to_pct(3, 1, 2, 18)
        assert n + p + k == pytest.approx(18.0, abs=0.001)


class TestPctToSaNotation:
    @pytest.mark.golden
    def test_simple_2_3_2(self):
        sa, intl = pct_to_sa_notation(6.2857, 9.4286, 6.2857)
        assert sa.startswith("2:3:2")
        assert "(22" in sa
        assert "N 6.3%" in intl
        assert "P 9.4%" in intl
        assert "K 6.3%" in intl

    @pytest.mark.golden
    def test_zero_all_returns_zero_notation(self):
        sa, intl = pct_to_sa_notation(0, 0, 0)
        assert sa == "0:0:0 (0)"
        assert intl == "N 0% P 0% K 0%"

    @pytest.mark.golden
    def test_zero_all_with_secondary(self):
        """When NPK=0 but secondaries exist (e.g. Ca-only product),
        SA notation still emits 0:0:0 but with the Ca tail appended."""
        sa, intl = pct_to_sa_notation(0, 0, 0, {"Ca": 15})
        assert sa.startswith("0:0:0")
        assert "Ca 15.0%" in sa

    @pytest.mark.golden
    def test_only_n_present(self):
        """Urea-like 46% N. Algorithm caps the ratio search at denom=20.0,
        so it can't find [1,0,0] (which would need denom=46). It settles
        on [2,0,0]. This is a quirk of the denom_x10 upper bound (200)
        — locking in current behavior so a future fix (raise the bound
        for single-nutrient cases) trips the test."""
        sa, intl = pct_to_sa_notation(46.0, 0, 0)
        assert sa == "2:0:0 (46)"
        assert "N 46.0%" in intl

    @pytest.mark.golden
    def test_only_k_present(self):
        """Same denom-bound quirk: 60% K lands on [0,0,3] not [0,0,1]."""
        sa, intl = pct_to_sa_notation(0, 0, 60.0)
        assert sa == "0:0:3 (60)"
        assert "K 60.0%" in intl

    @pytest.mark.golden
    def test_secondary_nutrients_appended(self):
        sa, intl = pct_to_sa_notation(4, 1, 4, {"Ca": 4.0, "Mg": 1.5})
        assert sa.startswith("4:1:4")
        assert "Ca 4.0%" in sa
        assert "Mg 1.5%" in sa
        assert "Ca 4.0%" in intl
        assert "Mg 1.5%" in intl

    @pytest.mark.golden
    def test_tiny_secondary_below_threshold_ignored(self):
        # Threshold in code is > 0.01
        sa, intl = pct_to_sa_notation(4, 1, 4, {"Zn": 0.005})
        assert "Zn" not in sa

    @pytest.mark.golden
    def test_small_ratios_never_exceed_20(self):
        """The loop caps individual ratios at 20 to avoid ugly notations."""
        sa, _ = pct_to_sa_notation(20, 1, 1)
        parts = sa.split("(")[0].strip()
        ratios = [int(x) for x in parts.split(":")]
        assert max(ratios) <= 20


class TestFormatSecondaries:
    @pytest.mark.golden
    def test_empty_returns_empty(self):
        assert _format_secondaries(None) == ""
        assert _format_secondaries({}) == ""

    @pytest.mark.golden
    def test_ordering_is_standard(self):
        # Order: Ca, Mg, S, Fe, B, Mn, Zn, Mo, Cu
        result = _format_secondaries({"Mg": 2, "Ca": 4, "S": 1})
        parts = result.split(" + ")
        # Expect Ca first, then Mg, then S
        assert parts[0].startswith("Ca")
        assert parts[1].startswith("Mg")
        assert parts[2].startswith("S")

    @pytest.mark.golden
    def test_below_threshold_filtered(self):
        assert _format_secondaries({"Ca": 0.005}) == ""

    @pytest.mark.golden
    def test_formats_one_decimal(self):
        assert _format_secondaries({"Ca": 4}) == "Ca 4.0%"
