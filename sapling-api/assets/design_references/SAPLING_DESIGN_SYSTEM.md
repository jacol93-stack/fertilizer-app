# Sapling Programme PDF — design system specification

> **Source of truth** for the WeasyPrint template work (Task 55+). Every visual decision below is extracted from `clivia_garlic_WJ60421.pdf` (2026-04 reference, depth benchmark) and `allicro_karoo_2026-27.pdf` (2026-04-24 reference, closer-to-client). Both PDFs are committed alongside this doc in `assets/design_references/`.

---

## 1. Brand voice (typographic)

The programme reads like a precise technical document with editorial confidence. Two fingerprints:

- **Headlines end with a hard period.** "Background.", "Reading of the Soil.", "The Strategy.", "Items We're Carrying Into The Season." — this is the Sapling motif. Always render with the trailing period.
- **Numerical data uses a monospace face.** Application date strips ("Day 0 / Day 14 / Day 42"), week ranges ("Week 0", "Wks 3-7"), per-ha rates ("100 kg/ha", "~13 kg"), and ref numbers all set in monospace. This is the "code-style" treatment that signals "these numbers are precise, not approximate."

---

## 2. Colour palette

| Role | Hex (best estimate) | CSS variable | Notes |
|---|---|---|---|
| Primary background (cover) | `#1A1A1A` | `--ink` | Deep charcoal, not pure black. Used full-bleed on cover + as table-header / strip background |
| Body ink (interior) | `#1A1A1A` | `--ink` | Same colour, used as text on white |
| Page background | `#FFFFFF` | `--paper` | Pure white interiors |
| Primary accent | `#E55A30` | `--accent` | Burnt-orange / terracotta. Used for: section labels, headlines (selectively), bullet squares, table border accents, callout-box borders, status badges, left-edge callouts, "S" logo |
| Accent — softer (badges) | `#E89A6B` | `--accent-soft` | Tan/khaki. Used on badges with milder severity ("ELEVATED", "ABOVE OPTIMUM") to differentiate from full-orange ("LOW", "SODIC THRESHOLD") |
| Muted text (footers, sample meta) | `#6B6B6B` | `--muted` | Greys for less prominent metadata |
| Hairline rule | `#D8D8D8` | `--rule` | Thin horizontal dividers between sections |
| Success (✓ check marks) | `#2E7D5C` | `--ok` | Used in nutrient-balance "positive" rows |

The accent orange shifts slightly between charcoal-on-orange (cover, headline) and white-on-orange (badges). Both should reference the same `--accent` token; opacity/contrast does the visual work.

---

## 3. Typography

### Faces

The reference PDFs use what looks like a **modern grotesk family** for both display and body text, with a **monospace** face for tabular numerics. Best-fit free / open-source picks that match the visual feel:

| Role | Font | Weights used | Source |
|---|---|---|---|
| Display + body | **Inter** | 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 900 (black) | `https://rsms.me/inter/` — Open Font License, embeddable |
| Numerics / code-style | **JetBrains Mono** | 400, 500, 600 | `https://www.jetbrains.com/lp/mono/` — Open Font License |

If the user has a specific brand face (e.g. **Söhne**, **Neue Haas Grotesk**, **PP Neue Montreal**) those would be the higher-fidelity match — Inter is the closest free equivalent. Verify with the user before locking.

### Type scale

| Use | Size (pt) | Weight | Letter-spacing | Notes |
|---|---|---|---|---|
| Cover headline | 56 | 900 (black) | -0.02em | Multi-line, accent on the operative word ("Programme" in orange, others white) |
| Cover tagline | 18 | 400 italic | normal | "Fertilise Smarter, Grow Stronger." right-aligned |
| Cover body | 14 | 400 | normal | White on dark |
| Cover meta-table label | 9 | 500 | 0.08em | All-caps, orange |
| Cover meta-table value | 11 | 400 | normal | White |
| Cover footer | 9 | 500 | 0.08em | All-caps, white |
| Page header — wordmark | 13 | 600 | normal | "Sapling" next to icon |
| Page header — section locator | 9 | 500 | 0.10em | All-caps, muted, right-aligned. "04 · APPLICATIONS" |
| Section label ("SECTION 0X") | 9 | 500 | 0.10em | All-caps, accent-orange |
| Section headline | 28 | 700 | -0.01em | Trailing period. Black on white |
| Section sub (1.1, 2.1, 4.2 etc.) | 14 | 600 | normal | Black on white |
| Body text | 11 | 400 | normal | Black on white, line-height 1.55 |
| Body bold | 11 | 700 | normal | Used inline within paragraphs |
| Table header cell | 9 | 600 | 0.06em | All-caps, white on dark |
| Table body cell | 10 | 400 | normal | Black on white |
| Status badge | 8.5 | 700 | 0.08em | All-caps, white on accent |
| Code-style numerics | 10 | 400 | normal | JetBrains Mono. Used in date strips, week ranges, per-ha rates |
| Application strip headline | 11 | 600 | 0.06em | All-caps, white on dark, in strip bar |
| Application strip day | 10 | 400 | normal | Monospace white |
| Application strip annotation | 10 | 400 | normal | Monospace accent-orange (right-side of strip) |
| Footer | 9 | 400 | 0.06em | All-caps, muted |

---

## 4. Page layout

- **Page size:** A4 portrait (210 × 297 mm)
- **Margins (interior pages):**
  - Top: 22 mm (header bar lives here)
  - Bottom: 18 mm (footer)
  - Left: 22 mm
  - Right: 22 mm
- **Margins (cover):** 22 mm equivalent but full-bleed background. Title block sits at ~30 % from top.
- **Vertical rhythm:** 8 pt baseline. Section heading + 24 pt → body. Body paragraph spacing 12 pt.

### Page templates

#### (a) Cover

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                                          [S watermark]  │
│                                          ▢ subtle       │
│  ▬▬▬▬                                       30% opacity │
│                                                         │
│  Section title with                                     │
│  accent-coloured key word.        Fertilise Smarter,    │
│                                   Grow Stronger.        │
│                                       (italic, right)   │
│  Sub-paragraph (white)                                  │
│  describing scope.                                      │
│                                                         │
│  ─────────────────────                                  │
│  PREPARED BY  | Sapling Fertilizer                      │
│  SEASON       | 2026/27                                 │
│  REF          | FL60424                                 │
│  ─────────────────────                                  │
│                                                         │
│                                                         │
│                                                         │
│  ─────────────────────────────────────                 │
│  CLIENT FOOTER · BLOCKS    SAPLING · AGRICULTURAL      │
│                            ADVISORY                     │
└─────────────────────────────────────────────────────────┘
```

- Background: `--ink` (full bleed)
- Text: white
- Watermark: `--accent` "S" hex, 30 % opacity, top-right, ~50 % page-width
- Headline can highlight ONE word in `--accent` (e.g. "Programme" orange while "Fertilizer" + "2026/27" stay white). Selectable per programme — usually the noun that defines the document
- Meta table: 2-column, orange labels (small caps) left, white values right, hairline separator above + below
- Footer: small caps, white, separated from content by hairline rule

#### (b) Contents page

```
┌─────────────────────────────────────────────────────────┐
│  [S] Sapling                            CONTENTS        │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  CONTENTS                                               │
│  In this programme.                                     │
│                                                         │
│  01   Background . . . . . . . . . . . . . . . . p. 03  │
│  02   Reading of the Soil . . . . . . . . . . . . p. 04 │
│  03   The Strategy . . . . . . . . . . . . . . . p. 05  │
│  ...                                                    │
└─────────────────────────────────────────────────────────┘
```

- Section number: orange, monospace, 2-digit zero-padded
- Section title: black, regular weight, body size
- Page number: monospace right-aligned, "p. 03" style
- Dotted leader between title and page number is OPTIONAL — Allicro omits it; Clivia includes it

#### (c) Interior content page

```
┌─────────────────────────────────────────────────────────┐
│  [S] Sapling                       04 · APPLICATIONS    │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  SECTION 04                                             │
│  Applications.                                          │
│                                                         │
│  4.1 Planting (Tuesday)                                 │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ PLANTING · 10 ha + 4 ha     Day 0       Tuesday   │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Body paragraph text...                                 │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ON THE 4 HA ONLY — SIDE-DRESS                   │   │
│  │ Add 50 kg/ha of the 21 % N + 24 % S granule...  │   │
│  └─────────────────────────────────────────────────┘   │
│  (orange border callout)                                │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  INFO@SAPLINGFERTILIZER.COM                       03    │
└─────────────────────────────────────────────────────────┘
```

- Page header: hex "S" icon (~16 pt) + "Sapling" wordmark left, section locator right, hairline below
- Section banner: `SECTION 0X` orange small-caps + black headline with trailing period
- Sub-section heading: "4.1 Planting (Tuesday)" — sans-serif semibold
- Application strip: full-width row with `--ink` background, white headline left, monospace day middle, monospace accent-orange annotation right
- Callout box: orange border, orange small-caps headline at top, body text below
- Footer (optional): email left, monospace page number right (Clivia has this; Allicro omits)

---

## 5. Component library

### 5.1 Page header bar

```html
<header class="page-header">
  <div class="page-header__brand">
    <img class="page-header__logo" src="logo-icon.svg" alt="" />
    <span class="page-header__wordmark">Sapling</span>
  </div>
  <span class="page-header__locator">04 · APPLICATIONS</span>
</header>
<hr class="rule" />
```

CSS:
```css
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8mm;
}
.page-header__logo { height: 24px; }
.page-header__wordmark { font: 600 13pt Inter; margin-left: 6px; }
.page-header__locator {
  font: 500 9pt Inter;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--muted);
}
.rule { border: 0; border-top: 0.5pt solid var(--rule); margin-top: 4mm; }
```

### 5.2 Section headline

```html
<div class="section-banner">
  <span class="section-banner__label">SECTION 04</span>
  <h2 class="section-banner__title">Applications.</h2>
</div>
```

CSS:
```css
.section-banner__label {
  display: block;
  font: 500 9pt Inter;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 4mm;
}
.section-banner__title {
  font: 700 28pt Inter;
  line-height: 1.1;
  letter-spacing: -0.01em;
  margin: 0 0 6mm;
}
```

### 5.3 Application strip (the "Day 0 · Tuesday" bar)

```html
<div class="app-strip">
  <span class="app-strip__title">PLANTING · 10 ha + 4 ha (starter already down)</span>
  <span class="app-strip__day">Day 0</span>
  <span class="app-strip__date">Tuesday</span>
</div>
```

CSS:
```css
.app-strip {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 12mm;
  background: var(--ink);
  color: white;
  padding: 4mm 6mm;
  margin-bottom: 4mm;
}
.app-strip__title {
  font: 600 11pt Inter;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.app-strip__day,
.app-strip__date {
  font: 400 10pt 'JetBrains Mono';
}
.app-strip__date { color: var(--accent); }
```

### 5.4 Status badge

```html
<span class="status status--alert">SODIC THRESHOLD</span>
<span class="status status--soft">ELEVATED</span>
<span class="status status--ok">IDEAL — NO INTERVENTION</span>
```

CSS:
```css
.status {
  display: inline-block;
  padding: 1.5mm 3mm;
  font: 700 8.5pt Inter;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: white;
}
.status--alert { background: var(--accent); }
.status--soft { background: var(--accent-soft); }
.status--ok { background: transparent; color: var(--ok); border: 0.5pt solid var(--ok); }
```

### 5.5 Callout box (orange border)

```html
<aside class="callout">
  <span class="callout__label">PROGRAMME AT A GLANCE</span>
  <ul class="callout__list">
    <li>14 ha under centre-pivot irrigation across the Kraan and Gamka blocks</li>
    ...
  </ul>
</aside>
```

CSS:
```css
.callout {
  border: 1pt solid var(--accent);
  padding: 4mm 5mm;
  margin: 4mm 0;
}
.callout__label {
  display: block;
  font: 500 9pt Inter;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 2mm;
}
.callout__list { list-style: none; padding: 0; margin: 0; }
.callout__list li::before {
  content: "▪";
  color: var(--accent);
  margin-right: 2mm;
}
```

### 5.6 Data table

```html
<table class="data-table">
  <thead>
    <tr><th>Parameter</th><th>Reading</th><th>Target</th><th>Status</th></tr>
  </thead>
  <tbody>
    <tr><td>Phosphorus (Olsen)</td><td>Low</td><td>Moderate-High</td>
        <td><span class="status status--alert">LOW</span></td></tr>
    ...
  </tbody>
</table>
```

CSS:
```css
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 10pt;
}
.data-table thead {
  background: var(--ink);
  color: white;
}
.data-table th {
  font: 600 9pt Inter;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  text-align: left;
  padding: 3mm 4mm;
}
.data-table td {
  padding: 3mm 4mm;
  border-bottom: 0.5pt solid var(--rule);
}
```

### 5.7 Three-signals callout (left-edge orange bar)

```html
<div class="signal">
  <h4 class="signal__head">Sodium is the biggest long-term soil-health concern.</h4>
  <p>Gamka at 14.7 % base saturation sits right at the sodic threshold...</p>
</div>
```

CSS:
```css
.signal {
  border-left: 2pt solid var(--accent);
  padding: 1mm 0 1mm 5mm;
  margin: 4mm 0;
}
.signal__head {
  font: 700 11pt Inter;
  margin: 0 0 1mm;
}
```

### 5.8 Year / phase card (Year 2 and Beyond pattern)

```html
<div class="year-card">
  <span class="year-card__label">YEAR 1</span>
  <span class="year-card__title">Establishment</span>
  <ul class="year-card__list">
    <li>Cereals cut August — roughly 5 tons of mixed hay per hectare.</li>
    ...
  </ul>
</div>
```

CSS:
```css
.year-card {
  border: 1pt solid var(--ink);
  padding: 4mm 5mm;
  margin: 3mm 0;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0 6mm;
}
.year-card__label {
  font: 500 9pt Inter;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--accent);
  grid-column: 1;
}
.year-card__title {
  font: 600 12pt Inter;
  text-align: right;
  grid-column: 2;
}
.year-card__list {
  grid-column: 1 / -1;
  list-style: none;
  padding: 2mm 0 0;
  margin: 0;
}
.year-card__list li::before { content: "▪"; color: var(--accent); margin-right: 2mm; }
```

---

## 6. Brand assets

Existing logo files in `sapling-api/assets/`:

- `logo.png` — full lockup with slogan
- `logo_no_slogan.png` — wordmark + icon, no tagline
- `logo_no_slogan_transparent.png` — same on transparent
- `logo_icon_only.png` — just the hex "S"

For the PDF template:
- Cover watermark + interior page-header → `logo_icon_only.png` (or SVG export)
- Cover headline area uses LARGE icon-only at high opacity in Clivia, watermark-style at 30 % opacity in Allicro
- Interior page header uses small icon (24 px) + "Sapling" wordmark text rendered in CSS (not from the logo file — so the colour can match `--ink` consistently)

**Recommendation:** export an SVG version of the icon for crisp rendering at any size. PDF embedding handles SVG well.

---

## 7. Variations between Clivia and Allicro

| Element | Clivia | Allicro | Choose |
|---|---|---|---|
| Cover logo | Full hex "S" top-right, prominent | Subtle watermark, ~30 % opacity, larger | **Allicro pattern** — calmer, more confident |
| Cover headline accent | One word in orange (e.g. "Fertigation") | One word in orange (e.g. "Programme") | Same — make `--accent-word` configurable per programme |
| Interior header | Logo + tagline + section locator | Logo (no tagline) + section locator | **Allicro** — cleaner; tagline is on cover only |
| Footer | Email left + page number right | None | **Clivia** — page numbers are useful; email reinforces brand |
| Section subnumbering | "1.1 Programme shape at a glance" | "4.1 Planting (Tuesday)" | Both use it — keep |
| Headline period motif | Yes ("Garlic Fertigation Programme.") | Yes ("Fertilizer Programme 2026/27.") | Always |

**Picked combination:** Allicro's cover (subtle watermark) + Allicro's interior header (no tagline) + Clivia's footer (email + page number) + headline-period everywhere.

---

## 8. Implementation notes for WeasyPrint

- WeasyPrint supports `@page` directives for per-page layout — define separate page templates for cover, contents, interior with `@page :first` / `@page contents` / `@page interior`.
- `@font-face` works cleanly with .woff2 — embed Inter + JetBrains Mono.
- `position: running()` lets you place a header/footer once and have it repeat on every page — set the section locator dynamically per page using `string-set`.
- Status badges, callouts, year-cards all render fine with simple CSS.
- One known WeasyPrint limit: complex flex layouts in nested grids can be brittle. Keep components flat where possible.
- Page break behaviour: use `break-inside: avoid` on cards and tables; `break-before: page` on each section's `<section>` element.

---

## 9. What this design does NOT include

Per `feedback_client_disclosure_boundary` memory:

- **No FERTASA / SAMAC / Schoeman / CRI / source citations** anywhere in the visible doc.
- **No raw material names** — products referenced by analysis ("21 % N + 24 % S granule") or Sapling product names ("Rescue + Gypsum pellet").
- **No factory procedures, QC checks, SOPs, batch IDs, mixing instructions** — those are operator-mode only.

The renderer's `_strip_source_refs()` sanitiser already enforces the source-citation rule on every prose field. The WeasyPrint template inherits that — it just renders what the sanitised markdown emits.

---

## 10. Locked decisions (2026-04-25)

1. **Typography stack** — Inter + JetBrains Mono. Both Open Font License, embedded via `@font-face`. ✅
2. **Accent orange** — `#E55A30` (visual best-estimate, no specific brand hex provided). ✅
3. **Footer** — Clivia-style: `info@saplingfertilizer.com` left + monospace page number right. ✅
4. **Email footer** — `info@saplingfertilizer.com` confirmed. ✅
5. **Cover headline pattern** — **standardised, auto-derived from artifact**, no user editing:
   - Pattern: `{Crop} Fertilizer Programme {Season}.`
   - Examples:
     - Macadamia · 2026/27 → **Macadamia Fertilizer** *Programme* **2026/27.**
     - Citrus (Valencia) · 2026/27 → **Citrus (Valencia) Fertilizer** *Programme* **2026/27.**
   - Accent word: always **"Programme"** (matches Allicro reference, the most recent stylesheet).
   - Source: `header.crop` + `header.season` from ProgrammeArtifact. No template variable for an "accent word override" — the rule is fixed.
   - ✅
