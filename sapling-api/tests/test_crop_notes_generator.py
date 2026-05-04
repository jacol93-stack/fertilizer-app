"""Tests for crop_notes_generator — covers both KB-driven and
DB-driven (crop_calc_flags row) note generation.

Lock in the contract that:
  * KB notes survive when no DB row is present
  * Cultivar variants fall back to genus KB
  * DB-driven flags layer ON TOP of the KB without duplicating
    when the same kind is already covered
  * Numeric ceilings produce templated notes with the value embedded
"""
from __future__ import annotations

from app.services.crop_notes_generator import generate_crop_notes


def test_kb_notes_survive_with_no_db_row():
    notes = generate_crop_notes("Garlic")
    kinds = {n.kind for n in notes}
    assert "sulfur_critical" in kinds
    assert "acid_intolerant" in kinds


def test_cultivar_falls_back_to_genus_kb():
    notes = generate_crop_notes("Citrus (Valencia)")
    # Citrus genus has no KB entry; cultivars fall back to genus
    # → no KB notes available. Verify graceful empty return.
    assert notes == []  # neither has KB entries; cultivar fallback empty too


def test_kb_takes_precedence_over_db_flag():
    # Kiwi has a rich KB entry for no_chloride_fertilisers AND a DB
    # flag row would set the same flag. Ensure KB content wins (single
    # note, not two for the same kind).
    db_row = {
        "skip_cation_ratio_path": True,
        "no_chloride_fertilisers": True,
        "source": "DB seed for test",
        "source_section": "n/a",
    }
    notes = generate_crop_notes("Kiwi", db_row)
    no_chloride = [n for n in notes if n.kind == "no_chloride_fertilisers"]
    assert len(no_chloride) == 1, f"expected single note, got {[n.headline for n in no_chloride]}"
    # KB headline mentions "acutely chloride-sensitive"; templated DB
    # fallback would be shorter/different.
    assert "acutely" in no_chloride[0].headline.lower()


def test_db_flag_layers_on_when_kb_missing_kind():
    # An imaginary crop with no KB entry — DB flag should produce a
    # templated note.
    db_row = {
        "skip_cation_ratio_path": False,
        "salt_tolerant": True,
        "source": "Test source",
        "source_section": "Test §1",
    }
    notes = generate_crop_notes("FakeTestCrop", db_row)
    salt_notes = [n for n in notes if n.kind == "salt_tolerant"]
    assert len(salt_notes) == 1
    assert "salt-tolerant" in salt_notes[0].headline.lower()
    assert salt_notes[0].source_citation and "Test source" in salt_notes[0].source_citation


def test_numeric_ceiling_n_protein_cap_produces_note_with_value():
    db_row = {
        "n_protein_cap_kg_ha": 80,
        "source": "SAB Maltings + ARC-SGI",
        "source_section": "n/a",
    }
    notes = generate_crop_notes("Barley", db_row)
    cap_notes = [n for n in notes if n.kind == "n_protein_cap"]
    assert len(cap_notes) == 1
    assert "80" in cap_notes[0].detail


def test_numeric_ceiling_zero_does_not_generate_note():
    db_row = {
        "n_protein_cap_kg_ha": 0,
        "source": "Test",
    }
    notes = generate_crop_notes("AnotherFake", db_row)
    assert all(n.kind != "n_protein_cap" for n in notes)


def test_skip_cation_ratio_path_only_surfaces_when_kb_doesnt_cover():
    # Blueberry: KB already has acid_intolerant + no_chloride.
    # If DB row sets skip_cation_ratio_path=True, we want it surfaced
    # because the KB doesn't include that specific kind.
    db_row = {
        "skip_cation_ratio_path": True,
        "source": "MSU E2011",
    }
    notes = generate_crop_notes("Blueberry", db_row)
    skips = [n for n in notes if n.kind == "skip_cation_ratio_path"]
    assert len(skips) == 1


def test_n_fixation_template_for_legume_without_kb_entry():
    # A legume not in the KB — DB row should generate the n_fixation_active
    # note via template.
    db_row = {
        "n_fixation_active": True,
        "mo_responsive": True,
        "inoculant_required": True,
        "source": "FERTASA 5.5.x",
    }
    notes = generate_crop_notes("ImaginaryLegume", db_row)
    kinds = {n.kind for n in notes}
    assert "n_fixation_active" in kinds
    assert "mo_responsive" in kinds
    assert "inoculant_required" in kinds


def test_garlic_db_row_does_not_duplicate_kb_notes():
    # Garlic's DB row sets sulfur_critical=True; KB also has it.
    # Final notes should have ONE sulfur_critical note (KB wins on content).
    db_row = {
        "sulfur_critical": True,
        "acid_intolerant": True,
        "photoperiod_sensitive": True,
        "source": "DB seed",
    }
    notes = generate_crop_notes("Garlic", db_row)
    kinds_count: dict[str, int] = {}
    for n in notes:
        kinds_count[n.kind] = kinds_count.get(n.kind, 0) + 1
    for kind, count in kinds_count.items():
        assert count == 1, f"kind {kind!r} appeared {count} times — should be 1"
