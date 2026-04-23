# Wizard → Build Artifact → Artifact View: E2E golden path

Hand-testable checklist. Also used by Claude when driving Playwright MCP
through the flow. Keep this doc in sync with the wizard code — if the
steps change, update this before shipping.

## Preconditions

- `cd sapling-api && ./venv/bin/uvicorn app.main:app --reload` running on `:8000`
- `cd sapling-web && npm run dev` running on `:3000`
- A dev account that can log in (agronomist or admin role)
- At least one client with:
  - one farm
  - one field/block with `area_ha` set
  - a linked soil analysis that has a populated `soil_values` dict (check via SQL: `select soil_values from soil_analyses where id = '...'`)
  - a crop that has `crop_growth_stages` rows seeded (Garlic, Macadamia, Maize, Wheat, Sugarcane, Lucerne are known-good)

## Golden path (happy)

### 1. Log in
- Navigate to `/login`
- Fill email + password, click "Sign in"
- **Expect:** redirect to `/` (which might redirect again to `/clients` or similar)
- **Watch for:** auth error toast, 401 in network tab

### 2. Open wizard from clients
- Navigate to `/clients`
- Click a client card → `/clients/[id]`
- Click "New Programme" or navigate to `/season-manager/new?client_id=...&farm_id=...`
- **Expect:** wizard on Step 0 with client name pre-filled

### 3. Step 0 — Client & Farm + Methods
- Verify programme name is auto-populated (`{client} — {farm}`)
- Verify season is current-year slash next-year format
- **Check the "Application methods available on this farm" section exists** with 7 checkboxes:
  - Drip fertigation
  - Pivot fertigation
  - Sprinkler fertigation
  - Foliar sprayer (pre-checked)
  - Granular spreader (pre-checked)
  - Fertigation injectors (A/B)
  - Seed treatment
- Tick any relevant methods for the test crop
- Click Next

### 4. Step 1 — Blocks
- FieldPicker renders the farm's fields
- Select at least one block that has a linked soil analysis
- Fill in yield target + unit if not pre-populated from the field record
- Click "Preview Schedule"
- **Expect:** progresses to Step 2 OR shows "N blocks skipped" amber warning if any block lacks growth stages or soil analysis

### 5. Step 2 — Schedule
- ScheduleReview renders with growth-stage bars per block
- Set a planting month for each block (or accept defaults)
- Add at least one application per block (select method + month)
- Click "Generate Blends"
- **Expect:** progresses to Step 3; no scheduleError banner

### 6. Step 3 — Blend Groups
- BlendGroups renders the optimized blends per blend_group
- **Expect:** each group shows 2–6 products (per consolidator MAX_PRODUCTS_PER_BLEND)
- Click Next

### 7. Step 4 — Review + BUILD ARTIFACT
- Summary table renders with blocks + crops + yields
- "X optimized blends ready" green callout
- **Three buttons visible:** "Save as Draft", "Activate Programme", "Build Artifact (new engine)"
- **Click "Build Artifact (new engine)"**
- **Expect toast:** success OR warning about N skipped blocks
- **Expect redirect:** `/season-manager/artifact/[uuid]`

### 8. Artifact view
- URL pattern `/season-manager/artifact/{uuid}`
- ArtifactView renders. Check each section exists:
  - **Header card** — crop, farm, planting date, season, data confidence level, blocks count
  - **Soil analysis** — one card per block with pH/nutrient numbers + headline_signals if any
  - **Pre-season** — (may be empty for a first-pass build)
  - **Stage schedule** — per-block weeks + stage bars
  - **Blends** — grouped by block name (NOT raw block_id); for clusters, shows "Cluster A: Land X, Land Y"
  - **Foliar events** — (may be empty if no triggers fired for this crop)
  - **Risk flags** — severity-sorted (critical/warn/watch/info), each with source citation
  - **Outstanding items** — includes "Block X not planned (no soil analysis linked)" for any skipped blocks
  - **Assumptions** — defaults applied with override guidance
  - **Sources audit** — dedup list of every source used
  - **Decision trace** — orchestrator breadcrumbs including any "Clustered blocks [...]" entries

### 9. State transitions
- Click "Approve" (when state=draft)
- **Expect:** state badge updates to "approved", state-action buttons show "Activate" + "Revert to draft"
- Click "Activate"
- **Expect:** state becomes "activated"
- Navigate back to `/season-manager`
- **Expect:** "Programme Artifacts · New engine" section lists this artifact with orange border

## Regression checklist

Flows that must still work (we didn't break the legacy path):

- `/season-manager` index renders both legacy programmes and new artifacts
- `/season-manager/new` wizard "Activate Programme" button still creates a legacy programme and navigates to `/season-manager/[id]`
- `/season-manager/[id]` legacy detail view still loads, tabs switch, heterogeneity_by_group warning renders if present
- `/quick-blend` standalone flow unchanged
- Nav has `Quick Blend · Quick Analysis · Season Manager · Quotes · Clients · Records` (no Programme Builder / Season Tracker entries)

## Negative-path checks

### Missing soil analysis on a block
- Create a block without linking a soil analysis, add it to the wizard
- Build Artifact
- **Expect:** toast shows "N blocks not planned (no soil analysis) — see Outstanding Items"
- Artifact renders, Outstanding Items section lists the skipped block

### Soil analysis with empty soil_values
- Use a legacy soil_analyses row (pre-`soil_values` migration) or `update soil_analyses set soil_values = null where id = '...'`
- Build Artifact
- **Expect:** toast warning, Outstanding Items includes "Block X not planned (linked soil analysis has no soil_values)"

### Multi-block, mixed crops
- Two blocks with different crops
- Click Build Artifact
- **Expect:** toast error "Mixed crops not supported in a single build (crop1, crop2). Build one artifact per crop."
- Wizard stays on Step 4; no redirect

### Clustering
- Two blocks of the same crop with very similar NPK targets → should cluster into one
- Artifact shows:
  - One cluster-level soil snapshot named "Cluster A: Land X, Land Y"
  - Per-block snapshots labelled "Land X (in Cluster A)" etc.
  - Decision trace has "Clustered blocks […] into 'A' (N.N ha, area_weighted weighting)"
- Two blocks with wildly different NPK targets → NO clustering, two separate programmes

### Heterogeneity flag
- Force a high-variance cluster: same NPK ratio but very different absolute magnitudes
- **Expect:** Risk Flag with severity=warn or critical, message naming the affected nutrients + CV % + Wilding citation

## Common breakage signals

| Symptom | Likely cause |
|---|---|
| 500 on every route after code change | Dev server stale; kill+restart |
| "Build failed: Programme build failed" generic toast | Backend 500 — check `sapling-api` logs |
| "No blocks with a linked soil analysis" despite linked | `soil_values` is null on the analysis row |
| Artifact blends section says "Block cluster_A" not "Cluster A: …" | `blockNameById` map not passed; regression |
| Refresh token error in console | Stale session; log out + back in |

## Env for automation

If later bolting on `@playwright/test`, the minimum env:

```
PLAYWRIGHT_BASE_URL=http://localhost:3000
PLAYWRIGHT_TEST_EMAIL=dev@example.com
PLAYWRIGHT_TEST_PASSWORD=...
PLAYWRIGHT_TEST_CLIENT_ID=<uuid>
PLAYWRIGHT_TEST_FARM_ID=<uuid>
PLAYWRIGHT_TEST_BLOCK_NAME="Test Block 1"
```

For the MCP-driven variant (what Claude does), no env is needed — the
agent navigates by visible text and the user provides credentials
when asked.
