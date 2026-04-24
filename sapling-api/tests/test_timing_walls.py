"""Tests for the per-crop timing-walls module.

Locks the hard agronomic rules the allocator + similarity-merger must
never violate. When rules are added or adjusted, tests evolve with
them — they're the spec, not the implementation detail.
"""
from __future__ import annotations

from app.services.timing_walls import (
    CROP_TIMING_WALLS,
    nutrient_blocked_in_month,
    nutrients_may_coapply,
    stage_must_stand_alone,
    walls_for_crop,
)


# ============================================================
# walls_for_crop
# ============================================================

def test_walls_for_exact_crop_name():
    walls = walls_for_crop("Macadamia")
    assert len(walls) >= 1
    assert any(w.kind == "nutrient_cutoff" for w in walls)


def test_walls_for_variant_falls_back_to_parent():
    """'Citrus (Valencia)' picks up 'Citrus' rules."""
    walls = walls_for_crop("Citrus (Valencia)")
    assert any(
        w.kind == "nutrient_antagonism" and "N" in w.together_forbidden
        for w in walls
    )


def test_walls_for_unknown_crop_returns_empty():
    assert walls_for_crop("UnobtainiumFruit") == []


# ============================================================
# Macadamia — Nov-Feb N cutoff (FERTASA 5.8.1)
# ============================================================

def test_mac_n_blocked_november():
    wall = nutrient_blocked_in_month("Macadamia", "N", 11)
    assert wall is not None
    assert "Nov-Feb" in wall.reason


def test_mac_n_blocked_february():
    assert nutrient_blocked_in_month("Macadamia", "N", 2) is not None


def test_mac_n_allowed_october():
    """Oct is the last N window per FERTASA 5.8.1 — not blocked."""
    assert nutrient_blocked_in_month("Macadamia", "N", 10) is None


def test_mac_k_not_blocked_in_november():
    """The wall is N-specific; K is fine in Nov (K peak Oct-Dec per FERTASA)."""
    assert nutrient_blocked_in_month("Macadamia", "K", 11) is None


def test_mac_p_not_blocked_anywhere():
    for m in range(1, 13):
        assert nutrient_blocked_in_month("Macadamia", "P", m) is None


# ============================================================
# Citrus — N+K salinity antagonism (FERTASA 5.7.3)
# ============================================================

def test_citrus_n_and_k_cannot_coapply():
    wall = nutrients_may_coapply("Citrus", {"N", "K"})
    assert wall is not None
    assert "salinity" in wall.reason.lower()


def test_citrus_variant_inherits_antagonism():
    wall = nutrients_may_coapply("Citrus (Valencia)", {"N", "K"})
    assert wall is not None


def test_citrus_n_alone_is_fine():
    assert nutrients_may_coapply("Citrus", {"N"}) is None


def test_citrus_n_with_ca_is_fine():
    """Only N+K combo is walled; N+Ca is fine."""
    assert nutrients_may_coapply("Citrus", {"N", "Ca"}) is None


# ============================================================
# Apple — bitter-pit Ca isolation (WSU)
# ============================================================

def test_apple_cell_division_stage_isolated():
    wall = stage_must_stand_alone("Apple", "Cell-division window")
    assert wall is not None
    assert "bitter-pit" in wall.reason.lower()


def test_apple_other_stage_not_isolated():
    assert stage_must_stand_alone("Apple", "Fruit fill") is None


# ============================================================
# Lucerne — establishment N isolated
# ============================================================

def test_lucerne_establishment_isolated():
    wall = stage_must_stand_alone("Lucerne", "Establishment phase")
    assert wall is not None
    assert "nodulation" in wall.reason.lower()


# ============================================================
# Avocado — Fuerte pre-bloom N cutoff
# ============================================================

def test_avocado_n_blocked_june_july():
    """Default avo N cutoff Jun-Jul (Fuerte-safe)."""
    assert nutrient_blocked_in_month("Avocado", "N", 6) is not None
    assert nutrient_blocked_in_month("Avocado", "N", 7) is not None


def test_avocado_n_allowed_september():
    """Sep = post-fruit-set window; N allowed."""
    assert nutrient_blocked_in_month("Avocado", "N", 9) is None


# ============================================================
# Fallbacks + edge cases
# ============================================================

def test_no_walls_no_blocks_anywhere():
    """A crop without any walls behaves as fully-permissive."""
    for m in range(1, 13):
        assert nutrient_blocked_in_month("Wheat", "N", m) is None
    assert nutrients_may_coapply("Wheat", {"N", "K"}) is None


def test_wall_provenance_is_populated():
    """Every wall must carry a source citation (Tier + section + id)."""
    for crop, walls in CROP_TIMING_WALLS.items():
        for wall in walls:
            assert wall.source_id, f"Wall for {crop} missing source_id"
            assert wall.source_section, f"Wall for {crop} missing source_section"
            assert 1 <= wall.tier <= 6, f"Wall for {crop} tier out of range"
            assert wall.reason, f"Wall for {crop} missing reason"
