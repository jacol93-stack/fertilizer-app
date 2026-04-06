"""PDF generation for blend recipes and soil analysis reports.

Ported from blend_app/shared.py — produces identical output.
No Streamlit dependency.
"""

import io
import pathlib
from fpdf import FPDF
from datetime import date

# ── Asset paths ───────────────────────────────────────────────────────────────
_ASSETS = pathlib.Path(__file__).parent.parent.parent / "assets"
LOGO_PATH = _ASSETS / "logo.png"
LOGO_NO_SLOGAN_PATH = _ASSETS / "logo_no_slogan.png"

# ── Brand colours (RGB tuples) ────────────────────────────────────────────────
ORANGE_RGB = (255, 79, 0)
DARK_GREY_RGB = (25, 25, 25)
MED_GREY_RGB = (77, 77, 77)
ORANGE_FILL_RGB = (255, 243, 235)
GREY_LIGHT_RGB = (245, 245, 245)

# ── Soil analysis visual chart colour palette ─────────────────────────────────
_CLS_RGB = {
    "Very Low":  (229, 57, 53),
    "Low":       (255, 152, 0),
    "Optimal":   (67, 160, 71),
    "High":      (41, 121, 255),
    "Very High": (142, 36, 170),
}
_CLS_LIGHT = {
    "Very Low":  (255, 205, 210),
    "Low":       (255, 224, 178),
    "Optimal":   (200, 230, 201),
    "High":      (187, 222, 251),
    "Very High": (225, 190, 231),
}
_STATUS_RGB = {
    "Below ideal": (229, 57, 53),
    "Ideal":       (67, 160, 71),
    "Above ideal": (41, 121, 255),
}

# ── Nutrient list used by soil PDF ────────────────────────────────────────────
NUTRIENTS_SOIL = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Mo", "Cu"]


# ── Soil classification helper (DataFrame version, matching shared.py) ────────
def classify_soil_value(value, param_name, sufficiency_df):
    """Classify a soil analysis value against sufficiency thresholds.
    Returns one of: Very Low, Low, Optimal, High, Very High, or '' if no match.

    sufficiency_df: pandas DataFrame with columns
        Parameter, Very_Low_Max, Low_Max, Optimal_Max, High_Max
    """
    import pandas as pd
    if value is None or pd.isna(value):
        return ""
    row = sufficiency_df[sufficiency_df["Parameter"] == param_name]
    if row.empty:
        return ""
    r = row.iloc[0]
    if value <= r["Very_Low_Max"]:
        return "Very Low"
    elif value <= r["Low_Max"]:
        return "Low"
    elif value <= r["Optimal_Max"]:
        return "Optimal"
    elif value <= r["High_Max"]:
        return "High"
    else:
        return "Very High"


# ═══════════════════════════════════════════════════════════════════════════════
#  build_pdf — Blend Recipe PDF
# ═══════════════════════════════════════════════════════════════════════════════

def build_pdf(blend_name, client, farm, batch, compost_pct, cost_per_ton,
              total_cost, selling_price, margin, is_relaxed, relaxed_scale,
              recipe_data, nutrient_data, sa_notation=None,
              international_notation=None,
              pricing_suggestion=None,
              company_details=None):
    cd = company_details or {}
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Header: logo top-right, title + slogan just above orange line
    logo_h = 50
    top_margin = 10
    line_y = top_margin + logo_h + 6

    logo_path = LOGO_NO_SLOGAN_PATH if LOGO_NO_SLOGAN_PATH.exists() else LOGO_PATH
    if logo_path.exists():
        pdf.image(str(logo_path), x=200 - logo_h * 1.2, y=top_margin, h=logo_h)

    pdf.set_xy(10, line_y - 17)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(0, 12, "Blend Recipe", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(0, 5, "Fertilise Smarter, Grow Stronger", new_x="LMARGIN", new_y="NEXT")

    # Company details (right side, under logo)
    if cd:
        cy = line_y - 22
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MED_GREY_RGB)
        for line in [
            cd.get("company_name", ""),
            f"Reg: {cd['reg_number']}" if cd.get("reg_number") else "",
            f"VAT: {cd['vat_number']}" if cd.get("vat_number") else "",
            cd.get("address", ""),
            cd.get("phone", ""),
            cd.get("email", ""),
        ]:
            if line:
                pdf.set_xy(130, cy)
                pdf.cell(70, 3.5, line, align="R")
                cy += 3.5

    pdf.set_y(line_y)

    # Accent line
    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Meta info
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MED_GREY_RGB)
    meta_parts = [f"Date: {date.today().strftime('%Y-%m-%d')}"]
    if blend_name:
        meta_parts.insert(0, f"Blend: {blend_name}")
    if client:
        meta_parts.append(f"Client: {client}")
    if farm:
        meta_parts.append(f"Farm: {farm}")
    pdf.cell(0, 6, "  |  ".join(meta_parts), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # KPI summary
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MED_GREY_RGB)
    kpi_items = []
    if sa_notation:
        kpi_items.append(f"SA Notation: {sa_notation}")
    # International notation
    if international_notation:
        kpi_items.append(f"International: {international_notation}")
    elif nutrient_data:
        intl_parts = []
        for row in nutrient_data[:3]:
            try:
                intl_parts.append(f"{float(row[2]):.1f}")
            except (ValueError, IndexError):
                intl_parts.append("0.0")
        if len(intl_parts) == 3:
            kpi_items.append(f"International: N {intl_parts[0]}% P {intl_parts[1]}% K {intl_parts[2]}%")
    kpi_items.append(f"Batch size: {batch:,} kg")
    if recipe_data:
        # Only show compost/chemical breakdown for admin (who gets recipe_data)
        kpi_items.append(f"Compost: {compost_pct:.1f}%")
        kpi_items.append(f"Chemical: {100 - compost_pct:.1f}%")
    for item in kpi_items:
        pdf.cell(0, 5, item, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if is_relaxed:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*ORANGE_RGB)
        pdf.cell(
            0, 5,
            f"Note: Targets relaxed to {relaxed_scale * 100:.1f}% of requested levels.",
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(2)

    def pdf_table(title, columns, widths, rows):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 9)
        header_y = pdf.get_y()
        total_w = sum(widths)
        pdf.set_fill_color(*ORANGE_RGB)
        pdf.rect(pdf.l_margin, header_y, total_w, 6, "F")
        pdf.set_text_color(255, 255, 255)
        for label, w in zip(columns, widths):
            pdf.cell(w, 6, label)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for i, row_vals in enumerate(rows):
            row_y = pdf.get_y()
            if i % 2 == 1:
                pdf.set_fill_color(*GREY_LIGHT_RGB)
                pdf.rect(pdf.l_margin, row_y, total_w, 5, "F")
            pdf.set_text_color(*DARK_GREY_RGB)
            for val, w in zip(row_vals, widths):
                pdf.cell(w, 5, val)
            pdf.ln()

        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.4)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + total_w, pdf.get_y())
        pdf.ln(4)

    # Recipe table
    if recipe_data:
        recipe_cols = ["Material", "Type", "kg", "% of Blend", "Cost (R)"]
        col_widths = [60, 35, 25, 25, 25]
        pdf_table("Recipe", recipe_cols, col_widths, recipe_data)

    # Nutrient analysis table -only show targeted nutrients
    if nutrient_data:
        nut_cols = ["Nutrient", "Target %", "Actual %", "Diff", "kg per ton"]
        nut_widths = [30, 25, 25, 25, 25]
        try:
            targeted_rows = [r for r in nutrient_data if float(r[1]) > 0]
        except (ValueError, IndexError):
            targeted_rows = nutrient_data
        pdf_table("Nutrient Analysis", nut_cols, nut_widths, targeted_rows)

    # ── Page 2: Pricing Analysis (if available) ──────────────────────────
    if pricing_suggestion and pricing_suggestion.get("found", 0) > 0:
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 12, "Pricing Analysis", new_x="LMARGIN", new_y="NEXT")

        # Accent line
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        # Method note
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*MED_GREY_RGB)
        w = pricing_suggestion.get("weights", {})
        if pricing_suggestion["method"] == "tight":
            method_txt = (f"Based on {pricing_suggestion['found']} similar blends "
                          f"(within R500 cost-weighted nutrient distance)")
        elif pricing_suggestion["method"] == "widened":
            method_txt = (f"Based on {pricing_suggestion['found']} broadly similar blends "
                          f"(within R1,000 -widened due to few close matches)")
        else:
            method_txt = "Estimate from regression model using all historical blends"
        pdf.cell(0, 5, method_txt, new_x="LMARGIN", new_y="NEXT")
        if w:
            pdf.cell(0, 5,
                     f"Nutrient cost weights:  N: R{w.get('N',0):,.0f}/%   "
                     f"P: R{w.get('P',0):,.0f}/%   K: R{w.get('K',0):,.0f}/%",
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Price summary boxes
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 8, "Suggested Selling Price", new_x="LMARGIN", new_y="NEXT")

        box_y = pdf.get_y()
        box_w = 45
        box_h = 22
        gap = 3
        labels = ["Your Cost", "Low", "Mid", "High"]
        values = [
            f"R {cost_per_ton:,.0f}",
            f"R {pricing_suggestion['low']:,.0f}",
            f"R {pricing_suggestion['mid']:,.0f}",
            f"R {pricing_suggestion['high']:,.0f}",
        ]
        margins_list = [
            None,
            pricing_suggestion['low'] - cost_per_ton,
            pricing_suggestion['mid'] - cost_per_ton,
            pricing_suggestion['high'] - cost_per_ton,
        ]

        for i, (lbl, val, mgn) in enumerate(zip(labels, values, margins_list)):
            x = pdf.l_margin + i * (box_w + gap)
            # Box background
            if i == 0:
                pdf.set_fill_color(*GREY_LIGHT_RGB)
            else:
                pdf.set_fill_color(*ORANGE_FILL_RGB)
            pdf.rect(x, box_y, box_w, box_h, "F")
            # Border
            pdf.set_draw_color(*ORANGE_RGB)
            pdf.set_line_width(0.3)
            pdf.rect(x, box_y, box_w, box_h, "D")
            # Label
            pdf.set_xy(x, box_y + 2)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(box_w, 4, lbl, align="C")
            # Value
            pdf.set_xy(x, box_y + 7)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(box_w, 6, val, align="C")
            # Margin
            if mgn is not None:
                pdf.set_xy(x, box_y + 15)
                pdf.set_font("Helvetica", "", 7)
                color = (0, 130, 0) if mgn >= 0 else (200, 0, 0)
                pdf.set_text_color(*color)
                pdf.cell(box_w, 4, f"R {mgn:,.0f} margin", align="C")

        pdf.set_y(box_y + box_h + 6)

        # Regression note
        if pricing_suggestion.get("regression"):
            reg = pricing_suggestion["regression"]
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(0, 5,
                     f"Regression model estimate: R {reg['predicted']:,.0f}/ton",
                     new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        # Comparable blends table
        comps = pricing_suggestion.get("comparables", [])
        if comps:
            comp_cols = ["Blend", "Client", "Price", "Cost", "Dist.", "N%", "P%", "K%", "Date"]
            comp_widths = [38, 22, 20, 20, 16, 12, 12, 12, 22]
            comp_rows = []
            for c in comps:
                comp_rows.append([
                    str(c["blend_name"])[:22],
                    str(c.get("client", ""))[:12],
                    f"R{c['price']:,.0f}",
                    f"R{c['cost']:,.0f}",
                    f"R{c.get('distance', 0):,.0f}",
                    f"{c['npk']['N']:.1f}",
                    f"{c['npk']['P']:.1f}",
                    f"{c['npk']['K']:.1f}",
                    str(c.get("date", ""))[:10],
                ])
            pdf_table("Comparable Historical Blends", comp_cols, comp_widths,
                      comp_rows)

    elif pricing_suggestion and pricing_suggestion.get("method") == "regression":
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(0, 12, "Pricing Analysis", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(0, 6, "No close historical matches. Regression estimate:",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_GREY_RGB)
        for lbl, val in [("Low", pricing_suggestion["low"]),
                         ("Mid", pricing_suggestion["mid"]),
                         ("High", pricing_suggestion["high"])]:
            pdf.cell(0, 6, f"{lbl}: R {val:,.0f}  "
                     f"(margin R {val - cost_per_ton:,.0f})",
                     new_x="LMARGIN", new_y="NEXT")

    # Footer on last page
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(0, 5, "Generated by Sapling Blend Calculator - Internal Document",
             new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
#  build_soil_pdf — Soil Analysis Report PDF
# ═══════════════════════════════════════════════════════════════════════════════

def build_soil_pdf(customer, farm, field, crop_name, cultivar, yield_target,
                   yield_unit, pop_per_ha, plants_per_field, field_area_ha,
                   agent_name, agent_cell, agent_email,
                   lab_name, analysis_date,
                   soil_values, nutrient_targets, ratio_results,
                   products, total_cost_ha,
                   norms=None, total_cost_field=None, role="admin"):
    """Build a Fertilizer Recommendation Report PDF with visual analysis.

    Args:
        products: list of dicts with keys: product, method, timing,
                  kg_ha, kg_field, price_ha, price_field, nutrients (dict)
        norms: dict of DataFrames from load_soil_norms() (for gauge thresholds)
    """
    pdf = FPDF(orientation="L")
    pdf.set_auto_page_break(auto=False)

    page_w = 297  # A4 landscape
    page_h = 210
    margin = 10
    content_w = page_w - 2 * margin

    logo_path = LOGO_NO_SLOGAN_PATH if LOGO_NO_SLOGAN_PATH.exists() else LOGO_PATH

    # ─── Shared helpers ─────────────────────────────────────────────────

    def page_header(title):
        if logo_path.exists():
            pdf.image(str(logo_path), x=margin, y=8, h=22)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.set_xy(margin + 30, 10)
        pdf.cell(content_w - 30, 10, title, align="C")
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.8)
        pdf.line(margin, 30, page_w - margin, 30)

    def page_footer():
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.set_xy(margin, page_h - 12)
        pdf.cell(content_w / 2, 4,
                 "Generated by Sapling Blend Calculator")
        pdf.cell(content_w / 2, 4,
                 f"Date Printed:  {date.today().strftime('%Y-%m-%d')}",
                 align="R")

    def section_label(y, text):
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(content_w, 5, text, new_x="LMARGIN", new_y="NEXT")
        # thin accent underline
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.3)
        pdf.line(margin, y + 5.5, margin + content_w, y + 5.5)

    # ─── Gauge-bar drawing ──────────────────────────────────────────────

    def draw_gauge(x, y, w, h, value, thresholds):
        """Draw a horizontal gauge bar with 5 coloured zones, marker, and scale."""
        vl, lo, opt, hi = thresholds
        max_scale = hi * 1.35 if hi > 0 else 1
        if value > max_scale:
            max_scale = value * 1.15

        zones = [
            (0,   vl,  _CLS_RGB["Very Low"]),
            (vl,  lo,  _CLS_RGB["Low"]),
            (lo,  opt, _CLS_RGB["Optimal"]),
            (opt, hi,  _CLS_RGB["High"]),
            (hi,  max_scale, _CLS_RGB["Very High"]),
        ]

        # Draw each zone
        for z_start, z_end, colour in zones:
            x0 = x + (z_start / max_scale) * w
            x1 = x + min(z_end / max_scale, 1.0) * w
            zw = x1 - x0
            if zw < 0.2:
                continue
            light = _CLS_LIGHT.get(
                [k for k, v in _CLS_RGB.items() if v == colour][0], colour)
            pdf.set_fill_color(*light)
            pdf.set_draw_color(*colour)
            pdf.set_line_width(0.15)
            pdf.rect(x0, y, zw, h, "FD")

        # Optimal zone highlight
        ox0 = x + (lo / max_scale) * w
        ox1 = x + min(opt / max_scale, 1.0) * w
        pdf.set_draw_color(*_CLS_RGB["Optimal"])
        pdf.set_line_width(0.5)
        pdf.rect(ox0, y, ox1 - ox0, h, "D")

        # Scale labels below bar — zone boundaries
        scale_y = y + h + 0.8
        pdf.set_font("Helvetica", "B", 7)
        boundaries = [vl, lo, opt, hi]
        for bv in boundaries:
            bx = x + (bv / max_scale) * w
            fmt = ".0f" if bv >= 10 else (".1f" if bv >= 1 else ".2f")
            # Tick mark
            pdf.set_draw_color(150, 150, 150)
            pdf.set_line_width(0.15)
            pdf.line(bx, y + h, bx, y + h + 1.5)
            # Label
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(bx - 6, scale_y)
            pdf.cell(12, 4, f"{bv:{fmt}}", align="C")

        # Value marker — diamond
        marker_x = x + min(value / max_scale, 1.0) * w
        marker_y = y + h / 2
        d = h * 0.45
        pdf.set_fill_color(*DARK_GREY_RGB)
        pdf.set_draw_color(*DARK_GREY_RGB)
        pdf.set_line_width(0.1)
        pdf.polygon([
            (marker_x, marker_y - d),
            (marker_x + d * 0.6, marker_y),
            (marker_x, marker_y + d),
            (marker_x - d * 0.6, marker_y),
        ], style="F")

    def draw_classification_badge(x, y, w, h, classification):
        colour = _CLS_RGB.get(classification, MED_GREY_RGB)
        pdf.set_fill_color(*colour)
        pdf.set_draw_color(*colour)
        pdf.rect(x, y, w, h, "F")
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(x, y)
        pdf.cell(w, h, classification, align="C")

    def draw_gauge_row(y, label, value, unit, thresholds, classification):
        """Draw one complete gauge row: label | value | gauge | badge.
        Returns total height consumed including scale labels."""
        bar_h = 5
        scale_h = 5          # space for scale text below bar
        row_total = bar_h + scale_h + 2
        lbl_w = 30
        val_w = 24
        badge_w = 21
        gauge_w = content_w - lbl_w - val_w - badge_w - 8

        # Label
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(lbl_w, bar_h, label)

        # Value + unit
        pdf.set_xy(margin + lbl_w, y)
        pdf.set_font("Helvetica", "B", 8)
        colour = _CLS_RGB.get(classification, MED_GREY_RGB)
        pdf.set_text_color(*colour)
        val_txt = f"{value:.2f}" if value < 100 else f"{value:.1f}"
        pdf.cell(val_w, bar_h, f"{val_txt} {unit}", align="R")

        # Gauge bar
        gauge_x = margin + lbl_w + val_w + 4
        if thresholds:
            draw_gauge(gauge_x, y, gauge_w, bar_h, value, thresholds)

        # Badge (vertically centred on bar)
        badge_x = margin + content_w - badge_w
        if classification:
            draw_classification_badge(badge_x, y + 0.3, badge_w, bar_h - 0.6,
                                      classification)
        return row_total

    # ─── Ratio range-bar drawing ────────────────────────────────────────

    def draw_ratio_row(y, ratio_name, actual, ideal_min, ideal_max, unit, status,
                       row_total=None):
        """Draw a ratio analysis row with ideal range indicator and scale.
        Returns total height consumed."""
        import math
        if row_total is None:
            row_total = 14
        bar_h = row_total * 0.43
        scale_h = row_total * 0.43
        lbl_w = 32
        val_w = 22
        badge_w = 24
        bar_w = content_w - lbl_w - val_w - badge_w - 10

        # Scale range
        if ideal_max > 100:
            scale_max = max(actual * 1.5, ideal_min * 3) if actual > 0 else ideal_min * 3
        else:
            scale_max = max(ideal_max * 1.8, actual * 1.3) if actual > 0 else ideal_max * 2
        if scale_max <= 0:
            scale_max = 1

        bar_x = margin + lbl_w + val_w + 5
        bar_y = y
        scale_y = bar_y + bar_h + 1

        # Background track
        pdf.set_fill_color(235, 235, 235)
        pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")

        # Ideal range zone (green)
        ix0 = bar_x + (ideal_min / scale_max) * bar_w
        ix1 = bar_x + min(ideal_max / scale_max, 1.0) * bar_w
        pdf.set_fill_color(*_CLS_LIGHT["Optimal"])
        pdf.set_draw_color(*_CLS_RGB["Optimal"])
        pdf.set_line_width(0.5)
        pdf.rect(ix0, bar_y, ix1 - ix0, bar_h, "FD")

        # Scale ticks
        raw_step = scale_max / 5
        magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
        nice_steps = [1, 2, 2.5, 5, 10]
        step = magnitude * min(nice_steps,
                               key=lambda s: abs(s * magnitude - raw_step))
        pdf.set_draw_color(180, 180, 180)
        pdf.set_line_width(0.15)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(130, 130, 130)
        tick_val = 0
        while tick_val <= scale_max * 1.01:
            tx = bar_x + (tick_val / scale_max) * bar_w
            if tx <= bar_x + bar_w + 0.5:
                pdf.line(tx, bar_y + bar_h, tx, bar_y + bar_h + 1.5)
                fmt_t = ".0f" if tick_val >= 10 else (
                    ".1f" if tick_val >= 1 else ".2f")
                pdf.set_xy(tx - 6, scale_y)
                pdf.cell(12, 4, f"{tick_val:{fmt_t}}", align="C")
            tick_val += step

        # Ideal boundary labels (bold green, over the ticks)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*_CLS_RGB["Optimal"])
        fmt = ".0f" if ideal_min >= 10 else (".1f" if ideal_min >= 1 else ".2f")
        pdf.set_xy(ix0 - 6, scale_y)
        pdf.cell(12, 4, f"{ideal_min:{fmt}}", align="C")
        if ideal_max < 100:
            pdf.set_xy(ix1 - 6, scale_y)
            pdf.cell(12, 4, f"{ideal_max:{fmt}}", align="C")

        # Actual value marker
        marker_x = bar_x + min(actual / scale_max, 1.0) * bar_w
        status_colour = _STATUS_RGB.get(status, DARK_GREY_RGB)
        pdf.set_draw_color(*status_colour)
        pdf.set_line_width(0.7)
        pdf.line(marker_x, bar_y - 1, marker_x, bar_y + bar_h + 1)
        d = 1.4
        cy = bar_y + bar_h / 2
        pdf.set_fill_color(*status_colour)
        pdf.polygon([
            (marker_x, cy - d),
            (marker_x + d * 0.7, cy),
            (marker_x, cy + d),
            (marker_x - d * 0.7, cy),
        ], style="F")

        # Row label
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(lbl_w, bar_h, ratio_name)

        # Actual value text
        pdf.set_xy(margin + lbl_w, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*status_colour)
        val_txt = f"{actual:.1f}" if unit == "%" else f"{actual:.2f}"
        pdf.cell(val_w, bar_h, val_txt, align="R")

        # Status badge
        badge_x = margin + content_w - badge_w
        pdf.set_fill_color(*status_colour)
        pdf.rect(badge_x, y + 0.5, badge_w, bar_h - 1, "F")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(badge_x, y + 0.5)
        pdf.cell(badge_w, bar_h - 1, status, align="C")

        return row_total

    # ─── Target-vs-Actual horizontal bar chart ──────────────────────────

    def draw_target_vs_actual(y_start, targets_d, totals_d, nutrients_list):
        """Draw grouped horizontal bars: target (orange) vs actual (grey).
        Dynamically sizes rows to fit on a single page."""
        lbl_w = 14
        num_w = 22
        bar_area_w = content_w - lbl_w - num_w * 2 - 10

        n_items = len(nutrients_list)
        # Available height: from y_start to footer area
        avail_h = (page_h - 18) - y_start
        # Compute pair_h to fit all items (legend takes ~6mm)
        legend_h = 6
        if n_items > 0:
            pair_h = max((avail_h - legend_h) / n_items, 6)
        else:
            pair_h = 13.5
        row_h = pair_h * 0.42
        gap = pair_h * 0.08

        all_vals = list(targets_d.values()) + list(totals_d.values())
        max_val = max(all_vals) if all_vals else 1
        if max_val <= 0:
            max_val = 1

        bar_x = margin + lbl_w + num_w + 4
        y = y_start

        # Legend
        pdf.set_fill_color(*ORANGE_RGB)
        pdf.rect(bar_x, y - 5, 4, 3, "F")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.set_xy(bar_x + 5, y - 5.5)
        pdf.cell(15, 3.5, "Target")
        pdf.set_fill_color(*MED_GREY_RGB)
        pdf.rect(bar_x + 28, y - 5, 4, 3, "F")
        pdf.set_xy(bar_x + 33, y - 5.5)
        pdf.cell(15, 3.5, "Products")
        y += 1

        for nut in nutrients_list:
            target_v = targets_d.get(nut, 0)
            actual_v = totals_d.get(nut, 0)

            # Label
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(lbl_w, pair_h, nut)

            # Target bar
            t_w = (target_v / max_val) * bar_area_w if target_v > 0 else 0
            pdf.set_fill_color(*ORANGE_RGB)
            if t_w > 0.5:
                pdf.rect(bar_x, y + 0.5, t_w, row_h - 1, "F")
            pdf.set_xy(margin + lbl_w, y)
            pdf.set_font("Helvetica", "", 6.5)
            pdf.set_text_color(*ORANGE_RGB)
            pdf.cell(num_w, row_h, f"{target_v:.1f}", align="R")

            # Actual bar
            a_w = (actual_v / max_val) * bar_area_w if actual_v > 0 else 0
            pdf.set_fill_color(*MED_GREY_RGB)
            if a_w > 0.5:
                pdf.rect(bar_x, y + row_h + gap - 0.5, a_w, row_h - 1, "F")
            pdf.set_xy(margin + lbl_w, y + row_h + gap)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(num_w, row_h, f"{actual_v:.1f}", align="R")

            # Over/short label
            diff = actual_v - target_v
            if abs(diff) > 0.01:
                pdf.set_xy(bar_x + max(t_w, a_w) + 2,
                           y + (row_h + gap) / 2 - 1.5)
                pdf.set_font("Helvetica", "B", 6)
                if diff >= 0:
                    pdf.set_text_color(*_CLS_RGB["Optimal"])
                    pdf.cell(18, 3, f"+{diff:.1f}")
                else:
                    pdf.set_text_color(*_CLS_RGB["Very Low"])
                    pdf.cell(18, 3, f"{diff:.1f}")

            y += pair_h

        return y

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 1 -Fertilizer Recommendation Report
    # ═════════════════════════════════════════════════════════════════════
    pdf.add_page()
    page_header("FERTILIZER RECOMMENDATION REPORT")

    # Info boxes
    box_w = (content_w - 6) / 3
    box_y = 34

    def info_box(x, y_top, title, items):
        pdf.set_xy(x, y_top)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.set_fill_color(*ORANGE_FILL_RGB)
        pdf.cell(box_w, 6, title, fill=True, align="C",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MED_GREY_RGB)
        for label, value in items:
            pdf.set_x(x)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(25, 4.5, f"{label}:", new_x="END")
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(box_w - 25, 4.5, str(value or ""),
                     new_x="LMARGIN", new_y="NEXT")

    info_box(margin, box_y, "Customer", [
        ("Name", customer), ("Farm", farm), ("Field", field),
    ])
    field_info = [
        ("Yield Target", f"{yield_target} {yield_unit}" if yield_target else ""),
        ("Pop/Ha", f"{pop_per_ha:,}" if pop_per_ha else ""),
    ]
    if plants_per_field:
        field_info.append(("Plants/Field", f"{plants_per_field:,}"))
    if field_area_ha:
        field_info.append(("Field Size", f"{field_area_ha} ha"))
    info_box(margin + box_w + 3, box_y, "Field Info", field_info)
    info_box(margin + 2 * (box_w + 3), box_y, "Agent", [
        ("Name", agent_name), ("Cell No", agent_cell), ("E-mail", agent_email),
    ])

    box_y2 = box_y + 30
    info_box(margin, box_y2, "Soil Analysis", [
        ("Date", analysis_date), ("Lab", lab_name),
    ])
    info_box(margin + box_w + 3, box_y2, "Crop", [
        ("Crop", crop_name), ("Cultivar", cultivar or crop_name),
    ])
    # Total cost box
    pdf.set_xy(margin + 2 * (box_w + 3), box_y2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.set_fill_color(*ORANGE_FILL_RGB)
    pdf.cell(box_w, 6, "Total Cost", fill=True, align="C",
             new_x="LMARGIN", new_y="NEXT")
    x_cost = margin + 2 * (box_w + 3)
    pdf.set_x(x_cost)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(25, 4.5, "Per Ha:", new_x="END")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(box_w - 25, 4.5, f"R{total_cost_ha:,.2f}" if total_cost_ha else "",
             align="R", new_x="LMARGIN", new_y="NEXT")

    # Nutrient Totals table
    nut_y = box_y2 + 24
    pdf.set_xy(margin, nut_y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(content_w, 6, "Nutrient Totals and Targets", align="C",
             new_x="LMARGIN", new_y="NEXT")
    nut_y += 7

    nutrients_display = NUTRIENTS_SOIL
    label_w = 22
    nut_w = (content_w - label_w) / len(nutrients_display)

    # Header row
    pdf.set_xy(margin, nut_y)
    pdf.set_fill_color(*ORANGE_RGB)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(label_w, 5, "", fill=True)
    for nut in nutrients_display:
        pdf.cell(nut_w, 5, nut, fill=True, align="C")
    nut_y += 5

    targets_dict = {t["Nutrient"]: t["Target_kg_ha"] for t in nutrient_targets}
    totals_dict = {}
    for p in products:
        for nk, nv in (p.get("nutrients") or {}).items():
            totals_dict[nk] = totals_dict.get(nk, 0) + (nv or 0)

    for row_label, row_vals, bold, is_diff in [
        ("Targets", targets_dict, True, False),
        ("Totals", totals_dict, False, False),
        ("Over/Short", None, True, True),
    ]:
        pdf.set_xy(margin, nut_y)
        alt = (nut_y - box_y2) % 2 == 0
        pdf.set_fill_color(*GREY_LIGHT_RGB) if alt else pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "B" if bold else "", 8)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(label_w, 5, row_label, fill=True)
        for nut in nutrients_display:
            if is_diff:
                v = totals_dict.get(nut, 0) - targets_dict.get(nut, 0)
                if abs(v) > 0.01:
                    pdf.set_text_color(0, 130, 0) if v >= 0 else pdf.set_text_color(200, 0, 0)
                    pdf.cell(nut_w, 5, f"{v:.2f}", fill=True, align="C")
                    pdf.set_text_color(*DARK_GREY_RGB)
                else:
                    pdf.cell(nut_w, 5, "", fill=True, align="C")
            else:
                v = row_vals.get(nut, 0)
                pdf.cell(nut_w, 5, f"{v:.2f}" if v != 0 else "",
                         fill=True, align="C")
        nut_y += 5

    # Accent line
    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.4)
    pdf.line(margin, nut_y, page_w - margin, nut_y)

    # Products table
    prod_y = nut_y + 5
    pdf.set_xy(margin, prod_y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(content_w, 6, "Products", align="C")
    prod_y += 7

    if role == "admin":
        prod_cols = ["Product", "Application Method", "Application Time",
                     "Kg Per Ha", "Price Per Ton", "Price Per Ha"]
        prod_widths = [60, 45, 40, 35, 40, 40]
    else:
        prod_cols = ["Product", "Application Method", "Application Time",
                     "Kg Per Ha", "Price Per Ha"]
        prod_widths = [100, 45, 40, 35, 40]

    pdf.set_xy(margin, prod_y)
    pdf.set_fill_color(*ORANGE_RGB)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(255, 255, 255)
    for lbl, w in zip(prod_cols, prod_widths):
        pdf.cell(w, 5, lbl, fill=True, align="C")
    prod_y += 5

    pdf.set_font("Helvetica", "", 8)
    for i, p in enumerate(products):
        pdf.set_xy(margin, prod_y)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.set_fill_color(*GREY_LIGHT_RGB) if i % 2 == 1 else pdf.set_fill_color(255, 255, 255)
        if role == "admin":
            vals = [
                str(p.get("product", "")), str(p.get("method", "")),
                str(p.get("timing", "")), f"{p.get('kg_ha', 0):.2f}",
                f"R{p.get('price_per_ton', 0):,.2f}",
                f"R{p.get('price_ha', 0):,.2f}",
            ]
        else:
            vals = [
                str(p.get("product", "")), str(p.get("method", "")),
                str(p.get("timing", "")), f"{p.get('kg_ha', 0):.2f}",
                f"R{p.get('price_ha', 0):,.2f}",
            ]
        for val, w in zip(vals, prod_widths):
            pdf.cell(w, 5, val, fill=True, align="C")
        prod_y += 5

    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.4)
    pdf.line(margin, prod_y, margin + sum(prod_widths), prod_y)

    page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 2 -Soil Health Analysis (gauge charts)
    # ═════════════════════════════════════════════════════════════════════
    if soil_values and norms:
        suf_df = norms.get("Soil_Sufficiency")
        if suf_df is not None:
            pdf.add_page()
            page_header("SOIL HEALTH ANALYSIS")

            # Subtitle
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.set_xy(margin, 32)
            parts = [customer, farm, f"Lab: {lab_name}", str(analysis_date)]
            pdf.cell(content_w, 4, "  |  ".join(p for p in parts if p),
                     align="C")

            # Summary strip -count classifications
            class_counts = {}
            classifications_list = []
            for _, row in suf_df.iterrows():
                param = row["Parameter"]
                val = soil_values.get(param)
                if val is not None:
                    cls = classify_soil_value(val, param, suf_df)
                    if cls:
                        class_counts[cls] = class_counts.get(cls, 0) + 1
                        classifications_list.append(
                            (param, val, str(row["Unit"]),
                             [row["Very_Low_Max"], row["Low_Max"],
                              row["Optimal_Max"], row["High_Max"]],
                             cls))

            # Draw summary pills
            pill_y = 37
            pill_x = margin
            total_params = sum(class_counts.values())
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.set_xy(pill_x, pill_y)
            pdf.cell(30, 6, f"{total_params} parameters:")
            pill_x += 31

            for cls_name in ["Very Low", "Low", "Optimal", "High", "Very High"]:
                count = class_counts.get(cls_name, 0)
                if count == 0:
                    continue
                colour = _CLS_RGB[cls_name]
                pw = 32
                pdf.set_fill_color(*colour)
                pdf.rect(pill_x, pill_y, pw, 6, "F")
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(pill_x, pill_y)
                pdf.cell(pw, 6, f"{count} {cls_name}", align="C")
                pill_x += pw + 2

            # Group parameters
            macro_params = ["N (total)", "P (Bray-1)", "K", "Ca", "Mg", "S"]
            general_params = ["pH (H2O)", "pH (KCl)", "Org C", "CEC", "Clay"]
            micro_params = ["Fe", "Mn", "Zn", "Cu", "B", "Mo"]

            cls_lookup = {c[0]: c for c in classifications_list}

            y_cursor = 46

            for group_label, params in [
                ("Macronutrients", macro_params),
                ("General Soil Properties", general_params),
                ("Micronutrients", micro_params),
            ]:
                group_items = [cls_lookup[p] for p in params if p in cls_lookup]
                if not group_items:
                    continue

                # If we'd overflow, start a new page
                row_step = 10  # row_h(7) + scale(3)
                needed = 7 + len(group_items) * row_step
                if y_cursor + needed > page_h - 25:
                    page_footer()
                    pdf.add_page()
                    page_header("SOIL HEALTH ANALYSIS (cont.)")
                    y_cursor = 34

                section_label(y_cursor, group_label)
                y_cursor += 7

                for param, val, unit, thresholds, cls in group_items:
                    rh = draw_gauge_row(y_cursor, param, val, unit,
                                        thresholds, cls)
                    y_cursor += rh

                y_cursor += 1.5  # gap between groups

            # ── Key Findings box ────────────────────────────────────────
            findings = []
            vl_count = class_counts.get("Very Low", 0)
            lo_count = class_counts.get("Low", 0)
            hi_count = class_counts.get("High", 0)
            vh_count = class_counts.get("Very High", 0)

            if vl_count + lo_count > 0:
                deficient = [c[0] for c in classifications_list
                             if c[4] in ("Very Low", "Low")]
                findings.append(
                    f"Deficient ({vl_count + lo_count}): "
                    + ", ".join(deficient)
                    + " -adjustment factors applied to increase targets."
                )
            if hi_count + vh_count > 0:
                excess = [c[0] for c in classifications_list
                          if c[4] in ("High", "Very High")]
                findings.append(
                    f"Elevated ({hi_count + vh_count}): "
                    + ", ".join(excess)
                    + " -targets reduced or zeroed."
                )

            opt_count = class_counts.get("Optimal", 0)
            if opt_count > 0:
                optimal = [c[0] for c in classifications_list if c[4] == "Optimal"]
                findings.append(
                    f"Optimal ({opt_count}): "
                    + ", ".join(optimal)
                    + " -maintenance rates applied."
                )

            if findings:
                # If not enough room, start new page
                needed = 10 + len(findings) * 7
                if y_cursor + needed > page_h - 18:
                    page_footer()
                    pdf.add_page()
                    page_header("SOIL HEALTH ANALYSIS (cont.)")
                    y_cursor = 36

                y_cursor += 4
                section_label(y_cursor, "Key Findings")
                y_cursor += 9

                # Boxed summary area
                box_h = len(findings) * 7 + 4
                pdf.set_fill_color(250, 250, 250)
                pdf.set_draw_color(*ORANGE_RGB)
                pdf.set_line_width(0.4)
                pdf.rect(margin, y_cursor, content_w, box_h, "FD")

                y_cursor += 2
                for finding in findings:
                    pdf.set_xy(margin + 4, y_cursor)
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_text_color(*ORANGE_RGB)
                    pdf.cell(4, 5, ">")
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(*DARK_GREY_RGB)
                    pdf.cell(content_w - 10, 5, finding)
                    y_cursor += 7
                y_cursor += 4

            page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 3 -Nutrient Ratios & Target vs Actual
    # ═════════════════════════════════════════════════════════════════════
    has_ratios = bool(ratio_results)
    has_products = bool(products)

    if has_ratios or has_products:
        pdf.add_page()
        page_header("NUTRIENT BALANCE & RATIOS")

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.set_xy(margin, 32)
        pdf.cell(content_w, 4,
                 f"{crop_name}  |  Yield target: {yield_target} {yield_unit}"
                 f"  |  {customer}",
                 align="C")

        y_cursor = 39

        # ── Ratio analysis (left/top) ───────────────────────────────────
        if has_ratios:
            section_label(y_cursor, "Nutrient Ratios")
            y_cursor += 8

            # Ratio summary pills
            r_counts = {}
            for r in ratio_results:
                s = r["Status"]
                r_counts[s] = r_counts.get(s, 0) + 1

            pill_x = margin
            for status_name in ["Below ideal", "Ideal", "Above ideal"]:
                count = r_counts.get(status_name, 0)
                if count == 0:
                    continue
                colour = _STATUS_RGB[status_name]
                pw = 30
                pdf.set_fill_color(*colour)
                pdf.rect(pill_x, y_cursor, pw, 5, "F")
                pdf.set_font("Helvetica", "B", 7)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(pill_x, y_cursor)
                pdf.cell(pw, 5, f"{count} {status_name}", align="C")
                pill_x += pw + 3
            y_cursor += 8

            # Compute interpretation box height in advance
            below = [r for r in ratio_results if r["Status"] == "Below ideal"]
            above = [r for r in ratio_results if r["Status"] == "Above ideal"]
            interp_lines = []
            if below:
                names = ", ".join(r["Ratio"] for r in below)
                interp_lines.append(
                    ("Below ideal:", names,
                     "Consider corrective amendments.",
                     _STATUS_RGB["Below ideal"]))
            if above:
                names = ", ".join(r["Ratio"] for r in above)
                interp_lines.append(
                    ("Above ideal:", names,
                     "Monitor and reduce contributing inputs.",
                     _STATUS_RGB["Above ideal"]))
            interp_h = (len(interp_lines) * 8 + 10) if interp_lines else 0

            # Dynamically size ratio rows to fit page
            n_ratios = len(ratio_results)
            avail_for_ratios = (page_h - 18) - y_cursor - interp_h
            ratio_row_h = max(avail_for_ratios / n_ratios, 8) if n_ratios > 0 else 14

            for r in ratio_results:
                rh = draw_ratio_row(
                    y_cursor, r["Ratio"], r["Actual"],
                    r["Ideal_Min"], r["Ideal_Max"],
                    r["Unit"], r["Status"],
                    row_total=ratio_row_h,
                )
                y_cursor += rh

            # Ratio interpretation box
            y_cursor += 4
            if interp_lines:
                box_h = len(interp_lines) * 8 + 4
                pdf.set_fill_color(250, 250, 250)
                pdf.set_draw_color(*ORANGE_RGB)
                pdf.set_line_width(0.4)
                pdf.rect(margin, y_cursor, content_w, box_h, "FD")
                y_cursor += 2
                for label, names, action, colour in interp_lines:
                    pdf.set_xy(margin + 4, y_cursor)
                    pdf.set_font("Helvetica", "B", 8.5)
                    pdf.set_text_color(*colour)
                    pdf.cell(28, 6, label)
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(*DARK_GREY_RGB)
                    pdf.cell(content_w - 36, 6, f"{names}  -  {action}")
                    y_cursor += 8
                y_cursor += 4

            y_cursor += 2

        # ── Target vs Actual bar chart (own page, fitted) ─────────────
        if has_products:
            page_footer()
            pdf.add_page()
            page_header("TARGET vs PRODUCT SUPPLY")
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.set_xy(margin, 33)
            pdf.cell(content_w, 4,
                     f"{crop_name}  |  Yield target: {yield_target} {yield_unit}"
                     f"  |  {customer}", align="C")
            y_cursor = 40
            section_label(y_cursor, "Target vs Product Supply (kg/ha)")
            y_cursor += 12
            draw_target_vs_actual(y_cursor, targets_dict, totals_dict,
                                  NUTRIENTS_SOIL)

        page_footer()

    # ═════════════════════════════════════════════════════════════════════
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
#  build_program_pdf — Comprehensive Soil Analysis + Fertilizer Program PDF
# ═══════════════════════════════════════════════════════════════════════════════

def build_program_pdf(
    # Customer info
    customer, farm, field, crop, cultivar, tree_age, yield_target, yield_unit,
    plants_per_ha, field_area_ha,
    agent_name, agent_email,
    lab_name, analysis_date,
    # Soil data
    soil_values,        # dict  {param: numeric_value}
    classifications,    # dict  {param: classification_string}
    ratio_results,      # list of dicts with Ratio, Actual, Ideal_Min, Ideal_Max, Unit, Status
    # Targets
    nutrient_targets,   # list of dicts with Nutrient, Final_Target_kg_ha, Ratio_Adjustment_kg_ha, Ratio_Reasons, etc.
    # Program
    applications,       # list of practical plan applications
    blend_groups,       # list of blend group summaries
    total_cost_ha, total_cost_field, total_cost_tree,
    # Role
    role="admin",
) -> bytes:
    """Build a comprehensive Fertilizer Recommendation Report PDF (landscape A4).

    Contains: Cover & Summary, Soil Analysis Results, Nutrient Ratios,
    Nutrient Requirements, Fertilizer Program (monthly applications),
    and Cost Summary.
    Admin role sees full recipe breakdowns; agent role sees only blended products.
    """
    import math

    pdf = FPDF(orientation="L")
    pdf.set_auto_page_break(auto=False)

    page_w = 297   # A4 landscape
    page_h = 210
    margin = 12
    content_w = page_w - 2 * margin

    is_admin = role == "admin"

    logo_path = LOGO_NO_SLOGAN_PATH if LOGO_NO_SLOGAN_PATH.exists() else LOGO_PATH

    # ─── Layout constants ─────────────────────────────────────────────
    ROW_H = 5.5           # standard table row height
    HDR_H = 6             # table header row height
    TITLE_FONT = 20       # cover title
    SECTION_FONT = 13     # section headers
    BODY_FONT = 9         # body text
    TABLE_FONT = 8        # table cells
    TABLE_HDR_FONT = 8    # table header text
    BLEND_COLOURS = {
        "A": ORANGE_RGB,
        "B": (41, 121, 255),
        "C": (67, 160, 71),
        "D": (142, 36, 170),
        "E": (0, 150, 136),
    }

    # ─── Shared helpers ──────────────────────────────────────────────

    def new_page(title=None, subtitle=None):
        """Add a landscape page with optional header. Returns y cursor."""
        pdf.add_page()
        if title is None:
            return margin
        # Small logo left
        if logo_path.exists():
            pdf.image(str(logo_path), x=margin, y=margin - 1, h=15)
        # Page title centred
        pdf.set_font("Helvetica", "B", SECTION_FONT)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.set_xy(margin + 22, margin)
        pdf.cell(content_w - 22, 8, title, align="C")
        # Thin orange line
        rule_y = margin + 16
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.6)
        pdf.line(margin, rule_y, page_w - margin, rule_y)
        if subtitle:
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.set_xy(margin, rule_y + 1.5)
            pdf.cell(content_w, 4, subtitle, align="C")
        return rule_y + (7 if subtitle else 4)

    def page_footer():
        """Footer on the current page."""
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.set_xy(margin, page_h - 10)
        pdf.cell(content_w / 2, 4, "Generated by Sapling Blend Calculator")
        pdf.cell(content_w / 2, 4,
                 f"Date: {date.today().strftime('%Y-%m-%d')}",
                 align="R")

    def section_heading(y, text):
        """Section header: 13pt bold + thin orange underline."""
        pdf.set_font("Helvetica", "B", SECTION_FONT)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.set_xy(margin, y)
        pdf.cell(content_w, 7, text)
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.4)
        pdf.line(margin, y + 7.5, page_w - margin, y + 7.5)
        return y + 10

    def _ensure_space(y_cursor, needed, title_if_new=None):
        """If not enough room, finish page and start new. Returns y."""
        if y_cursor + needed > page_h - 14:
            page_footer()
            if title_if_new:
                return new_page(title_if_new)
            return new_page()
        return y_cursor

    def table_header(y, cols, widths):
        """Orange header row, white text. Returns y after header."""
        pdf.set_xy(margin, y)
        pdf.set_fill_color(*ORANGE_RGB)
        pdf.set_font("Helvetica", "B", TABLE_HDR_FONT)
        pdf.set_text_color(255, 255, 255)
        total_w = sum(widths)
        pdf.rect(margin, y, total_w, HDR_H, "F")
        for lbl, w in zip(cols, widths):
            pdf.cell(w, HDR_H, lbl, align="C")
        return y + HDR_H

    def table_row(y, vals, widths, bold=False, alt=False, aligns=None,
                  text_colours=None):
        """One table data row. Returns y after."""
        pdf.set_xy(margin, y)
        bg = GREY_LIGHT_RGB if alt else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_font("Helvetica", "B" if bold else "", TABLE_FONT)
        for i, (val, w) in enumerate(zip(vals, widths)):
            a = "C"
            if aligns and i < len(aligns):
                a = aligns[i]
            if text_colours and i < len(text_colours) and text_colours[i]:
                pdf.set_text_color(*text_colours[i])
            else:
                pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(w, ROW_H, str(val), fill=True, align=a)
        return y + ROW_H

    def table_totals_row(y, vals, widths, aligns=None):
        """Bold totals row with orange tint."""
        pdf.set_xy(margin, y)
        pdf.set_fill_color(*ORANGE_FILL_RGB)
        pdf.set_font("Helvetica", "B", TABLE_FONT)
        pdf.set_text_color(*DARK_GREY_RGB)
        for i, (val, w) in enumerate(zip(vals, widths)):
            a = "C"
            if aligns and i < len(aligns):
                a = aligns[i]
            pdf.cell(w, ROW_H, str(val), fill=True, align=a)
        return y + ROW_H

    def table_bottom_line(y, widths):
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.4)
        pdf.line(margin, y, margin + sum(widths), y)

    def _fmt_cost(v):
        if v is None:
            return "-"
        return f"R {v:,.2f}"

    def _fmt_val(v, decimals=2):
        if v is None:
            return "-"
        if not isinstance(v, (int, float)):
            return str(v)
        if abs(v) >= 100:
            return f"{v:,.1f}"
        return f"{v:,.{decimals}f}"

    # ── KPI box ──────────────────────────────────────────────────────

    def draw_kpi_box(x, y, w, h, label, value):
        """KPI card: light grey bg, label small caps, value large bold."""
        pdf.set_fill_color(*GREY_LIGHT_RGB)
        pdf.set_draw_color(220, 220, 220)
        pdf.set_line_width(0.3)
        pdf.rect(x, y, w, h, "FD")
        # label
        pdf.set_xy(x, y + 3)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(w, 4, label.upper(), align="C")
        # value
        pdf.set_xy(x, y + 9)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(w, 8, str(value), align="C")

    # ── Classification badge ─────────────────────────────────────────

    def draw_classification_badge(x, y, w, h, classification):
        colour = _CLS_RGB.get(classification, MED_GREY_RGB)
        pdf.set_fill_color(*colour)
        pdf.rect(x, y, w, h, "F")
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(x, y)
        pdf.cell(w, h, classification, align="C")

    def draw_status_badge(x, y, w, h, status):
        colour = _STATUS_RGB.get(status, MED_GREY_RGB)
        pdf.set_fill_color(*colour)
        pdf.rect(x, y, w, h, "F")
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(x, y)
        pdf.cell(w, h, status, align="C")

    def draw_blend_badge(x, y, letter):
        colour = BLEND_COLOURS.get(letter, MED_GREY_RGB)
        bw, bh = 12, 5
        pdf.set_fill_color(*colour)
        pdf.rect(x, y, bw, bh, "F")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(x, y)
        pdf.cell(bw, bh, letter, align="C")
        return bw + 1

    # ── Gauge-bar drawing (soil parameters) ──────────────────────────

    def draw_gauge(x, y, w, h, value, cls):
        """Horizontal bar with 5 coloured zones and diamond marker.
        cls is classification string like 'Optimal'."""
        zone_names = ["Very Low", "Low", "Optimal", "High", "Very High"]
        zone_w = w / 5
        for zi, zn in enumerate(zone_names):
            zx = x + zi * zone_w
            light = _CLS_LIGHT.get(zn, (235, 235, 235))
            pdf.set_fill_color(*light)
            pdf.set_draw_color(*_CLS_RGB.get(zn, MED_GREY_RGB))
            pdf.set_line_width(0.15)
            pdf.rect(zx, y, zone_w, h, "FD")

        if cls in zone_names:
            idx = zone_names.index(cls)
            hx = x + idx * zone_w
            pdf.set_draw_color(*_CLS_RGB[cls])
            pdf.set_line_width(0.6)
            pdf.rect(hx, y, zone_w, h, "D")
            mx = hx + zone_w / 2
            my = y + h / 2
            d = h * 0.38
            pdf.set_fill_color(*DARK_GREY_RGB)
            pdf.set_line_width(0.1)
            pdf.polygon([
                (mx, my - d),
                (mx + d * 0.65, my),
                (mx, my + d),
                (mx - d * 0.65, my),
            ], style="F")

    def draw_gauge_row(y, label, value, unit, cls):
        """One soil parameter gauge row. Returns height consumed."""
        bar_h = 5
        lbl_w = 42
        val_w = 28
        badge_w = 22
        gauge_w = content_w - lbl_w - val_w - badge_w - 10

        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "", BODY_FONT)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(lbl_w, bar_h, label)

        pdf.set_xy(margin + lbl_w, y)
        pdf.set_font("Helvetica", "B", BODY_FONT)
        colour = _CLS_RGB.get(cls, MED_GREY_RGB)
        pdf.set_text_color(*colour)
        val_txt = _fmt_val(value)
        pdf.cell(val_w, bar_h, f"{val_txt} {unit}", align="R")

        gauge_x = margin + lbl_w + val_w + 4
        draw_gauge(gauge_x, y, gauge_w, bar_h, value, cls)

        badge_x = margin + content_w - badge_w
        if cls:
            draw_classification_badge(badge_x, y + 0.3, badge_w, bar_h - 0.6, cls)

        return bar_h + 2.5

    # ── Ratio range-bar drawing ──────────────────────────────────────

    def draw_ratio_row(y, ratio_name, actual, ideal_min, ideal_max, unit, status):
        """Ratio row with ideal-range bar and marker. Returns height."""
        bar_h = 5.5
        lbl_w = 42
        val_w = 24
        badge_w = 24
        bar_w = content_w - lbl_w - val_w - badge_w - 12

        if ideal_max > 100:
            scale_max = max(actual * 1.5, ideal_min * 3) if actual > 0 else ideal_min * 3
        else:
            scale_max = max(ideal_max * 1.8, actual * 1.3) if actual > 0 else ideal_max * 2
        if scale_max <= 0:
            scale_max = 1

        bar_x = margin + lbl_w + val_w + 6
        bar_y = y

        # background track
        pdf.set_fill_color(235, 235, 235)
        pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")

        # ideal range zone (green)
        ix0 = bar_x + (ideal_min / scale_max) * bar_w
        ix1 = bar_x + min(ideal_max / scale_max, 1.0) * bar_w
        pdf.set_fill_color(*_CLS_LIGHT["Optimal"])
        pdf.set_draw_color(*_CLS_RGB["Optimal"])
        pdf.set_line_width(0.5)
        pdf.rect(ix0, bar_y, max(ix1 - ix0, 0.5), bar_h, "FD")

        # ideal boundary labels
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(*_CLS_RGB["Optimal"])
        fmt = ".0f" if ideal_min >= 10 else (".1f" if ideal_min >= 1 else ".2f")
        pdf.set_xy(ix0 - 5, bar_y + bar_h + 0.5)
        pdf.cell(10, 3, f"{ideal_min:{fmt}}", align="C")
        if ideal_max < 9999:
            pdf.set_xy(ix1 - 5, bar_y + bar_h + 0.5)
            pdf.cell(10, 3, f"{ideal_max:{fmt}}", align="C")

        # actual value marker (vertical line + diamond)
        status_colour = _STATUS_RGB.get(status, DARK_GREY_RGB)
        marker_x = bar_x + min(actual / scale_max, 1.0) * bar_w
        pdf.set_draw_color(*status_colour)
        pdf.set_line_width(0.6)
        pdf.line(marker_x, bar_y - 0.5, marker_x, bar_y + bar_h + 0.5)
        d = 1.3
        cy = bar_y + bar_h / 2
        pdf.set_fill_color(*status_colour)
        pdf.polygon([
            (marker_x, cy - d),
            (marker_x + d * 0.7, cy),
            (marker_x, cy + d),
            (marker_x - d * 0.7, cy),
        ], style="F")

        # row label
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "", BODY_FONT)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(lbl_w, bar_h, ratio_name)

        # actual value text
        pdf.set_xy(margin + lbl_w, y)
        pdf.set_font("Helvetica", "B", BODY_FONT)
        pdf.set_text_color(*status_colour)
        val_txt = f"{actual:.1f}" if unit == "%" else f"{actual:.2f}"
        pdf.cell(val_w, bar_h, val_txt, align="R")

        # status badge
        badge_x = margin + content_w - badge_w
        draw_status_badge(badge_x, y + 0.5, badge_w, bar_h - 1, status)

        return bar_h + 5

    # ── Unit map for soil parameters ─────────────────────────────────
    _UNIT_MAP = {
        "pH (H2O)": "", "pH (KCl)": "", "Org C": "%", "CEC": "cmol/kg",
        "Clay": "%", "N (total)": "mg/kg", "P (Bray-1)": "mg/kg",
        "K": "mg/kg", "Ca": "mg/kg", "Mg": "mg/kg", "S": "mg/kg",
        "Fe": "mg/kg", "Mn": "mg/kg", "Zn": "mg/kg", "Cu": "mg/kg",
        "B": "mg/kg", "Mo": "mg/kg",
    }

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 1 -- Cover
    # ═════════════════════════════════════════════════════════════════════
    pdf.add_page()

    # Large logo top-left (35mm height)
    if logo_path.exists():
        pdf.image(str(logo_path), x=margin, y=margin, h=35)

    # Title
    pdf.set_font("Helvetica", "B", TITLE_FONT)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.set_xy(margin, margin + 40)
    pdf.cell(content_w, 10, "Fertilizer Recommendation Report", align="L")

    # Thin orange separator line
    line_y = margin + 53
    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.8)
    pdf.line(margin, line_y, page_w - margin, line_y)

    # Two-column info layout
    col_w = (content_w - 14) / 2
    info_y = line_y + 6
    left_x = margin
    right_x = margin + col_w + 14

    def _info_pair(x, y_pos, label, value, label_w=34):
        pdf.set_xy(x, y_pos)
        pdf.set_font("Helvetica", "B", BODY_FONT)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(label_w, 5.5, f"{label}:")
        pdf.set_font("Helvetica", "", BODY_FONT)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(col_w - label_w, 5.5, str(value or "-"))

    row_h_info = 6.5
    left_items = [
        ("Customer", customer),
        ("Farm", farm),
        ("Field", field),
        ("Crop", crop),
        ("Cultivar", cultivar or "-"),
        ("Tree Age", f"{tree_age} yrs" if tree_age else "-"),
        ("Yield Target", f"{yield_target} {yield_unit}" if yield_target else "-"),
        ("Plants/Ha", f"{plants_per_ha:,}" if plants_per_ha else "-"),
    ]
    if field_area_ha:
        left_items.append(("Field Area", f"{field_area_ha} ha"))

    for i, (lbl, val) in enumerate(left_items):
        _info_pair(left_x, info_y + i * row_h_info, lbl, val)

    right_items = [
        ("Agent", agent_name or "-"),
        ("Email", agent_email or "-"),
        ("Lab", lab_name or "-"),
        ("Analysis Date", analysis_date or "-"),
        ("Report Date", date.today().strftime("%Y-%m-%d")),
    ]
    for i, (lbl, val) in enumerate(right_items):
        _info_pair(right_x, info_y + i * row_h_info, lbl, val)

    # KPI boxes at bottom
    n_applications = len(applications) if applications else 0
    n_blends = len(blend_groups) if blend_groups else 0
    kpi_data = [
        ("Applications", str(n_applications)),
        ("Blends", str(n_blends)),
        ("Cost/Ha", _fmt_cost(total_cost_ha)),
    ]
    if plants_per_ha and total_cost_tree is not None and total_cost_tree > 0:
        kpi_data.append(("Cost/Tree", _fmt_cost(total_cost_tree)))

    kpi_box_w = 58
    kpi_box_h = 22
    kpi_gap = 8
    kpi_y = page_h - margin - kpi_box_h - 12
    total_kpi_w = len(kpi_data) * kpi_box_w + (len(kpi_data) - 1) * kpi_gap
    kpi_start_x = margin + (content_w - total_kpi_w) / 2

    for i, (lbl, val) in enumerate(kpi_data):
        draw_kpi_box(kpi_start_x + i * (kpi_box_w + kpi_gap),
                     kpi_y, kpi_box_w, kpi_box_h, lbl, val)

    page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 2 -- Soil Health Analysis
    # ═════════════════════════════════════════════════════════════════════
    if soil_values:
        y_cur = new_page("Soil Health Analysis",
                         subtitle=f"{customer}  |  {farm}  |  Lab: {lab_name or '-'}  |  {analysis_date or '-'}")

        general_params = ["pH (H2O)", "pH (KCl)", "Org C", "CEC", "Clay"]
        macro_params = ["N (total)", "P (Bray-1)", "K", "Ca", "Mg", "S"]
        micro_params = ["Fe", "Mn", "Zn", "Cu", "B", "Mo", "Na"]

        for group_label, params in [
            ("General Soil Properties", general_params),
            ("Macronutrients", macro_params),
            ("Micronutrients", micro_params),
        ]:
            group_items = [(p, soil_values[p]) for p in params
                           if p in soil_values and soil_values[p] is not None]
            if not group_items:
                continue

            needed = 10 + len(group_items) * 8
            y_cur = _ensure_space(y_cur, needed, "Soil Health Analysis (cont.)")

            y_cur = section_heading(y_cur, group_label)

            for param, val in group_items:
                cls = classifications.get(param, "") if classifications else ""
                unit = _UNIT_MAP.get(param, "")
                rh = draw_gauge_row(y_cur, param, val, unit, cls)
                y_cur += rh

            y_cur += 2

        page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 3 -- Nutrient Ratios
    # ═════════════════════════════════════════════════════════════════════
    if ratio_results:
        y_cur = new_page("Nutrient Ratios",
                         subtitle=f"{crop}  |  Yield target: {yield_target} {yield_unit}  |  {customer}")

        # Summary status pills
        r_counts = {}
        for r in ratio_results:
            s = r.get("Status", "")
            r_counts[s] = r_counts.get(s, 0) + 1

        pill_x = margin
        for status_name in ["Below ideal", "Ideal", "Above ideal"]:
            count = r_counts.get(status_name, 0)
            if count == 0:
                continue
            colour = _STATUS_RGB[status_name]
            pw = 32
            pdf.set_fill_color(*colour)
            pdf.rect(pill_x, y_cur, pw, 5, "F")
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(pill_x, y_cur)
            pdf.cell(pw, 5, f"{count} {status_name}", align="C")
            pill_x += pw + 3
        y_cur += 8

        for r in ratio_results:
            y_cur = _ensure_space(y_cur, 12, "Nutrient Ratios (cont.)")
            rh = draw_ratio_row(
                y_cur, r["Ratio"], r["Actual"],
                r["Ideal_Min"], r["Ideal_Max"],
                r["Unit"], r["Status"],
            )
            y_cur += rh

        # Interpretation box
        below = [r for r in ratio_results if r["Status"] == "Below ideal"]
        above = [r for r in ratio_results if r["Status"] == "Above ideal"]
        interp_lines = []
        if below:
            names = ", ".join(r["Ratio"] for r in below)
            interp_lines.append(("Below ideal:", names,
                                 "Consider corrective amendments.",
                                 _STATUS_RGB["Below ideal"]))
        if above:
            names = ", ".join(r["Ratio"] for r in above)
            interp_lines.append(("Above ideal:", names,
                                 "Monitor and reduce contributing inputs.",
                                 _STATUS_RGB["Above ideal"]))

        if interp_lines:
            y_cur += 4
            y_cur = _ensure_space(y_cur, len(interp_lines) * 8 + 8,
                                  "Nutrient Ratios (cont.)")
            box_h = len(interp_lines) * 8 + 4
            pdf.set_fill_color(250, 250, 250)
            pdf.set_draw_color(*ORANGE_RGB)
            pdf.set_line_width(0.4)
            pdf.rect(margin, y_cur, content_w, box_h, "FD")
            iy = y_cur + 2
            for label, names, action, colour in interp_lines:
                pdf.set_xy(margin + 4, iy)
                pdf.set_font("Helvetica", "B", 8.5)
                pdf.set_text_color(*colour)
                pdf.cell(28, 6, label)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*DARK_GREY_RGB)
                pdf.cell(content_w - 36, 6, f"{names}  --  {action}")
                iy += 8
            y_cur += box_h + 2

        page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 4 -- Nutrient Requirements
    # ═════════════════════════════════════════════════════════════════════
    if nutrient_targets:
        y_cur = new_page("Nutrient Requirements")

        y_cur = section_heading(y_cur, "Nutrient Targets (kg/ha)")

        nt_cols = ["Nutrient", "Soil Value", "Classification",
                   "Base Target", "Ratio Adj.", "Final Target"]
        nt_widths = [38, 38, 48, 42, 42, 42]
        nt_aligns = ["L", "C", "C", "C", "C", "C"]
        y_cur = table_header(y_cur, nt_cols, nt_widths)

        # Map short nutrient names to soil parameter names for lookup
        _PARAM_MAP = {
            "N": "N (total)", "P": "P (Bray-1)", "K": "K", "Ca": "Ca",
            "Mg": "Mg", "S": "S", "Fe": "Fe", "B": "B", "Mn": "Mn",
            "Zn": "Zn", "Mo": "Mo", "Cu": "Cu", "Na": "Na",
        }

        for i, t in enumerate(nutrient_targets):
            nut = t.get("Nutrient", "")
            # Try to get soil value: first from the target dict itself, then from soil_values
            sv = t.get("Soil_Value", t.get("soil_value", ""))
            if (sv == "" or sv is None) and soil_values:
                param_key = _PARAM_MAP.get(nut, nut)
                sv = soil_values.get(param_key, soil_values.get(nut, ""))
            sv_str = _fmt_val(sv) if isinstance(sv, (int, float)) else (str(sv) if sv else "-")
            # Classification: first from target dict, then from classifications dict
            cls = t.get("Classification", t.get("classification", ""))
            if not cls and classifications:
                param_key = _PARAM_MAP.get(nut, nut)
                cls = classifications.get(param_key, classifications.get(nut, ""))
            base = t.get("Base_Target_kg_ha", t.get("Target_kg_ha", 0))
            adj = t.get("Ratio_Adjustment_kg_ha", 0)
            final = t.get("Final_Target_kg_ha", base)

            base_str = _fmt_val(base) if isinstance(base, (int, float)) else str(base)
            adj_str = f"{adj:+.2f}" if isinstance(adj, (int, float)) and adj != 0 else "-"
            final_str = _fmt_val(final) if isinstance(final, (int, float)) else str(final)

            cls_colour = _CLS_RGB.get(cls, None)
            adj_colour = None
            if isinstance(adj, (int, float)) and adj != 0:
                adj_colour = (0, 130, 0) if adj > 0 else (200, 0, 0)

            colours = [None, None, cls_colour, None, adj_colour, ORANGE_RGB]
            vals = [nut, sv_str, cls, base_str, adj_str, final_str]

            y_cur = _ensure_space(y_cur, ROW_H + 2, "Nutrient Requirements (cont.)")
            if y_cur < margin + 20:
                y_cur = section_heading(y_cur, "Nutrient Targets (kg/ha) (cont.)")
                y_cur = table_header(y_cur, nt_cols, nt_widths)

            y_cur = table_row(y_cur, vals, nt_widths, alt=i % 2 == 1,
                              aligns=nt_aligns, text_colours=colours)

        table_bottom_line(y_cur, nt_widths)

        # Ratio Adjustment Notes
        reasons = []
        for t in nutrient_targets:
            r_list = t.get("Ratio_Reasons", [])
            if isinstance(r_list, list):
                for reason in r_list:
                    if reason and reason not in reasons:
                        reasons.append(reason)
            elif isinstance(r_list, str) and r_list:
                if r_list not in reasons:
                    reasons.append(r_list)

        if reasons:
            y_cur += 6
            y_cur = _ensure_space(y_cur, 10 + len(reasons) * 6,
                                  "Nutrient Requirements (cont.)")
            y_cur = section_heading(y_cur, "Ratio Adjustment Notes")
            box_h = len(reasons) * 6 + 4
            pdf.set_fill_color(250, 250, 250)
            pdf.set_draw_color(*ORANGE_RGB)
            pdf.set_line_width(0.4)
            pdf.rect(margin, y_cur, content_w, box_h, "FD")
            ny = y_cur + 2
            for reason in reasons:
                pdf.set_xy(margin + 4, ny)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*ORANGE_RGB)
                pdf.cell(4, 4, ">")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*DARK_GREY_RGB)
                pdf.cell(content_w - 12, 4, str(reason))
                ny += 6
            y_cur += box_h + 4

        # Ratio warnings (sufficiency conflicts)
        ratio_warnings = []
        for t in nutrient_targets:
            w_list = t.get("Ratio_Warnings", [])
            if isinstance(w_list, list):
                for w in w_list:
                    if w and w not in ratio_warnings:
                        ratio_warnings.append(w)

        if ratio_warnings:
            y_cur += 6
            y_cur = _ensure_space(y_cur, 10 + len(ratio_warnings) * 6,
                                  "Nutrient Requirements (cont.)")
            y_cur = section_heading(y_cur, "Ratio Warnings")
            box_h = len(ratio_warnings) * 6 + 4
            pdf.set_fill_color(255, 252, 240)
            pdf.set_draw_color(200, 160, 0)
            pdf.set_line_width(0.4)
            pdf.rect(margin, y_cur, content_w, box_h, "FD")
            ny = y_cur + 2
            for w in ratio_warnings:
                pdf.set_xy(margin + 4, ny)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(200, 160, 0)
                pdf.cell(4, 4, "!")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*DARK_GREY_RGB)
                pdf.cell(content_w - 12, 4, str(w))
                ny += 6
            y_cur += box_h + 4

        # Simple horizontal bars for N, P, K, Ca final targets
        bar_nutrients = ["N", "P", "K", "Ca"]
        bar_items = [(t.get("Nutrient", ""), t.get("Final_Target_kg_ha", 0))
                     for t in nutrient_targets
                     if t.get("Nutrient", "") in bar_nutrients
                     and t.get("Final_Target_kg_ha", 0) > 0]
        if bar_items:
            y_cur += 4
            y_cur = _ensure_space(y_cur, 10 + len(bar_items) * 8,
                                  "Nutrient Requirements (cont.)")
        page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  PAGE 5+ -- Fertilizer Program
    # ═════════════════════════════════════════════════════════════════════
    if applications:
        y_cur = new_page("Seasonal Fertilizer Program")

        y_cur = section_heading(y_cur, "Monthly Application Schedule")

        # Month names for display
        _MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        # Determine columns
        has_tree_rate = plants_per_ha and any(
            a.get("rate_kg_tree") or a.get("cost_per_tree") for a in applications)

        ap_cols = ["Month", "Stage", "Blend", "N", "P", "K", "Ca", "Mg",
                   "Rate kg/ha", "Method"]
        ap_widths = [18, 40, 18, 16, 16, 16, 16, 16, 22, 22]
        if has_tree_rate:
            ap_cols.append("kg/tree")
            ap_widths.append(18)
        ap_cols.append("Cost/ha")
        ap_widths.append(24)
        if has_tree_rate:
            ap_cols.append("R/tree")
            ap_widths.append(20)

        y_cur = table_header(y_cur, ap_cols, ap_widths)

        # Totals accumulators
        sum_n = sum_p = sum_k = sum_ca = sum_mg = 0.0
        sum_rate_ha = sum_cost_ha = 0.0

        for i, app in enumerate(applications):
            # Read nutrient values — practical plan uses n_kg_ha, p_kg_ha etc.
            n_val = float(app.get("n_kg_ha", 0) or 0)
            p_val = float(app.get("p_kg_ha", 0) or 0)
            k_val = float(app.get("k_kg_ha", 0) or 0)
            ca_val = float(app.get("ca_kg_ha", 0) or 0)
            mg_val = float(app.get("mg_kg_ha", 0) or 0)
            rate_ha = float(app.get("application_rate_kg_ha", 0) or 0)
            rate_tree = float(app.get("rate_kg_tree", 0) or 0)
            cost_ha = float(app.get("cost_per_ha", 0) or 0)
            cost_tree = float(app.get("cost_per_tree", 0) or 0)

            sum_n += n_val
            sum_p += p_val
            sum_k += k_val
            sum_ca += ca_val
            sum_mg += mg_val
            sum_rate_ha += rate_ha
            sum_cost_ha += cost_ha

            # Month name
            month_num = int(app.get("month", 0) or 0)
            month_name = app.get("month_name", "") or (_MONTHS[month_num] if 1 <= month_num <= 12 else str(month_num))

            # Stage names — may be a list
            stage_names = app.get("stage_names", [])
            if isinstance(stage_names, list):
                stage_str = ", ".join(s[:18] for s in stage_names[:2])
            else:
                stage_str = str(stage_names)[:36]

            blend_label = app.get("blend_group", "")
            method = app.get("method", "")

            vals = [
                month_name,
                stage_str[:24],
                str(blend_label),
                f"{n_val:.1f}" if n_val else "-",
                f"{p_val:.1f}" if p_val else "-",
                f"{k_val:.1f}" if k_val else "-",
                f"{ca_val:.1f}" if ca_val else "-",
                f"{mg_val:.1f}" if mg_val else "-",
                f"{rate_ha:.0f}" if rate_ha else "-",
                str(method)[:12] if method else "-",
            ]
            if has_tree_rate:
                vals.append(f"{rate_tree:.3f}" if rate_tree else "-")
            vals.append(_fmt_cost(cost_ha) if cost_ha else "-")
            if has_tree_rate:
                vals.append(_fmt_cost(cost_tree) if cost_tree else "-")

            y_cur = _ensure_space(y_cur, ROW_H + 2,
                                  "Seasonal Fertilizer Program (cont.)")
            if y_cur < margin + 20:
                y_cur = section_heading(y_cur, "Monthly Application Schedule (cont.)")
                y_cur = table_header(y_cur, ap_cols, ap_widths)

            y_cur = table_row(y_cur, vals, ap_widths, alt=i % 2 == 1)

        # Totals row
        total_vals = [
            "TOTAL", "", "",
            f"{sum_n:.1f}", f"{sum_p:.1f}", f"{sum_k:.1f}",
            f"{sum_ca:.1f}", f"{sum_mg:.1f}",
            f"{sum_rate_ha:.0f}", "",
        ]
        if has_tree_rate:
            total_vals.append("")
        total_vals.append(_fmt_cost(sum_cost_ha))
        if has_tree_rate:
            total_vals.append("")
        y_cur = table_totals_row(y_cur, total_vals, ap_widths)
        table_bottom_line(y_cur, ap_widths)

        # ── Blend group summary ──────────────────────────────────────
        if blend_groups:
            y_cur += 8
            y_cur = _ensure_space(y_cur, 10 + len(blend_groups) * 8,
                                  "Seasonal Fertilizer Program (cont.)")
            y_cur = section_heading(y_cur, "Blend Summary")

            from app.services.notation import pct_to_sa_notation

            for bg in blend_groups:
                y_cur = _ensure_space(y_cur, 20,
                                      "Seasonal Fertilizer Program (cont.)")
                letter = str(bg.get("group", bg.get("blend_name", "A")))
                if letter and letter[0].upper() in BLEND_COLOURS:
                    badge_letter = letter[0].upper()
                else:
                    badge_letter = ""

                bx = margin
                if badge_letter:
                    bw = draw_blend_badge(bx, y_cur, badge_letter)
                    bx += bw + 2

                # Calculate blend NPK percentages from recipe
                recipe = bg.get("recipe", [])
                blend_n_pct = 0
                blend_p_pct = 0
                blend_k_pct = 0
                if recipe:
                    # Recipe has pct (% of blend) and we can look up nutrient content
                    # But simpler: calculate from the application data
                    # Use the first application in this blend group's months
                    bg_months = bg.get("months", [])
                    for app in applications:
                        app_month_name = app.get("month_name", "")
                        if app_month_name in bg_months:
                            rate = float(app.get("application_rate_kg_ha", 0) or 0)
                            if rate > 0:
                                blend_n_pct = float(app.get("n_kg_ha", 0)) / rate * 100
                                blend_p_pct = float(app.get("p_kg_ha", 0)) / rate * 100
                                blend_k_pct = float(app.get("k_kg_ha", 0)) / rate * 100
                            break

                sa_notation, intl_notation = pct_to_sa_notation(blend_n_pct, blend_p_pct, blend_k_pct)

                # Line 1: Blend letter + notation
                pdf.set_xy(bx, y_cur)
                pdf.set_font("Helvetica", "B", BODY_FONT)
                pdf.set_text_color(*DARK_GREY_RGB)
                pdf.cell(30, 5, f"Blend {letter}")

                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*MED_GREY_RGB)
                pdf.cell(55, 5, f"SA: {sa_notation}")
                pdf.cell(65, 5, f"Intl: {intl_notation}")

                months_str = ", ".join(bg.get("months", []))
                if is_admin:
                    cpt = bg.get("cost_per_ton")
                    if cpt is not None:
                        pdf.cell(30, 5, f"R{cpt:,.0f}/ton")

                # Line 2: months
                y_cur += 5
                pdf.set_xy(bx, y_cur)
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(*MED_GREY_RGB)
                pdf.cell(content_w, 4, f"Applied: {months_str}")

                y_cur += 8

            # Admin-only: recipe tables per blend
            if is_admin:
                for bg in blend_groups:
                    recipe = bg.get("recipe", [])
                    if not recipe:
                        continue

                    y_cur += 4
                    y_cur = _ensure_space(
                        y_cur, 12 + len(recipe) * ROW_H + 4,
                        "Blend Recipes (Admin)")

                    letter = str(bg.get("group", bg.get("blend_name", "A")))
                    y_cur = section_heading(y_cur, f"Recipe: Blend {letter}")

                    rc_cols = ["Material", "% of Blend", "kg / ton",
                               "Cost / ton"]
                    rc_widths = [90, 45, 55, 55]
                    y_cur = table_header(y_cur, rc_cols, rc_widths)

                    # Scale recipe from application rate to per-ton
                    total_kg_in_recipe = sum(float(m.get("kg", 0)) for m in recipe)
                    scale = 1000 / total_kg_in_recipe if total_kg_in_recipe > 0 else 1

                    for j, mat in enumerate(recipe):
                        kg_per_ton = float(mat.get("kg", 0)) * scale
                        cost_per_ton = float(mat.get("cost", 0)) * scale
                        vals = [
                            str(mat.get("material", "")),
                            f"{mat.get('pct', 0):.1f}%",
                            f"{kg_per_ton:.1f}",
                            _fmt_cost(cost_per_ton),
                        ]
                        y_cur = _ensure_space(
                            y_cur, ROW_H + 2,
                            "Blend Recipes (Admin, cont.)")
                        if y_cur < margin + 20:
                            y_cur = table_header(y_cur, rc_cols, rc_widths)
                        y_cur = table_row(y_cur, vals, rc_widths,
                                          alt=j % 2 == 1)

                    table_bottom_line(y_cur, rc_widths)

        page_footer()

    # ═════════════════════════════════════════════════════════════════════
    #  LAST PAGE -- Cost Summary
    # ═════════════════════════════════════════════════════════════════════
    y_cur = new_page("Cost Summary")

    # Large cost boxes
    cost_items = [("Total Cost / Hectare", total_cost_ha)]
    if plants_per_ha and total_cost_tree is not None and total_cost_tree > 0:
        cost_items.append(("Total Cost / Tree", total_cost_tree))
    if field_area_ha and total_cost_field is not None and total_cost_field > 0:
        cost_items.append(("Total Cost / Field", total_cost_field))

    big_box_w = 88
    big_box_h = 36
    big_gap = 12
    total_boxes_w = len(cost_items) * big_box_w + (len(cost_items) - 1) * big_gap
    start_x = margin + (content_w - total_boxes_w) / 2

    for i, (label, val) in enumerate(cost_items):
        bx = start_x + i * (big_box_w + big_gap)
        pdf.set_fill_color(*GREY_LIGHT_RGB)
        pdf.set_draw_color(220, 220, 220)
        pdf.set_line_width(0.4)
        pdf.rect(bx, y_cur, big_box_w, big_box_h, "FD")
        # label
        pdf.set_xy(bx, y_cur + 5)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(big_box_w, 5, label, align="C")
        # value
        pdf.set_xy(bx, y_cur + 15)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(big_box_w, 12, _fmt_cost(val), align="C")

    y_cur += big_box_h + 14

    # Admin: per-blend cost breakdown
    if is_admin and blend_groups:
        y_cur = _ensure_space(y_cur, 10 + len(blend_groups) * ROW_H + 10,
                              "Cost Summary (cont.)")
        y_cur = section_heading(y_cur, "Cost Breakdown by Blend")

        cd_cols = ["Blend", "NPK Ratio", "Rate kg/ha (total)",
                   "Cost / Ton", "Cost / Ha"]
        cd_widths = [75, 50, 50, 45, 50]
        y_cur = table_header(y_cur, cd_cols, cd_widths)

        for i, bg in enumerate(blend_groups):
            vals = [
                str(bg.get("blend_name", "")),
                str(bg.get("npk_ratio", "")),
                f"{bg.get('total_rate_kg_ha', 0):.0f}" if bg.get("total_rate_kg_ha") else "-",
                _fmt_cost(bg.get("cost_per_ton")),
                _fmt_cost(bg.get("total_cost_ha")),
            ]
            y_cur = table_row(y_cur, vals, cd_widths, alt=i % 2 == 1)
        table_bottom_line(y_cur, cd_widths)
        y_cur += 6

    # Season Nutrient Totals boxes
    season_totals = {}
    if applications:
        for app in applications:
            nutrients = app.get("nutrients", {})
            for nut_key, nut_val in nutrients.items():
                if nut_val:
                    season_totals[nut_key] = season_totals.get(nut_key, 0) + nut_val

    npk_nutrients = ["N", "P", "K", "Ca", "Mg", "S", "Fe", "B", "Mn", "Zn", "Cu", "Mo"]
    displayed = [(n, season_totals.get(n, 0))
                 for n in npk_nutrients if season_totals.get(n, 0) > 0]

    if displayed:
        y_cur = _ensure_space(y_cur, 36, "Cost Summary (cont.)")
        y_cur = section_heading(y_cur, "Season Nutrient Totals (kg/ha)")

        npk_box_w = 38
        npk_box_h = 20
        npk_gap = 4
        row_start = 0
        while row_start < len(displayed):
            row_items = displayed[row_start:row_start + 7]
            total_row_w = len(row_items) * npk_box_w + (len(row_items) - 1) * npk_gap
            nx = margin + (content_w - total_row_w) / 2
            for nut_name, nut_total in row_items:
                pdf.set_fill_color(*GREY_LIGHT_RGB)
                pdf.set_draw_color(220, 220, 220)
                pdf.set_line_width(0.3)
                pdf.rect(nx, y_cur, npk_box_w, npk_box_h, "FD")
                pdf.set_xy(nx, y_cur + 2)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(*ORANGE_RGB)
                pdf.cell(npk_box_w, 5, nut_name, align="C")
                pdf.set_xy(nx, y_cur + 9)
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(*DARK_GREY_RGB)
                pdf.cell(npk_box_w, 7, f"{nut_total:.1f}", align="C")
                nx += npk_box_w + npk_gap
            y_cur += npk_box_h + 4
            row_start += 7

    # Branded footer
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.set_xy(margin, page_h - 18)
    pdf.cell(content_w, 5,
             f"Generated by Sapling Blend Calculator  --  {date.today().strftime('%Y-%m-%d')}",
             align="C")
    page_footer()

    # ═════════════════════════════════════════════════════════════════════
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# SOIL COMPARISON PDF
# ══════════════════════════════════════════════════════════════════════════════

def build_comparison_pdf(
    analyses: list[dict],
    comparison_type: str,
    crop_impact: list[dict],
    recommendations: list[dict],
    role: str = "admin",
) -> bytes:
    """Build a PDF comparing multiple soil analyses."""

    pdf = FPDF(orientation="L")
    pdf.set_auto_page_break(auto=False)

    margin = 15
    page_w = 297
    page_h = 210
    content_w = page_w - 2 * margin

    def page_header(title: str):
        if LOGO_NO_SLOGAN_PATH.exists():
            pdf.image(str(LOGO_NO_SLOGAN_PATH), margin, 8, 30)
        pdf.set_xy(margin, 10)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(content_w, 8, title, align="C")

    def page_footer():
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.set_xy(margin, page_h - 10)
        pdf.cell(content_w, 4,
                 f"Sapling Blend Calculator  |  Soil Comparison  |  {date.today().strftime('%Y-%m-%d')}",
                 align="C")

    def section_title(y: float, text: str):
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(content_w, 5, text)
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.3)
        pdf.line(margin, y + 5.5, margin + content_w, y + 5.5)

    # Collect all parameters
    all_params = []
    for a in analyses:
        for k in (a.get("soil_values") or {}):
            if k not in all_params:
                all_params.append(k)
    all_params.sort()

    labels = []
    for a in analyses:
        parts = [a.get("field") or a.get("farm") or "Unknown"]
        if a.get("crop"):
            parts.append(a["crop"])
        ad = a.get("analysis_date") or (a.get("created_at") or "")[:10]
        if ad:
            parts.append(ad)
        labels.append(" | ".join(parts))

    is_timeline = comparison_type == "timeline"
    mode_label = "Timeline (same field)" if is_timeline else "Snapshot (different fields)"

    num_analyses = len(analyses)
    param_col_w = 35
    val_col_w = (content_w - param_col_w) / max(num_analyses, 1)

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 1 — Soil values table
    # ═══════════════════════════════════════════════════════════════════
    pdf.add_page()
    page_header("SOIL COMPARISON REPORT")

    pdf.set_xy(margin, 22)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(content_w, 4, f"Mode: {mode_label}  |  Comparing {num_analyses} analyses", align="C")

    section_title(30, "Soil Values Comparison")

    y = 38
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(*ORANGE_RGB)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(margin, y)
    pdf.cell(param_col_w, 5, "Parameter", fill=True, align="C")
    for label in labels:
        pdf.cell(val_col_w, 5, label[:30], fill=True, align="C")
    y += 5

    pdf.set_font("Helvetica", "", 7)
    for ri, param in enumerate(all_params):
        if y > page_h - 20:
            page_footer()
            pdf.add_page()
            page_header("SOIL COMPARISON REPORT")
            y = 25

        bg = GREY_LIGHT_RGB if ri % 2 == 1 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.set_xy(margin, y)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(param_col_w, 4.5, param, fill=True)

        for a in analyses:
            sv = a.get("soil_values") or {}
            cls_map = a.get("classifications") or {}
            val = sv.get(param)
            cls = cls_map.get(param, "")
            val_str = str(val) if val is not None else "-"
            if cls:
                val_str += f" ({cls})"
            if cls in _CLS_RGB:
                pdf.set_text_color(*_CLS_RGB[cls])
            else:
                pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(val_col_w, 4.5, val_str, fill=True, align="C")
        y += 4.5

    page_footer()

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 2 — Ratios
    # ═══════════════════════════════════════════════════════════════════
    all_ratios = set()
    for a in analyses:
        for r in (a.get("ratio_results") or []):
            name = r.get("Ratio") or r.get("ratio_name", "")
            if name:
                all_ratios.add(name)

    if all_ratios:
        pdf.add_page()
        page_header("SOIL COMPARISON REPORT")
        section_title(25, "Nutrient Ratio Comparison")

        y = 33
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_fill_color(*ORANGE_RGB)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(margin, y)
        pdf.cell(param_col_w, 5, "Ratio", fill=True, align="C")
        for label in labels:
            pdf.cell(val_col_w, 5, label[:30], fill=True, align="C")
        y += 5

        pdf.set_font("Helvetica", "", 7)
        for ri, ratio_name in enumerate(sorted(all_ratios)):
            bg = GREY_LIGHT_RGB if ri % 2 == 1 else (255, 255, 255)
            pdf.set_fill_color(*bg)
            pdf.set_xy(margin, y)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(param_col_w, 4.5, ratio_name, fill=True)

            for a in analyses:
                ratios = a.get("ratio_results") or []
                r = next((r for r in ratios if (r.get("Ratio") or r.get("ratio_name")) == ratio_name), None)
                if r:
                    val = r.get("Actual") or r.get("actual")
                    status = r.get("Status") or r.get("status", "")
                    val_str = f"{val:.2f}" if val is not None else "-"
                    if status in _STATUS_RGB:
                        pdf.set_text_color(*_STATUS_RGB[status])
                    else:
                        pdf.set_text_color(*DARK_GREY_RGB)
                    pdf.cell(val_col_w, 4.5, f"{val_str} ({status})", fill=True, align="C")
                else:
                    pdf.set_text_color(*MED_GREY_RGB)
                    pdf.cell(val_col_w, 4.5, "-", fill=True, align="C")
            y += 4.5

        page_footer()

    # ═══════════════════════════════════════════════════════════════════
    # Crop Impact (timeline only)
    # ═══════════════════════════════════════════════════════════════════
    if is_timeline and crop_impact:
        for ci in crop_impact:
            if not ci.get("available"):
                continue
            pdf.add_page()
            page_header("SOIL COMPARISON REPORT")
            crops_label = ci.get("crops_label") or ci.get("crop", "")
            section_title(25, f"Crop Impact: {crops_label}")
            pdf.set_xy(margin, 33)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(content_w, 4, f"Period: {ci.get('date_from', '')} to {ci.get('date_to', '')}")

            y = 40
            cols = ["Nutrient", "Before", "After", "Change", "Exp. Depl.", "Interpretation"]
            col_ws = [20, 20, 20, 20, 28, content_w - 108]

            pdf.set_font("Helvetica", "B", 7)
            pdf.set_fill_color(*ORANGE_RGB)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(margin, y)
            for c, w in zip(cols, col_ws):
                pdf.cell(w, 5, c, fill=True, align="C")
            y += 5

            pdf.set_font("Helvetica", "", 7)
            for ri, n in enumerate(ci.get("nutrients", [])):
                if n.get("expected_depletion_kg_ha", 0) == 0 and n.get("actual_change") is None:
                    continue
                if y > page_h - 20:
                    page_footer()
                    pdf.add_page()
                    page_header("SOIL COMPARISON REPORT")
                    y = 25

                bg = GREY_LIGHT_RGB if ri % 2 == 1 else (255, 255, 255)
                pdf.set_fill_color(*bg)
                pdf.set_xy(margin, y)
                pdf.set_text_color(*DARK_GREY_RGB)
                pdf.cell(col_ws[0], 4.5, n["nutrient"], fill=True, align="C")
                pdf.cell(col_ws[1], 4.5,
                         f"{n['value_before']:.1f}" if n.get("value_before") is not None else "-",
                         fill=True, align="C")
                pdf.cell(col_ws[2], 4.5,
                         f"{n['value_after']:.1f}" if n.get("value_after") is not None else "-",
                         fill=True, align="C")
                change = n.get("actual_change")
                if change is not None:
                    if change < 0:
                        pdf.set_text_color(*_CLS_RGB["Very Low"])
                    elif change > 0:
                        pdf.set_text_color(*_CLS_RGB["Optimal"])
                    pdf.cell(col_ws[3], 4.5, f"{change:+.1f}", fill=True, align="C")
                    pdf.set_text_color(*DARK_GREY_RGB)
                else:
                    pdf.cell(col_ws[3], 4.5, "-", fill=True, align="C")
                pdf.cell(col_ws[4], 4.5,
                         f"{n['expected_depletion_kg_ha']:.1f} kg/ha" if n.get("expected_depletion_kg_ha") else "-",
                         fill=True, align="C")
                pdf.cell(col_ws[5], 4.5, n.get("interpretation", "")[:55], fill=True)
                y += 4.5
            page_footer()

    # ═══════════════════════════════════════════════════════════════════
    # Recommendations
    # ═══════════════════════════════════════════════════════════════════
    if recommendations:
        pdf.add_page()
        page_header("SOIL COMPARISON REPORT")
        section_title(25, "Observations & Recommendations")

        y = 33
        pdf.set_font("Helvetica", "", 8)
        type_colours = {
            "success": _CLS_RGB["Optimal"],
            "warning": _CLS_RGB["Low"],
            "info": (41, 121, 255),
        }
        for rec in recommendations:
            if y > page_h - 20:
                page_footer()
                pdf.add_page()
                page_header("SOIL COMPARISON REPORT")
                y = 25
            colour = type_colours.get(rec.get("type", ""), DARK_GREY_RGB)
            pdf.set_fill_color(*colour)
            pdf.ellipse(margin, y + 1, 2.5, 2.5, "F")
            pdf.set_xy(margin + 5, y)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.multi_cell(content_w - 5, 4, rec.get("message", ""), new_x="LMARGIN", new_y="NEXT")
            y = pdf.get_y() + 2
        page_footer()

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ==============================================================================
# QUOTE PDF
# ==============================================================================

def build_quote_pdf(quote: dict, company_details: dict | None = None) -> bytes:
    """Build a professional branded quote PDF for agent download."""
    # Prefer the specific company chosen at quote creation time
    rd = quote.get("request_data") or {}
    cd = rd.get("quoting_company") or company_details or {}
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)

    margin = 15
    page_w = 210
    content_w = page_w - 2 * margin

    # ── Header ─────────────────────────────────────────────────
    # Left side: logo, slogan, QUOTATION title
    logo_path = LOGO_NO_SLOGAN_PATH if LOGO_NO_SLOGAN_PATH.exists() else LOGO_PATH
    logo_bottom = 10
    if logo_path.exists():
        pdf.image(str(logo_path), x=margin, y=10, h=30)
        logo_bottom = 42

    pdf.set_xy(margin, logo_bottom)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MED_GREY_RGB)
    pdf.cell(100, 5, "Fertilise Smarter, Grow Stronger")

    pdf.set_xy(margin, logo_bottom + 6)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(100, 10, "QUOTATION")

    # Right side: company details (right-aligned, starting at top)
    header_bottom = logo_bottom + 18
    if cd:
        cy = 12
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*DARK_GREY_RGB)
        if cd.get("company_name"):
            pdf.set_xy(margin, cy)
            pdf.cell(content_w, 4, str(cd["company_name"]), align="R")
            cy += 5

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*MED_GREY_RGB)
        for line in [
            f"Reg: {cd['reg_number']}" if cd.get("reg_number") else "",
            f"VAT: {cd['vat_number']}" if cd.get("vat_number") else "",
            cd.get("address", ""),
            cd.get("phone", ""),
            cd.get("email", ""),
            cd.get("website", ""),
        ]:
            if line:
                pdf.set_xy(margin, cy)
                pdf.cell(content_w, 3.5, str(line), align="R")
                cy += 4
        header_bottom = max(header_bottom, cy + 2)

    # Orange accent line
    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(1)
    pdf.line(margin, header_bottom, page_w - margin, header_bottom)

    # Helper: check if we need a page break before drawing content
    def check_page(needed_h=30):
        nonlocal y
        if y + needed_h > 280:
            pdf.add_page()
            y = 15

    # ── Quote info strip ───────────────────────────────────────
    y = header_bottom + 5
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_GREY_RGB)

    # Left column
    pdf.set_xy(margin, y)
    pdf.cell(45, 5, "Quote Number:")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(50, 5, str(quote.get("quote_number", "")))
    y += 6

    pdf.set_xy(margin, y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 5, "Date:")
    pdf.set_font("Helvetica", "", 9)
    created = quote.get("created_at", "")
    if created:
        try:
            created = created[:10]
        except Exception:
            pass
    pdf.cell(50, 5, str(created))
    y += 6

    valid = quote.get("valid_until", "")
    if valid:
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(45, 5, "Valid Until:")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(50, 5, str(valid))
        y += 6

    status = quote.get("status", "")
    pdf.set_xy(margin, y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 5, "Status:")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(50, 5, str(status).replace("_", " ").title())
    y += 10

    # ── Client details ─────────────────────────────────────────
    client_cd = quote.get("client_company_details") or {}
    # Calculate box height based on content
    client_lines = 1  # always have client name
    if quote.get("farm_name"):
        client_lines += 1
    if quote.get("field_name"):
        client_lines += 1
    for k in ["company_name", "reg_number", "vat_number", "address", "phone", "email"]:
        if client_cd.get(k):
            client_lines += 1
    box_h = max(22, 10 + client_lines * 6)

    pdf.set_fill_color(*ORANGE_FILL_RGB)
    pdf.rect(margin, y, content_w, box_h, "F")
    pdf.set_xy(margin + 3, y + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*ORANGE_RGB)
    pdf.cell(content_w, 5, "QUOTED TO")

    pdf.set_text_color(*DARK_GREY_RGB)
    cy = y + 8
    def _client_row(label, value):
        nonlocal cy
        if not value:
            return
        pdf.set_xy(margin + 3, cy)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(30, 5, f"{label}:")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(content_w - 36, 5, str(value))
        cy += 6

    _client_row("Client", quote.get("client_name", ""))
    if client_cd.get("company_name") and client_cd["company_name"] != quote.get("client_name"):
        _client_row("Company", client_cd["company_name"])
    _client_row("Reg. No.", client_cd.get("reg_number"))
    _client_row("VAT No.", client_cd.get("vat_number"))
    _client_row("Address", client_cd.get("address"))
    _client_row("Farm", quote.get("farm_name"))
    _client_row("Field", quote.get("field_name"))
    if client_cd.get("phone"):
        _client_row("Phone", client_cd["phone"])
    if client_cd.get("email"):
        _client_row("Email", client_cd["email"])

    y += box_h + 6

    # ── Product details ────────────────────────────────────────
    check_page(50)

    pdf.set_xy(margin, y)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_GREY_RGB)
    pdf.cell(content_w, 6, "PRODUCT DETAILS")
    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.3)
    pdf.line(margin, y + 6.5, margin + content_w, y + 6.5)
    y += 10

    pdf.set_font("Helvetica", "", 9)
    details = []
    if rd.get("product_name"):
        details.append(("Product", str(rd["product_name"])))
    if rd.get("sa_notation") and rd.get("sa_notation") != rd.get("product_name"):
        details.append(("SA Notation", str(rd["sa_notation"])))
    if rd.get("international_notation"):
        details.append(("International", str(rd["international_notation"])))
    if rd.get("batch_size"):
        details.append(("Batch Size", f"{int(rd['batch_size']):,} kg"))
    if rd.get("min_compost_pct") is not None:
        details.append(("Min Compost", f"{rd['min_compost_pct']}%"))
    if rd.get("blend_mode"):
        details.append(("Blend Mode", str(rd["blend_mode"]).title()))
    if rd.get("preferences") and len(rd["preferences"]) > 0:
        details.append(("Preferences", ", ".join(str(p) for p in rd["preferences"])))

    # Also handle targets dict (from nutrient requests)
    targets = rd.get("targets")
    if targets and isinstance(targets, dict):
        for nut, val in targets.items():
            if float(val) > 0:
                details.append((f"{nut} Target", f"{val}%"))

    for label, value in details:
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.cell(45, 5, label)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(100, 5, value)
        y += 6

    y += 5

    # ── Nutrient table (if available) ──────────────────────────
    check_page(40)
    nutrients = rd.get("nutrients")
    if nutrients and isinstance(nutrients, list):
        targeted = [n for n in nutrients if n.get("target", 0) > 0]
        if targeted:
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(content_w, 6, "NUTRIENT ANALYSIS")
            pdf.line(margin, y + 6.5, margin + content_w, y + 6.5)
            y += 10

            cols = ["Nutrient", "Target %", "Actual %", "kg/ton"]
            col_ws = [40, 35, 35, 35]

            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(*ORANGE_RGB)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(margin, y)
            for c, w in zip(cols, col_ws):
                pdf.cell(w, 5, c, fill=True, align="C")
            y += 5

            pdf.set_font("Helvetica", "", 8)
            for i, n in enumerate(targeted):
                bg = GREY_LIGHT_RGB if i % 2 == 1 else (255, 255, 255)
                pdf.set_fill_color(*bg)
                pdf.set_text_color(*DARK_GREY_RGB)
                pdf.set_xy(margin, y)
                pdf.cell(col_ws[0], 4.5, str(n.get("nutrient", "")), fill=True, align="C")
                pdf.cell(col_ws[1], 4.5, f"{n.get('target', 0):.2f}", fill=True, align="C")
                pdf.cell(col_ws[2], 4.5, f"{n.get('actual', 0):.2f}", fill=True, align="C")
                pdf.cell(col_ws[3], 4.5, f"{n.get('kg_per_ton', 0):.1f}", fill=True, align="C")
                y += 4.5

            y += 5

    # Recipe intentionally excluded from client-facing quote PDF

    # ── Pricing section ─────────────────────────────────────────
    check_page(60)
    price = quote.get("quoted_price")
    if price is not None:
        unit_labels = {"per_ton": "per ton", "per_ha": "per hectare", "per_bag": "per bag (50kg)", "total": "total"}
        unit = unit_labels.get(quote.get("price_unit", "per_ton"), quote.get("price_unit", "per ton"))
        qty = rd.get("quantity_tons")
        include_vat = rd.get("include_vat", False)
        vat_rate = rd.get("vat_rate", 15) if include_vat else 0

        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(content_w, 6, "PRICING")
        pdf.set_draw_color(*ORANGE_RGB)
        pdf.set_line_width(0.3)
        pdf.line(margin, y + 6.5, margin + content_w, y + 6.5)
        y += 10

        # Price table
        col_l = content_w * 0.6
        col_r = content_w * 0.4

        def _price_row(label, amount, bold=False):
            nonlocal y
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B" if bold else "", 10 if bold else 9)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(col_l, 6, label)
            pdf.cell(col_r, 6, f"R {amount:,.2f}", align="R")
            y += 6

        _price_row(f"Price excl. VAT ({unit})", price)
        if include_vat:
            vat_amount = price * vat_rate / 100
            _price_row(f"VAT ({vat_rate:.0f}%)", vat_amount)
            # Incl VAT line with orange background
            pdf.set_fill_color(*ORANGE_RGB)
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(col_l, 8, f"Price incl. VAT ({unit})", fill=True)
            pdf.cell(col_r, 8, f"R {price + vat_amount:,.2f}", fill=True, align="R")
            y += 10
        else:
            # Simple total line
            pdf.set_fill_color(*ORANGE_RGB)
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(col_l, 8, f"Total ({unit})", fill=True)
            pdf.cell(col_r, 8, f"R {price:,.2f}", fill=True, align="R")
            y += 10

        if qty:
            unit_price = price * (1 + vat_rate / 100) if include_vat else price
            total = unit_price * float(qty)
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(col_l, 6, f"Quantity: {float(qty):,.1f} tons")
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(col_r, 6, f"R {total:,.2f}", align="R")
            y += 8

        y += 5

    # ── Payment terms ──────────────────────────────────────────
    check_page(30)
    payment = quote.get("payment_terms")
    delivery_from = quote.get("delivery_date_from")
    if payment or delivery_from:
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK_GREY_RGB)
        pdf.cell(content_w, 6, "TERMS & DELIVERY")
        pdf.line(margin, y + 6.5, margin + content_w, y + 6.5)
        y += 10

        pdf.set_font("Helvetica", "", 9)
        terms_labels = {
            "payment_at_order": "Payment at order",
            "payment_on_delivery": "Payment on delivery",
            "30_days": "30 days",
            "other": "Other",
        }
        if payment:
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(45, 5, "Payment Terms:")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK_GREY_RGB)
            pdf.cell(100, 5, terms_labels.get(payment, payment))
            y += 6

        if delivery_from:
            pdf.set_xy(margin, y)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*MED_GREY_RGB)
            pdf.cell(45, 5, "Delivery Window:")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*DARK_GREY_RGB)
            delivery_to = quote.get("delivery_date_to", "")
            pdf.cell(100, 5, f"{delivery_from}" + (f" to {delivery_to}" if delivery_to else ""))
            y += 6

        y += 5

    # ── Agent notes ────────────────────────────────────────────
    notes = quote.get("agent_notes")
    if notes:
        pdf.set_xy(margin, y)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*MED_GREY_RGB)
        pdf.multi_cell(content_w, 4, f"Agent notes: {notes}")
        y = pdf.get_y() + 5

    # ── Footer ─────────────────────────────────────────────────
    pdf.set_y(-25)
    pdf.set_draw_color(*ORANGE_RGB)
    pdf.set_line_width(0.5)
    pdf.line(margin, pdf.get_y(), page_w - margin, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MED_GREY_RGB)
    footer_name = cd.get("company_name", "Sapling Fertilizer")
    footer_site = cd.get("website", "app.saplingfertilizer.co.za")
    footer_parts = [footer_name]
    if footer_site:
        footer_parts.append(footer_site)
    footer_parts.append(date.today().strftime("%Y-%m-%d"))
    pdf.cell(content_w, 4, "  |  ".join(footer_parts), align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
