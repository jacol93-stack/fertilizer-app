"""Apply migration 037 via the supabase-py table API.

supabase-py doesn't accept raw SQL, so this script replicates the
operations in 037_programme_builder_data_integrity.sql as a sequence
of table-API calls. Idempotent — safe to re-run.

Usage:
    venv/bin/python migrations/apply_037.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running from sapling-api/ root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.supabase_client import get_supabase_admin


ANNUAL_CROPS = [
    'Butternut', 'Canola', 'Dry Beans', 'Garlic', 'Green Beans',
    'Lentils', 'Lettuce', 'Maize (dryland)', 'Maize (irrigated)',
    'Pepper (Bell)', 'Potato', 'Pumpkin', 'Spinach', 'Strawberry',
    'Sweetcorn', 'Watermelon',
]

STAGE_ALIASES = [
    ('Citrus (Grapefruit)',  'Citrus (Valencia)'),
    ('Citrus (Lemon)',       'Citrus (Valencia)'),
    ('Citrus (Navel)',       'Citrus (Valencia)'),
    ('Citrus (Soft Citrus)', 'Citrus (Valencia)'),
    ('Maize (dryland)',      'Maize'),
    ('Maize (irrigated)',    'Maize'),
    ('Sweetcorn',            'Maize'),
    ('Table Grape',          'Grape (Table)'),
    ('Wine Grape',           'Grape (Wine)'),
    ('Peach/Nectarine',      'Peach'),
    ('Lucerne/Alfalfa',      'Lucerne'),
    ('Dry Beans',            'Bean (Dry)'),
    ('Green Beans',          'Bean (Green)'),
    ('Potato',               'Potatoes'),
]

CITRUS_SUBTYPES = [
    'Citrus (Grapefruit)', 'Citrus (Lemon)',
    'Citrus (Navel)', 'Citrus (Soft Citrus)',
]

# (crop, label, age_min, age_max, n, p, k, general, notes)
NEW_AGE_FACTORS = [
    # Pome fruit — full bearing year 7
    ('Apple',  'Year 1-2',  0, 1, 0.20, 0.25, 0.15, 0.20, 'Establishment; minimal nutrition'),
    ('Apple',  'Year 3-4',  2, 3, 0.40, 0.45, 0.35, 0.40, 'Frame development'),
    ('Apple',  'Year 5-6',  4, 5, 0.65, 0.65, 0.60, 0.65, 'First bearing'),
    ('Apple',  'Year 7',    6, 6, 0.85, 0.85, 0.80, 0.85, 'Pre-mature bearing'),
    ('Apple',  'Year 8+',   7, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    ('Pear',   'Year 1-2',  0, 1, 0.20, 0.25, 0.15, 0.20, 'Establishment'),
    ('Pear',   'Year 3-4',  2, 3, 0.40, 0.45, 0.35, 0.40, 'Frame development'),
    ('Pear',   'Year 5-6',  4, 5, 0.65, 0.65, 0.60, 0.65, 'First bearing'),
    ('Pear',   'Year 7',    6, 6, 0.85, 0.85, 0.80, 0.85, 'Pre-mature bearing'),
    ('Pear',   'Year 8+',   7, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    # Stone fruit — full bearing year 5
    ('Peach/Nectarine', 'Year 1-2', 0, 1, 0.25, 0.30, 0.20, 0.25, 'Establishment'),
    ('Peach/Nectarine', 'Year 3-4', 2, 3, 0.55, 0.60, 0.50, 0.55, 'Early bearing'),
    ('Peach/Nectarine', 'Year 5',   4, 4, 0.80, 0.80, 0.75, 0.80, 'Pre-mature bearing'),
    ('Peach/Nectarine', 'Year 6+',  5, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    ('Apricot', 'Year 1-2', 0, 1, 0.25, 0.30, 0.20, 0.25, 'Establishment'),
    ('Apricot', 'Year 3-4', 2, 3, 0.55, 0.60, 0.50, 0.55, 'Early bearing'),
    ('Apricot', 'Year 5',   4, 4, 0.80, 0.80, 0.75, 0.80, 'Pre-mature bearing'),
    ('Apricot', 'Year 6+',  5, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    ('Plum', 'Year 1-2', 0, 1, 0.25, 0.30, 0.20, 0.25, 'Establishment'),
    ('Plum', 'Year 3-4', 2, 3, 0.55, 0.60, 0.50, 0.55, 'Early bearing'),
    ('Plum', 'Year 5',   4, 4, 0.80, 0.80, 0.75, 0.80, 'Pre-mature bearing'),
    ('Plum', 'Year 6+',  5, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    # Grape — full bearing year 3
    ('Table Grape', 'Year 1', 0, 0, 0.10, 0.20, 0.10, 0.10, 'Establishment'),
    ('Table Grape', 'Year 2', 1, 1, 0.35, 0.40, 0.30, 0.35, 'Canopy development'),
    ('Table Grape', 'Year 3', 2, 2, 0.65, 0.65, 0.60, 0.65, 'First bearing'),
    ('Table Grape', 'Year 4+', 3, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    ('Wine Grape', 'Year 1', 0, 0, 0.10, 0.20, 0.10, 0.10, 'Establishment'),
    ('Wine Grape', 'Year 2', 1, 1, 0.35, 0.40, 0.30, 0.35, 'Canopy development'),
    ('Wine Grape', 'Year 3', 2, 2, 0.65, 0.65, 0.60, 0.65, 'First bearing'),
    ('Wine Grape', 'Year 4+', 3, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    # Olive — full bearing year 9
    ('Olive', 'Year 1-3', 0, 2, 0.25, 0.30, 0.20, 0.25, 'Establishment'),
    ('Olive', 'Year 4-6', 3, 5, 0.55, 0.60, 0.50, 0.55, 'Early bearing'),
    ('Olive', 'Year 7-9', 6, 8, 0.80, 0.80, 0.75, 0.80, 'Pre-mature bearing'),
    ('Olive', 'Year 10+', 9, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
    # Blueberry — full bearing year 3
    ('Blueberry', 'Year 1', 0, 0, 0.30, 0.35, 0.25, 0.30, 'Establishment'),
    ('Blueberry', 'Year 2', 1, 1, 0.60, 0.65, 0.55, 0.60, 'Early bearing'),
    ('Blueberry', 'Year 3+', 2, 99, 1.00, 1.00, 1.00, 1.00, 'Full bearing'),
]


def step_1_fix_crop_type(sb):
    print('\n[1/4] Fixing crop_type misclassification...')
    n = 0
    for crop in ANNUAL_CROPS:
        r = sb.table('crop_requirements').update({'crop_type': 'annual'}).eq('crop', crop).execute()
        if r.data:
            n += len(r.data)
    print(f'  updated {n} rows to annual')


def step_2_alias_stages(sb):
    print('\n[2/4] Adding alias rows to crop_growth_stages...')
    added = 0
    skipped = 0
    for target, source in STAGE_ALIASES:
        existing = sb.table('crop_growth_stages').select('id', count='exact').eq('crop', target).execute()
        if existing.count and existing.count > 0:
            print(f'  skip {target} (already has {existing.count} rows)')
            skipped += 1
            continue
        src_rows = sb.table('crop_growth_stages').select('*').eq('crop', source).execute().data
        if not src_rows:
            print(f'  skip {target}: source {source!r} has no rows')
            continue
        to_insert = []
        for row in src_rows:
            new_row = {k: v for k, v in row.items() if k not in ('id', 'created_at', 'updated_at')}
            new_row['crop'] = target
            existing_notes = new_row.get('notes') or ''
            prefix = ' ' if existing_notes else ''
            new_row['notes'] = f'{existing_notes}{prefix}[aliased from {source}]'
            to_insert.append(new_row)
        sb.table('crop_growth_stages').insert(to_insert).execute()
        print(f'  {target} ← {source}: inserted {len(to_insert)} rows')
        added += len(to_insert)
    print(f'  total: {added} rows added, {skipped} aliases skipped (existed)')


def step_3_age_factors(sb):
    print('\n[3/4] Expanding perennial_age_factors...')
    # Citrus subtypes: clone from Valencia
    valencia = sb.table('perennial_age_factors').select('*').eq('crop', 'Citrus (Valencia)').execute().data
    for sub in CITRUS_SUBTYPES:
        existing = sb.table('perennial_age_factors').select('id', count='exact').eq('crop', sub).execute()
        if existing.count and existing.count > 0:
            print(f'  skip {sub} (already has {existing.count} rows)')
            continue
        to_insert = []
        for row in valencia:
            new_row = {k: v for k, v in row.items() if k not in ('id', 'created_at', 'updated_at')}
            new_row['crop'] = sub
            to_insert.append(new_row)
        if to_insert:
            sb.table('perennial_age_factors').insert(to_insert).execute()
            print(f'  {sub}: {len(to_insert)} rows')

    # New curves
    by_crop: dict[str, list[dict]] = {}
    for crop, label, lo, hi, n, p, k, gen, notes in NEW_AGE_FACTORS:
        by_crop.setdefault(crop, []).append({
            'crop': crop, 'age_label': label,
            'age_min': lo, 'age_max': hi,
            'n_factor': n, 'p_factor': p, 'k_factor': k,
            'general_factor': gen,
            'notes': notes,
        })
    for crop, rows in by_crop.items():
        existing = sb.table('perennial_age_factors').select('id', count='exact').eq('crop', crop).execute()
        if existing.count and existing.count > 0:
            print(f'  skip {crop} (already has {existing.count} rows)')
            continue
        sb.table('perennial_age_factors').insert(rows).execute()
        print(f'  {crop}: {len(rows)} rows')


def step_4_backfill_block_targets(sb):
    print('\n[4/4] Backfilling programme_blocks.nutrient_targets...')
    blocks = sb.table('programme_blocks').select('id, soil_analysis_id, nutrient_targets').execute().data
    candidates = [
        b for b in blocks
        if b.get('soil_analysis_id')
        and not (isinstance(b.get('nutrient_targets'), list) and b['nutrient_targets'])
    ]
    print(f'  {len(candidates)} blocks with soil_analysis_id and empty target cache')
    updated = 0
    for block in candidates:
        sa = sb.table('soil_analyses').select('nutrient_targets').eq('id', block['soil_analysis_id']).limit(1).execute().data
        if not sa:
            continue
        targets = sa[0].get('nutrient_targets')
        if isinstance(targets, list) and targets:
            sb.table('programme_blocks').update({'nutrient_targets': targets}).eq('id', block['id']).execute()
            updated += 1
    print(f'  backfilled {updated} blocks')


def main():
    sb = get_supabase_admin()
    step_1_fix_crop_type(sb)
    step_2_alias_stages(sb)
    step_3_age_factors(sb)
    step_4_backfill_block_targets(sb)
    print('\ndone.')


if __name__ == '__main__':
    main()
