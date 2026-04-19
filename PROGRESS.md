# Sapling upgrade — progress notes

Running log. Top of file is "where we are right now"; scroll down for
history of what's already shipped.

## TL;DR as of 2026-04-15 (end of day)

**Everything is committed.** Commit `3bb5d5d` landed 218 files
(+55,820 / −344) consolidating: backend security hardening, agent
workbench dashboard, full backend + frontend pagination, test suite,
and the absorption of `sapling-web` into the root monorepo. Working
tree is clean except for `.DS_Store` and `.claude/settings.local.json`
which are deliberately left alone.

**Current state:**
- **168 backend tests** passing (engines, rate limiter, pagination)
- **Backend imports cleanly** — 155 FastAPI routes registered
- **Frontend TypeScript clean** via `tsc --noEmit --skipLibCheck`
- **Migrations 032–035 applied** to Supabase; 11 tables have proper RLS policies; impersonation lives in the DB now
- **One monorepo, one git history** — previously sapling-web was a nested repo (4 commits lost in the absorption, content preserved)
- **No push to remote** — user backs up via iCloud + SSD so `jacol93-stack/fertilizer-app` remote is configured but not pushed

## Pick-up list for tomorrow (in priority order)

1. **Records page full pagination conversion** — last remaining piece of the pagination phase. Records is 997 lines with tabbed UI and complex client-side filtering. Current state: consumes the envelope via `api.getAll` so it works, but doesn't show pagination controls. Converting it properly means pushing search + user filter + tab state to the backend and wiring `usePagination`. Medium-size task.

2. **Calc bug fixes** — tests lock in current buggy behavior for ~8 audit-flagged issues. Fix the optimizer `None` crash first (highest blast radius). Each fix is a code+test update as a deliberate commit.

3. **Next workflow pain point** — user said workflow is the one they feel daily. Dashboard is v1 done. Candidates for v2:
   - Client → farm → field drill-down nav
   - Lab PDF extract UX (confidence scoring, diff view, bulk upload)
   - Season planning re-plan mid-season / programme versioning
   - Quote → order flow / quote revisions / expiry enforcement
   - Multi-step wizard state persistence / draft auto-save

4. **Workbench column assumptions** — I guessed a few column names in `workbench.py`. If any attention card is always empty when it shouldn't be, check the backend structured logs for `workbench.<section> failed` warnings and fix the column name.

## Things still parked

- **Quotes page, admin/users, admin/audit full conversion** — currently use `api.getAll` (works) but no pagination UI
- **Pydantic input validation** on engine request bodies — yield_target caps, crop_name length, field_area_ha bounds
- **Big audit backlog items** still untouched: CI/CD, Sentry, backup DR runbook, Privacy/ToS, multi-env separation, email deliverability (SPF/DKIM), file upload sanitization, GDPR export, monitoring/alerting, farmer portal, mobile PWA, WhatsApp integration

## How to verify everything's good

```bash
# Backend
cd sapling-api
venv/bin/python -m pytest tests/        # expect 168 passed
venv/bin/python -m uvicorn app.main:app --reload --port 8000
# Hit http://localhost:8000/api/health → expect {"status":"ok","database":"ok",...}

# Frontend
cd sapling-web
npx tsc --noEmit --skipLibCheck         # clean compile
npm run dev
# http://localhost:3000 → agent workbench dashboard
# http://localhost:3000/clients → paginated client list (try ?limit=10&search=foo)
```

---

## History of what's already shipped

### 2026-04-15 end of day — commit `3bb5d5d`

Unified the repo and committed everything. 218 files. See the commit
message for the full breakdown.

### 2026-04-15 daytime — pagination phase (pre-commit)

- Hardened `app/pagination.py` helper (PageParams/Page[T]/apply_page)
- Wired 10 backend list endpoints to the envelope with `count="exact"`: blends, soil, clients, quotes, programmes, leaf, feeding_plans, admin/audit-log, admin/users, admin/deleted
- Fixed a schema mismatch the user caught: `material_markups` is global, not per-agent (migrations 033+034 were corrected mid-run)
- Built frontend helpers: `src/lib/pagination.ts`, `src/lib/use-pagination.ts` (debounced search + URL sync), `src/components/pagination-controls.tsx`
- Added `api.getAll<T>()` helper that transparently unwraps the envelope for legacy consumers
- Migrated all ~15 simple list consumers to use `api.getAll`
- Converted the **clients page** to full `usePagination` with server-side search, page size picker, URL deep linking (flagship demo)
- Added 14 pagination unit tests

### 2026-04-15 overnight — test coverage expansion + cleanup

- Added golden-case tests for notation, comparison_engine, soil_corrections, foliar_engine, rate_limit middleware, pagination (95 new tests, total now 154 → 168)
- Upgraded 5 audit_log `except Exception: pass` sites to `logger.debug` so failures are visible
- Wrote comprehensive PROGRESS.md

### 2026-04-14 late — agent workbench dashboard

- New `/api/workbench/workbench` endpoint: stats, 4 attention sections (stale analyses, clients-never-analysed, pending quotes, unread messages), recent activity feed, onboarding flag
- Replaced `sapling-web/src/app/page.tsx` with workbench layout (welcome header, quick actions, stats strip, attention cards, recent activity, onboarding state)
- Task list restructured to put workflow phase under a parent task

### 2026-04-14 — backend security workstream

- **Migrations 032–035 applied to Supabase:**
  - 032 soft-delete consistency (blends, soil_analyses, feeding_plans, quotes + backfill on programmes, leaf_analyses)
  - 033 performance indexes (18 new indexes)
  - 034 RLS policies (11 tables + `public.is_admin()` helper; material_markups treated as global)
  - 035 impersonation_sessions table
- **auth.py refactor:** impersonation sessions moved from in-memory dict to DB table; timeout 60 → 15 min; IP + UA captured
- **main.py changes:** DB-backed health check, JSON log formatter (stdlib only), correlation ID request middleware
- **Rate limit middleware rewritten** as path-classifying tiered system (zero per-route decorations)
- **admin.py `/activity` bug fixed** — dead `.neq("role","admin")` filter on wrong table name `saved_blends`
- **Test suite scaffolded** with golden cases for soil_engine, optimizer, feeding_engine (59 initial tests)

### 2026-04-14 morning — first batch

- Legacy Streamlit app dirs removed (`blend_app/`, `fertilizer_app/`, `fertilizer_app_deploy/`)
- Removed stale macOS `.next/types/routes.d 2.ts` / `4.ts` duplicates
