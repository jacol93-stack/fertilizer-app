"""Generate Season Plan Calculation PDF report."""
from fpdf import FPDF

# Colours
DARK = (30, 30, 30)
HEADING = (34, 120, 74)  # Sapling green
SUBHEADING = (50, 50, 50)
MUTED = (100, 100, 100)
TABLE_HEADER_BG = (34, 120, 74)
TABLE_HEADER_FG = (255, 255, 255)
TABLE_ALT_BG = (245, 248, 245)
ACCENT = (220, 140, 40)
WHITE = (255, 255, 255)


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "Sapling - Season Plan Calculation Reference", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*HEADING)
        self.cell(0, 12, title)
        self.ln(14)

    def subsection(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*SUBHEADING)
        self.cell(0, 9, title)
        self.ln(11)

    def subsubsection(self, title):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*SUBHEADING)
        self.cell(0, 8, title)
        self.ln(9)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(*DARK)
        x = self.get_x()
        w = self.w - self.l_margin - self.r_margin
        self.rect(x, self.get_y(), w, len(text.split("\n")) * 5 + 4, "F")
        self.set_xy(x + 3, self.get_y() + 2)
        self.multi_cell(w - 6, 5, text)
        self.ln(4)

    def table(self, headers, rows, col_widths=None):
        w = self.w - self.l_margin - self.r_margin
        if not col_widths:
            col_widths = [w / len(headers)] * len(headers)

        # Header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*TABLE_HEADER_BG)
        self.set_text_color(*TABLE_HEADER_FG)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=0, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*DARK)
        for ri, row in enumerate(rows):
            if ri % 2 == 1:
                self.set_fill_color(*TABLE_ALT_BG)
            else:
                self.set_fill_color(*WHITE)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 6, str(cell), border=0, fill=True, align="C")
            self.ln()
        self.ln(4)

    def bullet(self, text, indent=5):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        x = self.l_margin + indent
        self.set_x(x)
        w = self.w - x - self.r_margin - 6
        self.cell(6, 5.5, "- ")
        self.multi_cell(w, 5.5, text)

    def ensure_space(self, h):
        if self.get_y() + h > self.h - 20:
            self.add_page()


def build():
    pdf = ReportPDF("P", "mm", "A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*HEADING)
    pdf.cell(0, 15, "Season Plan Calculation", align="C")
    pdf.ln(18)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 8, "How Sapling calculates fertilizer recommendations", align="C")
    pdf.ln(6)
    pdf.cell(0, 8, "From soil analysis through to corrective action timelines", align="C")
    pdf.ln(20)

    # Overview
    pdf.section("Overview")
    pdf.body("The calculation pipeline has four layers, each building on the previous:")
    pdf.ln(2)
    steps = [
        ("1. Sufficiency Assessment", "What does the crop need? What does the soil already have?"),
        ("2. Ratio Adjustments", "Are nutrients in balance? Adjust within sufficiency constraints"),
        ("3. Pre-season Soil Treatment", "pH correction, Na displacement, organic matter"),
        ("4. Corrective Action Plan", "Long-term soil improvement timelines"),
    ]
    for step, desc in steps:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*HEADING)
        pdf.cell(5, 6, "")
        pdf.cell(55, 6, step)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 6, desc)
        pdf.ln(7)
    pdf.ln(6)

    # ── 1. Sufficiency ──
    pdf.add_page()
    pdf.section("1. Sufficiency Assessment")

    pdf.subsection("Step 1: Base Requirement")
    pdf.body("For each of the 12 nutrients (N, P, K, Ca, Mg, S, Fe, B, Mn, Zn, Mo, Cu):")
    pdf.code_block("base_req = per_unit_requirement x yield_target")
    pdf.body("Example: Maize N at 0.022 kg/kg x 8000 kg/ha yield = 176 kg N/ha")

    pdf.subsection("Step 2: Soil Classification")
    pdf.body("Each soil test value is classified against sufficiency thresholds:")
    pdf.table(
        ["Range", "Classification"],
        [
            ["0 to very_low_max", "Very Low"],
            ["very_low_max to low_max", "Low"],
            ["low_max to optimal_max", "Optimal"],
            ["optimal_max to high_max", "High"],
            ["above high_max", "Very High"],
        ],
        [95, 95],
    )

    pdf.subsection("Step 3: Adjustment Factor (Nutrient-Group-Specific)")
    pdf.body("The base requirement is multiplied by a factor from the adjustment_factors table. Factors are nutrient-group-specific:")
    pdf.ensure_space(50)
    pdf.table(
        ["Group", "Nutrients", "V.Low", "Low", "Opt", "High", "V.High", "Rationale"],
        [
            ["N", "N", "1.0", "1.0", "1.0", "1.0", "1.0", "Not bankable"],
            ["P", "P", "1.5", "1.25", "1.0", "0.75", "0.5", "Slow draw-down"],
            ["cations", "K,Ca,Mg,S", "1.5", "1.25", "1.0", "0.5", "0.25", "Standard"],
            ["micro", "Fe,B,Mn,etc", "1.0", "1.0", "1.0", "1.0", "1.0", "Tiny qty"],
        ],
        [22, 26, 16, 16, 16, 16, 16, 62],
    )
    pdf.code_block("target_kg_ha = base_req x factor")

    pdf.ensure_space(40)
    pdf.subsubsection("Why N is never reduced")
    pdf.body("Soil N tests do not reliably predict plant-available N during the growing season. N is mobile, transforms rapidly (mineralisation, nitrification, denitrification, leaching), and crops need it supplied fresh every season regardless of soil test levels.")

    pdf.subsubsection("Why P is conservative")
    pdf.body("P draws down very slowly in soil (2-4 mg/kg per year). Aggressive cuts would deny the crop P for many seasons while the soil test barely moves. A factor of 0.5 at Very High still supplies half the crop's need while allowing gradual draw-down.")

    # ── 2. Ratios ──
    pdf.add_page()
    pdf.section("2. Ratio Adjustments")
    pdf.body("After sufficiency targets are calculated, the engine checks nutrient ratios against ideal ranges. The approach is sufficiency-first:")

    pdf.subsection("Principles")
    pdf.bullet("Prefer reducing the over-supplied nutrient rather than increasing the deficient one")
    pdf.bullet("Never increase a nutrient already classified as High/Very High (except P:Zn)")
    pdf.bullet("Never reduce N - it's not bankable, always needs full supply")
    pdf.bullet("If neither action is possible, generate a warning for the agronomist")
    pdf.ln(4)

    pdf.subsection("Ratio Handlers")
    pdf.ensure_space(60)
    pdf.table(
        ["Ratio", "When Off", "Primary Action", "Fallback"],
        [
            ["Ca:Mg", "Below ideal", "Reduce Mg", "Increase Ca (if not High)"],
            ["Ca:Mg", "Above ideal", "Reduce Ca", "Increase Mg (if not High)"],
            ["Ca:K", "Below ideal", "Reduce K", "Increase Ca (if not High)"],
            ["Mg:K", "Below ideal", "Reduce K", "Increase Mg (if not High)"],
            ["P:Zn", "Above ideal", "Always boost Zn", "-"],
            ["N:S", "Above ideal", "Increase S", "Warn (never reduce N)"],
            ["K:Na", "Below ideal", "Always increase K", "- (Na displacement)"],
            ["Ca base sat.", "Below ideal", "Increase Ca", "Warn + suggest lime"],
            ["K base sat.", "Below ideal", "Increase K", "-"],
            ["Mg base sat.", "Below ideal", "Increase Mg", "-"],
        ],
        [28, 28, 67, 67],
    )

    pdf.subsubsection("Why P:Zn is an exception")
    pdf.body("High soil P physically blocks Zn uptake at the root level - it's a direct physiological antagonism, not just a ratio on paper. Even if soil Zn tests as 'sufficient,' the plant may not access it when P is very high. This is the one case where boosting the 'low' side of a ratio is justified regardless of sufficiency status.")

    pdf.subsubsection("Exact Calculations")
    pdf.body("Ratio adjustments calculate the exact kg/ha change needed to move the application ratio toward the ideal midpoint. All adjustments are capped (never reduce by more than 50%, never increase by more than 2x) to prevent extreme swings.")

    # ── 3. Pre-season ──
    pdf.add_page()
    pdf.section("3. Pre-season Soil Treatment")
    pdf.body("Three pre-season corrections are evaluated independently of the nutrient targets:")

    pdf.subsection("3a. Lime (pH Correction)")
    pdf.body("Trigger: pH (H2O) more than 0.2 units below target")
    pdf.table(
        ["Crop Type", "Target pH"],
        [
            ["Standard crops", "6.0"],
            ["Acid-loving (blueberry, tea, pineapple, rooibos)", "5.0"],
        ],
        [100, 90],
    )
    pdf.code_block("lime_t_ha = pH_deficit x buffer_factor")
    pdf.body("Buffer factor is based on clay %:")
    pdf.table(
        ["Clay %", "Buffer (t lime per pH unit)"],
        [
            ["<15% (sandy)", "1.5"],
            ["15-25% (sandy loam)", "2.5"],
            ["25-35% (loam)", "3.5"],
            ["35-45% (clay loam)", "4.5"],
            [">45% (clay)", "5.5"],
        ],
        [95, 95],
    )
    pdf.body("Additional +0.5 if organic carbon > 2% (higher buffer capacity).")
    pdf.body("Lime type: Dolomitic if Mg is also Low/Very Low (supplies Mg), Calcitic otherwise.")

    pdf.ensure_space(50)
    pdf.subsection("3b. Gypsum (Na Displacement)")
    pdf.body("Trigger: Na classification is High or Very High")
    pdf.code_block("gypsum_kg_ha = Na_excess x gypsum_factor\nwhere Na_excess = Na_mg_kg - 50 (target)\n      gypsum_factor = 4 + (clay% / 20)")
    pdf.body("Not recommended if calculated rate < 100 kg/ha (below practical threshold).")

    pdf.subsection("3c. Organic Carbon")
    pdf.body("Trigger: Org C classification is Low or Very Low")
    pdf.table(
        ["Classification", "Min compost % in blend", "Severity"],
        [
            ["Very Low", "60%", "Critical"],
            ["Low", "55%", "Important"],
        ],
        [63, 63, 64],
    )
    pdf.body("This is a flag for the blend optimizer to include compost, not a calculated rate.")

    # ── 4. Corrective ──
    pdf.add_page()
    pdf.section("4. Corrective Action Plan")
    pdf.body("A separate output from the season recommendation. Shows how long it will take to bring soil levels to optimal, given the current strategy.")

    pdf.subsection("Required Data")
    pdf.bullet("CEC (cmol/kg) - determines build-up efficiency")
    pdf.bullet("Clay % - already used for lime calculation")
    pdf.ln(2)
    pdf.body("If either is missing, the system shows: 'Soil correction plan unavailable - missing CEC, Clay from soil analysis.'")

    pdf.subsection("Build-up (nutrients below optimal)")
    pdf.body("Target: midpoint of optimal range")
    pdf.code_block("total_kg_needed = gap_mg_kg x buildup_factor\nseasons = ceil(total_kg_needed / max_per_season)\nannual_rate = total_kg_needed / seasons")

    pdf.body("Build-up factors (kg element per ha per 1 mg/kg soil test rise):")
    pdf.table(
        ["Nutrient", "Sandy (CEC <6)", "Medium (CEC 6-15)", "Clay (CEC >15)"],
        [
            ["P (Bray-1)", "5", "8", "15"],
            ["K", "2.5", "4", "6.5"],
            ["Ca", "7", "10", "16"],
            ["Mg", "2.5", "4", "6.5"],
        ],
        [48, 48, 48, 46],
    )

    pdf.body("Per-season caps (to prevent fixation losses and luxury consumption):")
    pdf.bullet("P: 50 kg/ha")
    pdf.bullet("K: 120 kg/ha")
    pdf.bullet("Ca: 200 kg/ha")
    pdf.bullet("Mg: 60 kg/ha")
    pdf.ln(3)

    pdf.subsection("Draw-down (nutrients above optimal)")
    pdf.body("Target: top of optimal range. No extra fertilizer needed - the reduced application rate allows crop removal to draw down the soil bank.")
    pdf.body("Approximate draw-down rates (mg/kg decline per season):")
    pdf.bullet("P: ~3 mg/kg/season (very slow - strongly buffered)")
    pdf.bullet("K: ~8 mg/kg/season (moderate)")
    pdf.bullet("Ca: ~5 mg/kg/season (moderate)")
    pdf.bullet("Mg: ~5 mg/kg/season (moderate)")
    pdf.ln(3)
    pdf.body("The correction plan tells the agronomist how long it will take for soil to reach optimal. The system calculates the timeline - the user doesn't choose it.")

    # ── Key Decisions ──
    pdf.add_page()
    pdf.section("Key Design Decisions")

    decisions = [
        ("Sufficiency drives the recommendation.", "Ratios are secondary flags, not prescriptive targets. Research (Kopittke & Menzies 2007, FSSA Handbook) shows correcting ratios when individual nutrients are sufficient produces no yield benefit."),
        ("N is sacred.", "Never reduced by any mechanism - sufficiency factors, ratio adjustments, or draw-down. Always supply full crop demand."),
        ("P is treated conservatively.", "Slow soil draw-down (years to decades) means aggressive cuts deny the crop without meaningfully improving soil levels."),
        ("The system decides timelines, not the user.", "Soil properties (CEC, clay, fixation capacity) and per-season caps determine how long correction takes. This removes guesswork and prevents agronomically unsound acceleration."),
        ("Missing data is flagged, not assumed.", "When CEC or Clay% is absent, the system says so rather than guessing - corrective plans require these parameters."),
    ]
    for i, (title, desc) in enumerate(decisions, 1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*HEADING)
        pdf.cell(8, 7, f"{i}.")
        pdf.cell(0, 7, title)
        pdf.ln(8)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK)
        pdf.set_x(pdf.l_margin + 8)
        pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 8, 5.5, desc)
        pdf.ln(4)

    # References
    pdf.ln(10)
    pdf.section("References")
    refs = [
        "Kopittke, P.M. & Menzies, N.W. (2007) A review of the use of the BCSR. Plant and Soil.",
        "FSSA Fertilizer Handbook (8th ed.) - Fertilizer Society of South Africa.",
        "Havlin, J.L. et al. Soil Fertility and Fertilizers (8th ed.).",
        "IPNI 4R Nutrient Stewardship Framework.",
        "ARC-Institute for Soil, Climate and Water - Technical Bulletins.",
        "Miles, N. & Manson, A.D. - SASRI Mg:K antagonism research.",
    ]
    for ref in refs:
        pdf.bullet(ref)

    out = "/Users/jalabuschagne/Documents/Projects/Blend Calculator/sapling-api/docs/Season_Plan_Calculation.pdf"
    pdf.output(out)
    print(f"PDF saved to: {out}")


if __name__ == "__main__":
    build()
