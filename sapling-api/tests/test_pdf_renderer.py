"""Regression tests for the WeasyPrint PDF renderer.

Locks the Sapling-branded PDF pipeline against silent breakage. A drift
in the design system, missing fonts, or a regression in the engine →
artifact mapping all surface here as a clear failure.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.pdf_renderer import (
    _nutrient_pretty,
    _strip_source_refs,
    render_programme_pdf,
)
from app.services.programme_builder_orchestrator import build_programme
from tests.fixtures.reference_block_inputs import (
    reference_citrus_svr_input,
    reference_mac_levubu_input,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ============================================================
# End-to-end render
# ============================================================

@pytest.fixture(scope="module")
def mac_pdf() -> bytes:
    return render_programme_pdf(build_programme(reference_mac_levubu_input()))


@pytest.fixture(scope="module")
def citrus_pdf() -> bytes:
    return render_programme_pdf(build_programme(reference_citrus_svr_input()))


def test_mac_pdf_renders_non_empty(mac_pdf):
    """Sanity — pipeline produces a non-trivial PDF (cover + content +
    multiple sections). 100KB is well above any error-output threshold."""
    assert len(mac_pdf) > 100_000
    assert mac_pdf[:4] == b"%PDF"


def test_citrus_pdf_renders_non_empty(citrus_pdf):
    assert len(citrus_pdf) > 100_000
    assert citrus_pdf[:4] == b"%PDF"


def test_pdfs_written_to_fixtures_dir():
    """Persist rendered PDFs to tests/fixtures/ for visual review."""
    for name, build_input in (
        ("mac_levubu", reference_mac_levubu_input),
        ("citrus_svr", reference_citrus_svr_input),
    ):
        artifact = build_programme(build_input())
        pdf = render_programme_pdf(artifact)
        out_path = FIXTURES_DIR / f"reference_{name}.pdf"
        out_path.write_bytes(pdf)
        assert out_path.exists()
        assert out_path.stat().st_size > 100_000


def test_operator_mode_not_yet_implemented():
    """Phase E scope. Should fail loudly until built."""
    artifact = build_programme(reference_mac_levubu_input())
    with pytest.raises(NotImplementedError):
        render_programme_pdf(artifact, mode="operator")


# ============================================================
# Disclosure-boundary regression
# ============================================================
# The renderer must NEVER leak source citations, raw material names,
# or factory content into the rendered PDF. We assert this against the
# raw HTML the renderer produces (PDF binary scan is unreliable due to
# font encoding).

def _rendered_html_for(input_builder) -> str:
    """Render the artifact's HTML (pre-PDF) to inspect content."""
    from app.services.pdf_renderer import _build_context, _jinja, _ASSET_DIR
    artifact = build_programme(input_builder())
    context = _build_context(artifact)
    template = _jinja.get_template("programme.html")
    html = template.render(**context)
    return html.replace("__ASSET_DIR__", str(_ASSET_DIR.resolve()))


def test_pdf_renderer_strips_fertasa_refs():
    html = _rendered_html_for(reference_citrus_svr_input)
    assert "FERTASA" not in html
    assert "FERTASA 5.7.3" not in html


def test_pdf_renderer_strips_other_source_names():
    html = _rendered_html_for(reference_mac_levubu_input)
    forbidden = ("SAMAC", "Schoeman", "CRI", "Cedara", "Manson", "Sheard",
                 "ARC-ITSC", "GrainSA", "SASRI")
    for term in forbidden:
        assert term not in html, f"PDF HTML leaked source ref: {term}"


def test_pdf_renderer_no_raw_material_names_in_blends():
    """Per `feedback_client_disclosure_boundary`: products are referenced
    by analysis only, never by raw material name."""
    html = _rendered_html_for(reference_mac_levubu_input)
    forbidden_materials = (
        "Calcium Nitrate", "Potassium Nitrate", "Ammonium Sulphate",
        "MAP", "MKP", "SOP", "KCl", "Urea", "Solubor", "Manure Compost",
        "Magnesium Sulphate", "Magnesium Nitrate", "Zinc Oxide",
    )
    # Note: the ANALYSIS strings legitimately mention nutrients (N, K, P)
    # but never the raw material names. We only check the material names.
    for material in forbidden_materials:
        # The "Calcium Nitrate" check has to allow "Calcium" as a nutrient
        # mention but not the full product name.
        assert material not in html, f"PDF HTML leaked raw material: {material}"


# ============================================================
# Helper functions
# ============================================================

def test_nutrient_pretty_subscripts_p_and_k():
    assert _nutrient_pretty("P2O5") == "P₂O₅"
    assert _nutrient_pretty("K2O") == "K₂O"


def test_nutrient_pretty_passes_through_unaffected():
    assert _nutrient_pretty("N") == "N"
    assert _nutrient_pretty("Ca") == "Ca"
    assert _nutrient_pretty("Mg") == "Mg"


def test_nutrient_pretty_handles_extra_subscripts():
    assert "NH₄" in _nutrient_pretty("NH4")
    assert "NO₃" in _nutrient_pretty("NO3")
    assert "SO₄" in _nutrient_pretty("SO4")
