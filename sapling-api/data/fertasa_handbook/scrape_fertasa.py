#!/usr/bin/env python3
"""Scrape FERTASA Fertilizer Handbook chapter 5 using the user's
authenticated PHPSESSID cookie.

Writes one JSON per crop into `json/` (next to this file) with shape:

    {
      "section": "5.4.4",
      "module_id": 345,
      "title": "Maize",
      "slug": "maize",
      "prose": "...full article text (tags stripped)...",
      "tables": [[[col, col, ...], [cell, cell, ...], ...], ...],
      "image_tables": [
        {"id": "466", "url": "fhimg/466.jpg", "local_path": "images/466.jpg"},
        ...
      ],
      "cross_ref": null | "Wheat"
    }

Many FERTASA tables (leaf norms in 5.3, rate tables in wheat/canola, the
sunflower/potato/cotton/avocado/lucerne tables) are rendered as JPEGs,
not HTML. Earlier scrapes missed them. This version downloads each JPG
into `images/` so downstream consumers can transcribe with OCR/vision.

Run from `sapling-api/data/fertasa_handbook/`:
    python3 scrape_fertasa.py
Input:
    session_cookie.txt (Netscape format, single PHPSESSID line — NOT committed)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
COOKIE = HERE / 'session_cookie.txt'
OUT = HERE                   # write JSON files directly into the handbook dir
IMG_DIR = HERE / 'images'
IMG_DIR.mkdir(exist_ok=True)

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit('BeautifulSoup required: pip install beautifulsoup4')

MODULES = [
    ('5.1',   335, 'principles',            'Fertilizer guidelines — principles'),
    ('5.2',   336, 'interpretation_soil',   'Interpretation of soil analysis'),
    ('5.3',   337, 'leaf_analysis',         'Leaf analysis'),
    ('5.4.1', 339, 'barley',                'Barley'),
    ('5.4.2', 340, 'grain_sorghum',         'Grain sorghum'),
    ('5.4.3', 341, 'wheat',                 'Wheat'),
    ('5.4.4', 345, 'maize',                 'Maize'),
    ('5.4.5', 346, 'sweetcorn',             'Sweetcorn'),
    ('5.5.1', 348, 'canola',                'Canola'),
    ('5.5.2', 349, 'dry_beans',             'Dry beans'),
    ('5.5.3', 350, 'groundnuts',            'Groundnuts'),
    ('5.5.4', 351, 'lentils',               'Lentils'),
    ('5.5.5', 352, 'soya_beans',            'Soya beans'),
    ('5.5.6', 353, 'sunflower',             'Sunflower'),
    ('5.6.1', 355, 'general_vegetables',    'General vegetable crops'),
    ('5.6.2', 356, 'potatoes',              'Potatoes'),
    ('5.6.3', 357, 'asparagus',             'Asparagus'),
    ('5.6.4', 358, 'tomatoes',              'Tomatoes'),
    ('5.7.1', 360, 'avocados',              'Avocados'),
    ('5.7.2', 361, 'bananas',               'Bananas'),
    ('5.7.3', 362, 'citrus',                'Citrus'),
    ('5.8.1', 364, 'macadamias',            'Macadamias'),
    ('5.8.2', 365, 'pecan_nuts',            'Pecan nuts'),
    ('5.9',   366, 'cotton',                'Cotton'),
    ('5.11',  368, 'tobacco',               'Tobacco'),
    ('5.12.2', 371, 'lucerne',              'Lucerne'),
]


def fetch(module_id: int) -> str:
    r = subprocess.run(
        ['curl', '-s', '-b', str(COOKIE), '-A', 'Mozilla/5.0',
         f'https://www.fertasastats.co.za/pages/fh_bh_reader.php?moduleID={module_id}'],
        capture_output=True, text=True, check=True,
    )
    return r.stdout


def download_image(img_id: str) -> Path | None:
    """Download fhimg/<id>.jpg into IMG_DIR. Idempotent; skips existing."""
    dest = IMG_DIR / f'{img_id}.jpg'
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    url = f'https://www.fertasastats.co.za/pages/fhimg/{img_id}.jpg'
    r = subprocess.run(
        ['curl', '-s', '-b', str(COOKIE), '-A', 'Mozilla/5.0',
         '-o', str(dest), '-w', '%{http_code}', url],
        capture_output=True, text=True,
    )
    if r.stdout.strip() != '200' or not dest.exists() or dest.stat().st_size == 0:
        if dest.exists():
            dest.unlink()
        return None
    return dest


def extract_panel(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.select_one('div.panel-body')
    if body is None:
        return soup
    for a in body.find_all('a'):
        txt = a.get_text(' ', strip=True).lower()
        if 'previous' in txt or 'next' in txt or 'back to index' in txt:
            a.decompose()
    return body


def parse_tables(panel: BeautifulSoup) -> list[list[list[str]]]:
    out = []
    for tbl in panel.find_all('table'):
        rows = []
        for tr in tbl.find_all('tr'):
            cells = [
                c.get_text(' ', strip=True)
                for c in tr.find_all(['th', 'td'])
            ]
            if cells:
                rows.append(cells)
        if rows:
            out.append(rows)
    return out


def extract_image_refs(panel: BeautifulSoup) -> list[dict]:
    """Find every `fhimg/<n>.jpg` inside the panel. Download each into
    IMG_DIR and record id + url + local_path."""
    refs: list[dict] = []
    seen: set[str] = set()
    for img in panel.find_all('img'):
        src = img.get('src', '')
        m = re.search(r'fhimg/(\d+)\.jpg', src)
        if not m:
            continue
        img_id = m.group(1)
        if img_id in seen:
            continue
        seen.add(img_id)
        local = download_image(img_id)
        refs.append({
            'id': img_id,
            'url': f'fhimg/{img_id}.jpg',
            'local_path': f'images/{img_id}.jpg' if local else None,
            'alt': img.get('alt', ''),
        })
    return refs


def parse_prose(panel: BeautifulSoup) -> str:
    p = BeautifulSoup(str(panel), 'html.parser')
    for tbl in p.find_all('table'):
        tbl.decompose()
    text = p.get_text(' ', strip=True)
    return re.sub(r'\s+', ' ', text).strip()


CROSS_REF_RE = re.compile(
    r'Refer\s+([A-Z][A-Za-z ]+?)\s+Guidelines?\s*\(?(?:5\.[\d.]+)?',
    re.IGNORECASE,
)


def main() -> int:
    if not COOKIE.exists():
        sys.exit(f'Missing {COOKIE} — write Netscape cookie line first.')

    total_imgs = 0
    for section, mid, slug, title in MODULES:
        html = fetch(mid)
        panel = extract_panel(html)
        tables = parse_tables(panel)
        image_refs = extract_image_refs(panel)
        prose = parse_prose(panel)

        cross_ref = None
        if len(prose) < 200:
            m = CROSS_REF_RE.search(prose)
            if m:
                cross_ref = m.group(1).strip()

        record = {
            'section': section,
            'module_id': mid,
            'title': title,
            'slug': slug,
            'prose': prose,
            'tables': tables,
            'image_tables': image_refs,
            'cross_ref': cross_ref,
            'source_url': f'https://www.fertasastats.co.za/pages/fh_bh_reader.php?moduleID={mid}',
        }
        out_path = OUT / f'{section.replace(".", "_")}_{slug}.json'
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False))

        tcount = len(tables)
        rcount = sum(len(t) for t in tables)
        icount = len(image_refs)
        total_imgs += icount
        if cross_ref:
            status = f'cross-ref → {cross_ref}'
        else:
            status = f'{tcount} text-tables / {rcount} rows / {icount} image-tables'
        print(f'  {section:<7} {slug:<25} {status}')

    print(f'\nWrote {len(MODULES)} JSON files to {OUT}')
    print(f'Downloaded {total_imgs} image-tables into {IMG_DIR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
