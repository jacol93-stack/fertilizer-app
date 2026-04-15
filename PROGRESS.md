# Sapling upgrade — progress notes

Running log of everything Claude did while you were asleep, top of the
pile first. Read the top 3 sections when you check in; the rest is
reference.

## TL;DR for the morning

- **154 tests passing** (was 59 last check-in). Full engine safety net in
  place: soil, optimizer, feeding, notation, comparison, soil_corrections,
  foliar, rate_limit.
- **Workbench dashboard is live** — new `/api/workbench/workbench` endpoint
  and a replacement `sapling-web/src/app/page.tsx`. Single round-trip,
  "what needs my attention today" focus. Try it after restarting the API.
- **Rate limiting is wired** via a path-classifying middleware (no per-router
  decorations). Tiered: engine / list / admin / ai / session / default.
  Sporadic-but-intense workload as you asked for.
- **Migrations 032–035 applied successfully by you.** Backend picks them up
  on next restart (soft-delete columns, 18 indexes, RLS policies on 11
  bare tables, impersonation_sessions table).
- **Big untracked-code pile in `sapling-api/app/`** is still not committed.
  My changes are all on top of it. Commit your backend code + my changes
  together when you're ready; they're one coherent piece.

## How to verify it's working

```bash
# Backend
cd sapling-api
venv/bin/python -m pytest tests/        # expect 154 passed
venv/bin/python -m uvicorn app.main:app --reload --port 8000
# Then hit http://localhost:8000/api/health in a browser — should be {"status":"ok","database":"ok",...}

# Frontend
cd sapling-web
npx tsc --noEmit --skipLibCheck         # clean compile
npm run dev
# http://localhost:3000 — you'll land on the new workbench
```

## Things that need your call before I can do more

1. **Pagination envelope rollout (task #14).** `app/pagination.py` helper
   exists. Wiring it through the list endpoints changes response shape
   (from `[...]` to `{items, total, skip, limit}`) which requires a matching
   frontend change. Tell me "go" and I'll land both sides in one pass.
2. **Workbench column assumptions.** I built the dashboard against the
   column names I could verify in the router code. If any card is empty
   when it shouldn't be, check the backend logs for `workbench.<section>
   failed` — each section is wrapped in try/except so one bad column
   can't take down the page.
3. **Workflow next steps.** Dashboard is v1. The audit listed many other
   flow pains (client drill-down, lab PDF extract, season planning,
   records filtering, wizard state persistence). Pick which one hurts
   next and I'll run at it.
4. **Calc bug fixes.** I have golden tests locking in current (buggy)
   behavior for ~8 audit-flagged bugs (classification boundary inclusive,
   CEC-missing silently skipping base sat, optimizer `None` return,
   age-beyond-table rolling to 1.0, notation denom cap, clay buffer
   off-by-one, foliar 30 kg cap, 50% coverage threshold). Each fix
   updates its test as a deliberate act. Want me to start fixing?

---

## What's on disk right now (unstaged, on top of your untracked pile)

### New / modified tests — `sapling-api/tests/`

All 154 pass. Tests intentionally encode audit-flagged quirks so future
fixes have a target to push back on.

| File | Tests | Covers |
|------|-------|--------|
| `test_soil_engine.py` | 29 | classify, targets, ratio adjustment, base saturation |
| `test_optimizer.py` | 9 | run_optimizer, find_closest_blend, priority optimizer |
| `test_feeding_engine.py` | 21 | growth stages, age factors, practical plan, methods |
| `test_notation.py` | 16 | SA notation ↔ percent conversion, secondary nutrients |
| `test_comparison_engine.py` | 18 | class index, crop impact, recommendations |
| `test_soil_corrections.py` | 26 | lime, gypsum, organic carbon, nutrient explanations |
| `test_foliar_engine.py` | 15 | product scoring, coverage, rate capping |
| `test_rate_limit.py` | 20 | tier classification, sliding-window counter |

Run: `cd sapling-api && venv/bin/python -m pytest tests/ -v`

### New migrations — `sapling-api/migrations/`

| File | Status | Purpose |
|------|--------|---------|
| `032_soft_delete_consistency.sql` | ✅ applied | `deleted_at` + `deleted_by` on blends/soil_analyses/feeding_plans/quotes; backfill `deleted_by` on programmes/leaf_analyses |
| `033_performance_indexes.sql` | ✅ applied | 18 missing indexes on agent_id / client_id / created_at / deleted_at partials |
| `034_rls_policies.sql` | ✅ applied | RLS policies for 11 tables 031 left bare; `public.is_admin()` helper. `material_markups` treated as global (not per-agent — your correction) |
| `035_impersonation_sessions.sql` | ✅ applied | Durable `impersonation_sessions` table; replaces in-memory dict |

### Code changes — `sapling-api/app/`

- **`routers/admin.py`** — `/activity` endpoint: fixed dead `.neq("role","admin")`
  filter (column didn't exist), wrong `saved_blends` table name (→ `blends`),
  wrong `crop_name` column (→ `crop`). Excludes soft-deleted rows. `limit`
  query param. Also upgraded the audit_log silent except.

- **`routers/workbench.py`** (NEW) — `/api/workbench/workbench` endpoint.
  Single round-trip returning stats, 4 attention sections, recent activity,
  onboarding flag. Each section wrapped in try/except with named fallback
  so a broken column can't cascade.

- **`main.py`** —
  1. `/api/health` now probes the database and returns 503 on failure
  2. Stdlib-only JSON log formatter wired onto root logger; honors `$LOG_LEVEL`
  3. `rate_limit_middleware` registered (path-classifying tiered limiter)
  4. Request-logging middleware: correlation IDs, `request.start` / `request.finish`
     structured records with duration_ms / status / method / path
  5. Workbench router mounted at `/api/workbench`

- **`auth.py`** — impersonation sessions moved from in-memory dict to
  `impersonation_sessions` table. Timeout 60 → **15 min**. Captures IP +
  user agent. Expired sessions flip to `ended_at` with reason `"expired"`.
  Falls back to in-memory dict if migration 035 isn't applied (it is now).

- **`rate_limit.py`** — rewritten. Path-classifying middleware with
  tiered rules:
  - `engine` 30/sec; 300/min (POST/PUT on blend optimize, soil classify/targets/compare/corrections, feeding generate/practical, foliar/liquid/leaf diagnose, programmes generate)
  - `list` 60/sec; 600/min (GET on `/api/blends/`, `/api/soil/`, `/api/clients/`, `/api/quotes/`, `/api/programmes/`, `/api/leaf/`, `/api/feeding-plans/`, `/api/records`, `/api/workbench/`)
  - `admin` 20/min (POST/PATCH/DELETE on `/api/admin/*`, `/api/materials/`, `/api/crop-norms/`)
  - `ai` 5/min; 50/hour (POST on `/api/soil/extract`, `/api/leaf/extract`, `/api/crop-norms/generate`, `/api/soil/batch-analyze`)
  - `session` 10/min; 200/hour (all methods on `/api/sessions/*`)
  - `default` 200/min (everything else)

  Keyed by `X-Forwarded-For` with fallback to `request.client.host`.
  In-memory sliding-window store with per-(rule, key) deques.
  Bypasses `/api/health`, `/openapi`, `/docs`, `/redoc`, `/favicon`.
  Sends `Retry-After`, `X-RateLimit-Rule`, `X-RateLimit-Limit` headers on 429.

- **`pagination.py`** (NEW) — reusable `PageParams` / `Page[T]` / `apply_page()`
  helpers. Not yet wired into list endpoints — waiting on task #14 decision.

- **Audit log silent excepts upgraded** — `auth.py`, `admin.py`, `blends.py`,
  `feeding_plans.py`, `leaf.py`, `programmes.py`. Was `except Exception: pass`,
  now `except Exception: logger.debug(...)` with the event_type as context.
  Behavior unchanged (never blocks the host request) but failures are visible.

### Frontend — `sapling-web/`

- **`src/app/page.tsx`** (REPLACED) — Agent workbench dashboard.
  Layout: welcome header → quick actions row → stats strip → two-column
  (attention cards on left, recent activity on right). Collapses to single
  column on mobile. Has loading skeleton, error state with retry, and a
  server-driven onboarding state for zero-client agents with a 3-step
  "Add client → Run analysis → Build blend" welcome.
  Clean `tsc --noEmit --skipLibCheck`.

- **`.next/types/routes.d 2.ts`** and **`routes.d 4.ts`** — deleted. Stale
  macOS duplicate files that were causing a spurious TS2300 error. Next.js
  regenerates `routes.d.ts` on build.

### Committed in git (just one commit)

```
<new> Remove legacy Streamlit blend/fertilizer apps
```

Everything else above is on disk, unstaged, waiting for you to bundle it
with your untracked backend code.

---

## Task list state (for reference)

### Done

1. ✅ Commit legacy dir deletions
2. ✅ Fix dead role filters in admin.py
3. ✅ Scaffold pytest
4. ✅ Golden tests — soil_engine
5. ✅ Golden tests — optimizer
6. ✅ Golden tests — feeding_engine
7. ✅ Audit existing RLS policies
8. ✅ Migration 032 (soft-delete consistency)
9. ✅ Migration 033 (indexes)
10. ✅ Migration 034 (RLS policies)
11. ✅ Migration 035 + auth.py refactor (impersonation to DB)
12. ✅ DB health check
15. ✅ Structured logging + request middleware
16. ✅ Dashboard parent phase
17. ✅ Rate limiting (path-classifying middleware, zero router touches)
18. ✅ Dashboard data scoping
19. ✅ Workbench backend endpoint
20. ✅ Workbench layout design
21. ✅ Workbench page implementation
22. ✅ Attention card components
23. ✅ Onboarding state
24. ✅ Extended tests (notation, comparison, corrections)
25. ✅ Silent except-pass → structured debug logs (audit_log sites only)
26. ✅ Rate limit middleware tests
27. ✅ Foliar engine tests

### Parked (waiting on you)

14. 🟡 **Pagination envelope wiring.** Helper module done; threading it
    through routers + updating the frontend list pages is a backend/frontend
    coordinated change.

---

## Footguns / things you should know

1. **Backend restart required.** The rate-limit middleware, workbench
   router, and health check upgrade are module-level imports in `main.py`.
   Kill and restart uvicorn before you test.

2. **The workbench uses columns I verified by grep**, not by schema
   introspection. If any attention card is always empty for you, check the
   structured logs for `workbench.<section>_failed` entries — they tell
   you which section's column assumption is wrong. Fix is usually a
   one-line column rename in `app/routers/workbench.py`.

3. **Rate limiter is in-memory, single-worker.** If you scale uvicorn to
   multiple workers, the budget is per-worker which means effective limits
   are multiplied by worker count. Switch to Redis-backed if you scale.

4. **Auth.py has a fallback dict** for impersonation if migration 035
   isn't applied. It's applied now, so the fallback never triggers. If you
   ever need to roll back 035 without reverting auth.py, it'll still work.

5. **TypeScript check is clean** but only with `--skipLibCheck`. There's
   nothing in my page.tsx that needs lib check changes — the `--skipLibCheck`
   is just to sidestep upstream node_modules noise.

6. **`/api/workbench/workbench` is a slightly ugly URL.** I mounted the
   router at `/api/workbench` to leave room for future siblings
   (`/api/workbench/notifications`, `/api/workbench/alerts`). Can flatten
   to `/api/workbench` + a single endpoint if you prefer.

7. **Material_markups is global, not per-agent.** My migrations originally
   assumed per-agent; you caught it with the "column agent_id does not
   exist" SQL error. Both 033 and 034 were rewritten to treat it as a
   global admin-writeable, all-readable table. If you later want per-agent
   markups, that's a schema migration (add agent_id column + backfill).

---

## What I'd tackle next (ranked)

1. **Calc bug fixes.** Tests are the safety net; now I can fix the
   audit-flagged bugs one at a time, each a principled code+test change.
   Highest impact: the optimizer `None` crash, the CEC-missing silent
   skip, the classification boundary ambiguity.
2. **Next workflow pain point** — you pick. My guesses: client →
   farm → field drill-down navigation, or the lab-PDF extract UX.
3. **Pagination envelope wiring** (task 14) — waiting on your nod.
4. **More tests** — liquid_optimizer, programme_engine, leaf_engine.
5. **Pydantic input validation** on the engine request bodies — range
   caps for yield_target, field_area_ha, etc.
