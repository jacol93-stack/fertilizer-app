"""Generate fake SA-style soil lab report PDFs for testing the upload flow.

Produces NviroTek-style multi-sample reports whose block names match the
demo seed so the UI's auto-match can kick in on import. Use alongside
`seed_multi_sample_demo.py` to exercise the Phase 1 PDF extraction path
without a real lab report.

Usage (from `sapling-api/`):

    ./venv/bin/python -m seeds.gen_fake_lab_report
        # writes seeds/fake_reports/{boland.pdf, vrystaat.pdf, kzncane.pdf}

    ./venv/bin/python -m seeds.gen_fake_lab_report --only boland
    ./venv/bin/python -m seeds.gen_fake_lab_report --out-dir /tmp

The layouts intentionally mimic a real lab - SANAS accreditation line,
sample table with units in the header row - so the AI extractor has a
realistic target. Numbers are the same as those the seed inserts, just
written as they'd appear on a lab report (reversed direction: the seed
has already put these values in the DB; this generator is for testing
the *upload* path by *new* blocks against the same farm/client).
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime

from fpdf import FPDF


# ─── Layout helpers ──────────────────────────────────────────────────────


class _LabReportPDF(FPDF):
    def __init__(self, lab_name: str, lab_strapline: str):
        super().__init__(orientation="L", unit="mm", format="A4")
        self._lab_name = lab_name
        self._lab_strapline = lab_strapline
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, self._lab_name, ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, self._lab_strapline, ln=True, align="C")
        self.cell(0, 5, "SANAS T0123 accredited | ISO/IEC 17025", ln=True, align="C")
        self.ln(2)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5,
                  "This report is generated for software testing only. Values are "
                  "plausible but not field-measured.",
                  align="C")


def _add_meta(pdf: FPDF, client: str, farm: str, report_date: str, department: str):
    pdf.set_font("Helvetica", "", 10)
    left = [
        ("Report for:",   f"{client}  /  {farm}"),
        ("Report date:",  report_date),
        ("Lab reference:", f"NVT-{datetime.now().strftime('%Y%m%d')}-DEMO"),
        ("Department:",   department),
    ]
    for label, value in left:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 6, label)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, value, ln=True)
    pdf.ln(3)


_COLUMNS = [
    # (label on PDF, width mm, key in sample dict)
    ("Sample",          22, "sample_id"),
    ("Block",           32, "block_name"),
    ("Crop",            28, "crop"),
    ("pH (H2O)",        16, "pH (H2O)"),
    ("pH (KCl)",        16, "pH (KCl)"),
    ("Org C %",         16, "Org C"),
    ("P Bray-1",        18, "P (Bray-1)"),
    ("K",               16, "K"),
    ("Ca",              18, "Ca"),
    ("Mg",              16, "Mg"),
    ("S",               14, "S"),
    ("Zn",              14, "Zn"),
    ("B",               14, "B"),
    ("Clay %",          14, "Clay"),
]


def _add_sample_table(pdf: FPDF, samples: list[dict]):
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(240, 240, 240)
    for label, width, _ in _COLUMNS:
        pdf.cell(width, 7, label, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for s in samples:
        for _, width, key in _COLUMNS:
            raw = s.get(key)
            if raw is None:
                text = "-"
            elif isinstance(raw, float):
                text = f"{raw:.1f}" if raw < 100 else f"{raw:.0f}"
            else:
                text = str(raw)
            pdf.cell(width, 6, text, border=1, align="C")
        pdf.ln()
    pdf.ln(4)


def _add_units_note(pdf: FPDF):
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 4,
                   "Units: P, K, Ca, Mg, S, Zn, B, Mn - mg/kg. Clay, Org C - %. "
                   "pH values dimensionless. Extraction: P Bray-1, exchangeable cations in 1M NH4OAc pH 7.")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def _add_signature(pdf: FPDF, analyst: str):
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(60, 6, "Analyst:", ln=False)
    pdf.cell(0, 6, analyst, ln=True)
    pdf.cell(60, 6, "Date reported:", ln=False)
    pdf.cell(0, 6, datetime.now().strftime("%Y-%m-%d"), ln=True)


# ─── Scenario content ────────────────────────────────────────────────────


def _build_boland(out_path: str):
    pdf = _LabReportPDF("NviroTek Analytical Laboratories",
                        "PO Box 1234 | Polokwane | 0700 | info@nvirotek.example")
    pdf.add_page()
    _add_meta(pdf, "[DEMO] Boland Wines", "Paarl Hoofplaas",
              datetime.now().strftime("%Y-%m-%d"), "Soil Analysis")
    # Fresh values for the same Block Noord - different from the seeded
    # 2-day-old analysis, so the conflict modal will offer merge-as-composite.
    _add_sample_table(pdf, [{
        "sample_id": "24-0501", "block_name": "Block Noord", "crop": "Wine grapes",
        "pH (H2O)": 5.9, "pH (KCl)": 5.2, "Org C": 1.8, "P (Bray-1)": 32,
        "K": 195, "Ca": 720, "Mg": 140, "S": 13, "Zn": 2.3, "B": 0.6, "Clay": 24,
    }])
    _add_units_note(pdf)
    _add_signature(pdf, "A. Naidoo")
    pdf.output(out_path)


def _build_vrystaat(out_path: str):
    pdf = _LabReportPDF("NviroTek Analytical Laboratories",
                        "PO Box 1234 | Polokwane | 0700 | info@nvirotek.example")
    pdf.add_page()
    _add_meta(pdf, "[DEMO] Vrystaat Vennote", "Bothaville Hoof",
              datetime.now().strftime("%Y-%m-%d"), "Soil Analysis")
    # Same 5 blocks as the seed - gives auto-match something real to hit.
    # Slightly different numbers from the seed so this counts as a fresh
    # upload (conflict modal will offer resolutions when saving).
    _add_sample_table(pdf, [
        {"sample_id": "24-0601", "block_name": "Block A", "crop": "Maize (dryland)",
         "pH (H2O)": 6.3, "pH (KCl)": 5.5, "Org C": 2.1, "P (Bray-1)": 14, "K": 155, "Ca": 810, "Mg": 185, "S": 11, "Zn": 1.1, "B": 0.4, "Clay": 36},
        {"sample_id": "24-0602", "block_name": "Block B", "crop": "Maize (dryland)",
         "pH (H2O)": 6.2, "pH (KCl)": 5.4, "Org C": 1.9, "P (Bray-1)": 25, "K": 205, "Ca": 760, "Mg": 165, "S": 13, "Zn": 1.3, "B": 0.5, "Clay": 33},
        {"sample_id": "24-0603", "block_name": "Block C", "crop": "Maize (dryland)",
         "pH (H2O)": 6.6, "pH (KCl)": 5.8, "Org C": 2.4, "P (Bray-1)": 38, "K": 285, "Ca": 930, "Mg": 215, "S": 16, "Zn": 1.6, "B": 0.6, "Clay": 41},
        {"sample_id": "24-0604", "block_name": "Block D", "crop": "Maize (dryland)",
         "pH (H2O)": 6.4, "pH (KCl)": 5.6, "Org C": 2.2, "P (Bray-1)": 52, "K": 325, "Ca": 890, "Mg": 195, "S": 15, "Zn": 1.8, "B": 0.6, "Clay": 39},
        {"sample_id": "24-0605", "block_name": "Block E", "crop": "Maize (dryland)",
         "pH (H2O)": 6.0, "pH (KCl)": 5.2, "Org C": 1.8, "P (Bray-1)": 20, "K": 185, "Ca": 710, "Mg": 145, "S": 10, "Zn": 1.0, "B": 0.4, "Clay": 29},
    ])
    _add_units_note(pdf)
    _add_signature(pdf, "A. Naidoo")
    pdf.output(out_path)


def _build_kzncane(out_path: str):
    pdf = _LabReportPDF("NviroTek Analytical Laboratories",
                        "PO Box 1234 | Polokwane | 0700 | info@nvirotek.example")
    pdf.add_page()
    _add_meta(pdf, "[DEMO] KZN Cane Co-op", "Eshowe Hoof",
              datetime.now().strftime("%Y-%m-%d"), "Soil Analysis")
    _add_sample_table(pdf, [
        {"sample_id": "24-0701", "block_name": "Noord 1", "crop": "Sugarcane",
         "pH (H2O)": 5.7, "pH (KCl)": 5.0, "Org C": 2.6, "P (Bray-1)": 29, "K": 185, "Ca": 525, "Mg": 132, "S": 15, "Zn": 1.2, "B": 0.5, "Clay": 39},
        {"sample_id": "24-0702", "block_name": "Noord 2", "crop": "Sugarcane",
         "pH (H2O)": 5.8, "pH (KCl)": 5.1, "Org C": 2.5, "P (Bray-1)": 31, "K": 195, "Ca": 545, "Mg": 137, "S": 16, "Zn": 1.3, "B": 0.5, "Clay": 41},
        {"sample_id": "24-0703", "block_name": "Suid 1", "crop": "Sugarcane",
         "pH (H2O)": 5.7, "pH (KCl)": 5.0, "Org C": 2.7, "P (Bray-1)": 28, "K": 180, "Ca": 520, "Mg": 130, "S": 15, "Zn": 1.2, "B": 0.5, "Clay": 38},
        {"sample_id": "24-0704", "block_name": "Suid 2", "crop": "Sugarcane",
         "pH (H2O)": 5.9, "pH (KCl)": 5.2, "Org C": 2.6, "P (Bray-1)": 30, "K": 190, "Ca": 530, "Mg": 134, "S": 16, "Zn": 1.3, "B": 0.5, "Clay": 40},
    ])
    _add_units_note(pdf)
    _add_signature(pdf, "A. Naidoo")
    pdf.output(out_path)


REPORTS = {
    "boland":   _build_boland,
    "vrystaat": _build_vrystaat,
    "kzncane":  _build_kzncane,
}


# ─── Entry point ─────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--only",
        choices=sorted(REPORTS.keys()),
        help="Generate only one scenario instead of all.",
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.join(os.path.dirname(__file__), "fake_reports"),
        help="Directory to write PDFs into. Created if missing.",
    )
    args = parser.parse_args(argv)

    os.makedirs(args.out_dir, exist_ok=True)

    names = [args.only] if args.only else sorted(REPORTS.keys())
    for name in names:
        out_path = os.path.join(args.out_dir, f"{name}.pdf")
        REPORTS[name](out_path)
        print(f"wrote {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
