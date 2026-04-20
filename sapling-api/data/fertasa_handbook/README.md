# FERTASA Fertilizer Handbook — Chapter 5 (Fertilization)

Scraped 2026-04-20 from the interactive handbook at
<https://www.fertasastats.co.za/pages/fh_bh_index.php?lang=E> (paid
account required; login handled out-of-band with a session cookie).

## Why this lives in the repo

The FERTASA Fertilizer Handbook is **the** authoritative SA source for
fertilization guidelines. It covers every major SA crop by stage with
specific NPK/Ca/Mg/S rates, phenology windows, and cultivar-level
notes. Content is behind a paywall; the handbook is the primary data
bar the `feedback_fertasa_first.md` memory refers to.

An earlier scrape lived at `blend_app/data/fertasa_handbook/` and was
lost in commit `a0dd9be` when the legacy Streamlit app was removed.
This second scrape is committed so it doesn't get lost again.

## What's here

26 JSON files, one per chapter-5 leaf module:

| Section | File | Notes |
|---|---|---|
| 5.1 | `5_1_principles.json` | FERTASA threshold framework |
| 5.2 | `5_2_interpretation_soil.json` | Soil analysis interpretation |
| 5.3 | `5_3_leaf_analysis.json` | Leaf analysis norms |
| 5.4.1 | `5_4_1_barley.json` | **Cross-ref: refer to Wheat (5.4.3)** |
| 5.4.2 | `5_4_2_grain_sorghum.json` | **Cross-ref: refer to Maize (5.4.4)** |
| 5.4.3 | `5_4_3_wheat.json` | 12 tables, 97 rows — most detailed |
| 5.4.4 | `5_4_4_maize.json` | From the PDF linked on the site |
| 5.4.5 | `5_4_5_sweetcorn.json` | |
| 5.5.1 | `5_5_1_canola.json` | |
| 5.5.2 | `5_5_2_dry_beans.json` | |
| 5.5.3 | `5_5_3_groundnuts.json` | |
| 5.5.4 | `5_5_4_lentils.json` | SA IS covered (contrary to earlier research) |
| 5.5.5 | `5_5_5_soya_beans.json` | |
| 5.5.6 | `5_5_6_sunflower.json` | |
| 5.6.1 | `5_6_1_general_vegetables.json` | |
| 5.6.2 | `5_6_2_potatoes.json` | 12 tables, 65 rows |
| 5.6.3 | `5_6_3_asparagus.json` | SA IS covered (contrary to earlier research) |
| 5.6.4 | `5_6_4_tomatoes.json` | |
| 5.7.1 | `5_7_1_avocados.json` | SA-direct (no more Lovatt SH-conversion needed) |
| 5.7.2 | `5_7_2_bananas.json` | |
| 5.7.3 | `5_7_3_citrus.json` | SA-direct (no more Raath handbook paywall gap) |
| 5.8.1 | `5_8_1_macadamias.json` | |
| 5.8.2 | `5_8_2_pecan_nuts.json` | |
| 5.9 | `5_9_cotton.json` | |
| 5.11 | `5_11_tobacco.json` | |
| 5.12.2 | `5_12_2_lucerne.json` | |
| | `5_4_4_maize_OLD_GUIDELINES.pdf` | Original PDF retained |

## What's NOT covered by FERTASA

FERTASA does not include deciduous fruit (apple/pear/peach/etc),
grapes, berries, olives, rooibos, coffee, tea, pineapple, mango, guava,
fig, passion fruit, sweet potato, onion/garlic, cucurbits, lettuce/
spinach/cabbage/carrot, or peppers. For those, the previous research
(in the `research_growth_stages_*.md` memory files) stands.

## Record shape

```json
{
  "section": "5.8.1",
  "module_id": 364,
  "title": "Macadamias",
  "slug": "macadamias",
  "prose": "...full article text, tags stripped, whitespace normalised...",
  "tables": [[["Element", "Norm"], ["N", "1.2-1.6%"], ...], ...],
  "cross_ref": null,
  "source_url": "https://www.fertasastats.co.za/pages/fh_bh_reader.php?moduleID=364"
}
```

`tables` is a list of tables; each table is a list of rows; each row is
a list of cell text strings. Colspan/rowspan not expanded.

## Re-running the scraper

`scrape_fertasa.py` in this directory is the scraper. It reads
`session_cookie.txt` (Netscape cookie format, PHPSESSID only — not
committed) and rebuilds the JSON set. To refresh:

1. Log into <https://www.fertasastats.co.za/> in your browser
2. Copy the PHPSESSID cookie value
3. Write it to `/tmp/fertasa_scrape/session_cookie.txt` as a single
   Netscape-format line
4. Run `python3 scrape_fertasa.py` from that directory

The session cookie expires — if the script returns paywall-content
placeholder text, the cookie needs refreshing.

## Downstream use

- Updating `sapling-api/seeds/seed_growth_stages.sql` / migration 041
  with FERTASA-direct NPK stage splits (in progress).
- Reference source for the agronomist-facing notes column of
  `crop_growth_stages` rows (cite section number).
- Primary data bar for any future crop-specific code: check here first,
  fall back to international sources only when SA source absent.
