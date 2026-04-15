#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Sapling App — Full Flow Integration Test
# Tests both admin and agent roles across all restructured pages
# ═══════════════════════════════════════════════════════════════

API="http://localhost:8000"
ADMIN_TOKEN=$(cat /tmp/sapling_admin_token)
AGENT_TOKEN=$(cat /tmp/sapling_agent_token)

PASS=0
FAIL=0
WARN=0

pass() { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }
warn() { WARN=$((WARN+1)); echo "  ⚠️  $1"; }

api_get() {
  local token=$1 path=$2
  curl -s "$API$path" -H "Authorization: Bearer $token" -H "Content-Type: application/json" 2>/dev/null
}

api_post() {
  local token=$1 path=$2 body=$3
  curl -s "$API$path" -X POST -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d "$body" 2>/dev/null
}

api_patch() {
  local token=$1 path=$2 body=$3
  curl -s "$API$path" -X PATCH -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d "$body" 2>/dev/null
}

check_field() {
  local json="$1" field="$2" expected="$3" label="$4"
  local actual=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('$field','MISSING'))" 2>/dev/null)
  if [ "$actual" = "$expected" ]; then
    pass "$label: $field = $actual"
  else
    fail "$label: expected $field=$expected, got $actual"
  fi
}

check_not_empty() {
  local json="$1" field="$2" label="$3"
  local val=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); v=d.get('$field'); print('EMPTY' if not v else 'OK')" 2>/dev/null)
  if [ "$val" = "OK" ]; then
    pass "$label: $field is present"
  else
    fail "$label: $field is empty/missing"
  fi
}

check_array_len() {
  local json="$1" field="$2" min="$3" label="$4"
  local len=$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('$field',[])))" 2>/dev/null)
  if [ "$len" -ge "$min" ] 2>/dev/null; then
    pass "$label: $field has $len items (min $min)"
  else
    fail "$label: $field has $len items, expected >= $min"
  fi
}

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  SAPLING APP — FULL FLOW INTEGRATION TEST"
echo "═══════════════════════════════════════════════════════"
echo ""

# ─── TEST 1: CROP NORMS ───────────────────────────────────────
echo "── 1. Crop Norms (reference data) ──"
CROPS=$(api_get "$ADMIN_TOKEN" "/api/crop-norms/")
CROP_COUNT=$(echo "$CROPS" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$CROP_COUNT" -gt 10 ] 2>/dev/null; then
  pass "Loaded $CROP_COUNT crops"
else
  fail "Only $CROP_COUNT crops loaded"
fi

# ─── TEST 2: QUICK ANALYSIS — SOIL (no crop) ──────────────────
echo ""
echo "── 2. Quick Analysis — Soil Classification (no crop) ──"
SOIL_RESULT=$(api_post "$ADMIN_TOKEN" "/api/soil/classify" '{
  "soil_values": {"pH (H2O)": 6.2, "pH (KCl)": 5.5, "Org C": 1.8, "CEC": 12, "N (total)": 35, "P (Bray-1)": 18, "K": 120, "Ca": 1200, "Mg": 280, "S": 8, "Fe": 45, "B": 0.4, "Mn": 12, "Zn": 2.5, "Mo": 0.1, "Cu": 1.2, "Na": 15, "Clay": 22}
}')
check_not_empty "$SOIL_RESULT" "classifications" "Soil classify (no crop)"
check_not_empty "$SOIL_RESULT" "ratios" "Soil classify (no crop)"

# Check individual classifications exist
CLS_COUNT=$(echo "$SOIL_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('classifications',{})))" 2>/dev/null)
if [ "$CLS_COUNT" -gt 10 ] 2>/dev/null; then
  pass "Got $CLS_COUNT parameter classifications"
else
  fail "Only $CLS_COUNT classifications returned"
fi

# ─── TEST 3: QUICK ANALYSIS — SOIL WITH CROP + TARGETS ────────
echo ""
echo "── 3. Quick Analysis — Soil with Crop + Targets ──"
SOIL_RUN=$(api_post "$ADMIN_TOKEN" "/api/soil/run" '{
  "soil_values": {"pH (H2O)": 6.2, "pH (KCl)": 5.5, "Org C": 1.8, "CEC": 12, "N (total)": 35, "P (Bray-1)": 18, "K": 120, "Ca": 1200, "Mg": 280, "S": 8, "Fe": 45, "B": 0.4, "Mn": 12, "Zn": 2.5, "Mo": 0.1, "Cu": 1.2, "Na": 15, "Clay": 22},
  "crop_name": "Avocado",
  "yield_target": 12
}')
check_not_empty "$SOIL_RUN" "classifications" "Soil /run with crop"
check_not_empty "$SOIL_RUN" "ratios" "Soil /run with crop"
check_not_empty "$SOIL_RUN" "targets" "Soil /run with crop"

TARGET_COUNT=$(echo "$SOIL_RUN" | python3 -c "import json,sys; d=json.load(sys.stdin); t=d.get('targets',[]); print(len(t) if t else 0)" 2>/dev/null)
if [ "$TARGET_COUNT" -gt 5 ] 2>/dev/null; then
  pass "Got $TARGET_COUNT nutrient targets"
else
  fail "Only $TARGET_COUNT targets returned (expected 6+)"
fi

# ─── TEST 4: LEAF ANALYSIS — WITH CROP ────────────────────────
echo ""
echo "── 4. Leaf Analysis — With Crop ──"
LEAF_RESULT=$(api_post "$ADMIN_TOKEN" "/api/leaf/classify" '{
  "crop": "Avocado",
  "values": {"N": 1.8, "P": 0.10, "K": 0.9, "Ca": 1.2, "Mg": 0.3, "S": 0.15, "Fe": 50, "Mn": 30, "Zn": 15, "Cu": 5, "B": 25, "Mo": 0.5}
}')
check_not_empty "$LEAF_RESULT" "classifications" "Leaf classify"
LEAF_CLS=$(echo "$LEAF_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('classifications',{})))" 2>/dev/null)
if [ "$LEAF_CLS" -gt 0 ] 2>/dev/null; then
  pass "Got $LEAF_CLS leaf classifications"
else
  fail "No leaf classifications returned"
fi

# Check for deficiencies/recommendations
DEF_COUNT=$(echo "$LEAF_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('deficiencies',[])))" 2>/dev/null)
echo "  ℹ️  $DEF_COUNT deficiencies detected"

# ─── TEST 5: LEAF ANALYSIS — WITHOUT CROP (new feature) ───────
echo ""
echo "── 5. Leaf Analysis — Without Crop (should not crash) ──"
LEAF_NOCROP=$(api_post "$ADMIN_TOKEN" "/api/leaf/classify" '{
  "crop": null,
  "values": {"N": 1.8, "P": 0.10, "K": 0.9}
}')
ERROR_CHECK=$(echo "$LEAF_NOCROP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('detail','OK'))" 2>/dev/null)
if [ "$ERROR_CHECK" = "OK" ] || echo "$LEAF_NOCROP" | python3 -c "import json,sys; d=json.load(sys.stdin); print('classifications' in d)" 2>/dev/null | grep -q "True"; then
  pass "Leaf classify without crop: no crash"
else
  fail "Leaf classify without crop failed: $ERROR_CHECK"
fi

# ─── TEST 6: SAVE SOIL ANALYSIS ───────────────────────────────
echo ""
echo "── 6. Save Soil Analysis (admin) ──"
SAVE_RESULT=$(api_post "$ADMIN_TOKEN" "/api/soil/" '{
  "crop": "Avocado",
  "cultivar": "Hass",
  "yield_target": 12,
  "yield_unit": "t/ha",
  "lab_name": "Test Lab",
  "soil_values": {"pH (H2O)": 6.2, "K": 120, "Ca": 1200, "Mg": 280, "P (Bray-1)": 18, "N (total)": 35},
  "classifications": {"pH (H2O)": "Optimal", "K": "Low", "Ca": "Optimal"},
  "ratio_results": []
}')
ANALYSIS_ID=$(echo "$SAVE_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','FAIL'))" 2>/dev/null)
if [ "$ANALYSIS_ID" != "FAIL" ] && [ -n "$ANALYSIS_ID" ]; then
  pass "Saved analysis: $ANALYSIS_ID"
  echo "$ANALYSIS_ID" > /tmp/sapling_test_analysis_id
else
  fail "Failed to save analysis"
  echo "SKIP" > /tmp/sapling_test_analysis_id
fi

# ─── TEST 7: SEASON MANAGER — CREATE PROGRAMME (Auto mode) ────
echo ""
echo "── 7. Season Manager — Create Programme (Auto/Admin) ──"
PROG_RESULT=$(api_post "$ADMIN_TOKEN" "/api/programmes/" '{
  "name": "Test Farm 2026/2027",
  "season": "2026/2027",
  "blocks": [
    {"name": "Block A", "crop": "Avocado", "cultivar": "Hass", "area_ha": 5, "yield_target": 12, "yield_unit": "t/ha", "tree_age": 8, "pop_per_ha": 400},
    {"name": "Block B", "crop": "Maize", "area_ha": 10, "yield_target": 8, "yield_unit": "t/ha"}
  ]
}')
PROG_ID=$(echo "$PROG_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','FAIL'))" 2>/dev/null)
if [ "$PROG_ID" != "FAIL" ] && [ -n "$PROG_ID" ]; then
  pass "Created programme: $PROG_ID"
  echo "$PROG_ID" > /tmp/sapling_test_prog_id
else
  fail "Failed to create programme"
  echo "$PROG_RESULT" | head -2
fi

check_field "$PROG_RESULT" "status" "draft" "Programme"

BLOCK_COUNT=$(echo "$PROG_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('programme_blocks', d.get('blocks',[]))))" 2>/dev/null)
if [ "$BLOCK_COUNT" = "2" ]; then
  pass "Programme has 2 blocks"
else
  fail "Expected 2 blocks, got $BLOCK_COUNT"
fi

# ─── TEST 8: COLD START — CREATE ACTIVE PROGRAMME ─────────────
echo ""
echo "── 8. Cold Start — Create Active Programme ──"
COLD_RESULT=$(api_post "$ADMIN_TOKEN" "/api/programmes/" '{
  "name": "Cold Start Test 2026",
  "season": "2026",
  "status": "active",
  "blocks": [
    {"name": "Field 1", "crop": "Wheat", "area_ha": 20}
  ]
}')
COLD_ID=$(echo "$COLD_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','FAIL'))" 2>/dev/null)
COLD_STATUS=$(echo "$COLD_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','FAIL'))" 2>/dev/null)
if [ "$COLD_STATUS" = "active" ]; then
  pass "Cold start programme created with status=active"
  echo "$COLD_ID" > /tmp/sapling_test_cold_id
else
  fail "Cold start status=$COLD_STATUS, expected active"
fi

# ─── TEST 9: RECORD APPLICATION ───────────────────────────────
echo ""
echo "── 9. Record Application (Sapling product) ──"
COLD_BLOCK_ID=$(echo "$COLD_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); blocks=d.get('programme_blocks',d.get('blocks',[])); print(blocks[0]['id'] if blocks else 'FAIL')" 2>/dev/null)

APP_RESULT=$(api_post "$ADMIN_TOKEN" "/api/programmes/$COLD_ID/applications" "{
  \"block_id\": \"$COLD_BLOCK_ID\",
  \"actual_date\": \"2026-03-15\",
  \"actual_rate_kg_ha\": 750,
  \"product_name\": \"Sapling 3:2:1\",
  \"product_type\": \"pelletised\",
  \"is_sapling_product\": true,
  \"method\": \"broadcast\",
  \"status\": \"applied\"
}")
APP_ID=$(echo "$APP_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','FAIL'))" 2>/dev/null)
if [ "$APP_ID" != "FAIL" ] && [ -n "$APP_ID" ]; then
  pass "Recorded Sapling application: $APP_ID"
else
  fail "Failed to record application"
  echo "$APP_RESULT" | head -2
fi

# ─── TEST 10: RECORD COMPETITOR APPLICATION ────────────────────
echo ""
echo "── 10. Record Competitor Application ──"
COMP_RESULT=$(api_post "$ADMIN_TOKEN" "/api/programmes/$COLD_ID/applications" "{
  \"block_id\": \"$COLD_BLOCK_ID\",
  \"actual_date\": \"2026-04-01\",
  \"actual_rate_kg_ha\": 500,
  \"product_name\": \"CompetitorBrand XYZ\",
  \"product_type\": \"granular\",
  \"is_sapling_product\": false,
  \"method\": \"broadcast\",
  \"status\": \"applied\"
}")
COMP_ID=$(echo "$COMP_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','FAIL'))" 2>/dev/null)
COMP_SAPLING=$(echo "$COMP_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('is_sapling_product','MISSING'))" 2>/dev/null)
if [ "$COMP_ID" != "FAIL" ] && [ "$COMP_SAPLING" = "False" ]; then
  pass "Recorded competitor application with is_sapling_product=False"
else
  fail "Competitor application failed: sapling=$COMP_SAPLING"
fi

# ─── TEST 11: LIST APPLICATIONS ───────────────────────────────
echo ""
echo "── 11. List Applications ──"
APPS_LIST=$(api_get "$ADMIN_TOKEN" "/api/programmes/$COLD_ID/applications")
APP_LIST_COUNT=$(echo "$APPS_LIST" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$APP_LIST_COUNT" = "2" ]; then
  pass "Listed 2 applications"
else
  fail "Expected 2 applications, got $APP_LIST_COUNT"
fi

# Check competitor flag preserved
COMP_FLAG=$(echo "$APPS_LIST" | python3 -c "
import json,sys
apps=json.load(sys.stdin)
comp=[a for a in apps if a.get('product_name')=='CompetitorBrand XYZ']
print(comp[0].get('is_sapling_product','MISSING') if comp else 'NOT_FOUND')
" 2>/dev/null)
if [ "$COMP_FLAG" = "False" ]; then
  pass "Competitor flag preserved in list"
else
  fail "Competitor flag not preserved: $COMP_FLAG"
fi

# ─── TEST 12: VARIANCE ENDPOINT ───────────────────────────────
echo ""
echo "── 12. Variance Report ──"
VARIANCE=$(api_get "$ADMIN_TOKEN" "/api/programmes/$COLD_ID/variance")
VAR_STATUS=$(echo "$VARIANCE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('overall',{}).get('status','FAIL'))" 2>/dev/null)
if [ "$VAR_STATUS" != "FAIL" ] && [ -n "$VAR_STATUS" ]; then
  pass "Variance report returned, status=$VAR_STATUS"
else
  warn "Variance report: $VAR_STATUS (may need generated blends)"
fi

# ─── TEST 13: PROGRAMME STATUS ENDPOINT ───────────────────────
echo ""
echo "── 13. Programme Status ──"
STATUS=$(api_get "$ADMIN_TOKEN" "/api/programmes/$COLD_ID/status")
STATUS_APPLIED=$(echo "$STATUS" | python3 -c "import json,sys; print(json.load(sys.stdin).get('applications_applied',0))" 2>/dev/null)
if [ "$STATUS_APPLIED" = "2" ]; then
  pass "Status reports 2 applied applications"
else
  warn "Status reports $STATUS_APPLIED applied (expected 2)"
fi

# ─── TEST 14: ADJUSTMENTS — CREATE + LIST ─────────────────────
echo ""
echo "── 14. Adjustments — Create + List ──"
ADJ_RESULT=$(api_post "$ADMIN_TOKEN" "/api/programmes/$COLD_ID/adjustments" "{
  \"block_id\": \"$COLD_BLOCK_ID\",
  \"trigger_type\": \"observation\",
  \"adjustment_data\": {\"reason\": \"Yellowing leaves observed\", \"action\": \"Increase N by 20%\"},
  \"notes\": \"Field inspection 2026-04-01\"
}")
ADJ_ID=$(echo "$ADJ_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','FAIL'))" 2>/dev/null)
if [ "$ADJ_ID" != "FAIL" ] && [ -n "$ADJ_ID" ]; then
  pass "Created adjustment: $ADJ_ID"
else
  fail "Failed to create adjustment"
fi

ADJ_LIST=$(api_get "$ADMIN_TOKEN" "/api/programmes/$COLD_ID/adjustments")
ADJ_COUNT=$(echo "$ADJ_LIST" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$ADJ_COUNT" -ge 1 ] 2>/dev/null; then
  pass "Listed $ADJ_COUNT adjustment(s)"
else
  fail "GET adjustments returned $ADJ_COUNT items"
fi

# ─── TEST 15: PROGRAMME LIST ──────────────────────────────────
echo ""
echo "── 15. Programme List (admin sees all) ──"
PROG_LIST=$(api_get "$ADMIN_TOKEN" "/api/programmes/")
PROG_LIST_COUNT=$(echo "$PROG_LIST" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$PROG_LIST_COUNT" -ge 2 ] 2>/dev/null; then
  pass "Admin sees $PROG_LIST_COUNT programmes"
else
  fail "Admin only sees $PROG_LIST_COUNT programmes"
fi

# ─── TEST 16: AGENT ROLE — CREATE + ISOLATE ───────────────────
echo ""
echo "── 16. Agent Role — Create Programme ──"
AGENT_PROG=$(api_post "$AGENT_TOKEN" "/api/programmes/" '{
  "name": "Agent Test Programme",
  "season": "2026/2027",
  "blocks": [{"name": "Agent Block 1", "crop": "Maize", "area_ha": 15}]
}')
AGENT_PROG_ID=$(echo "$AGENT_PROG" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','FAIL'))" 2>/dev/null)
if [ "$AGENT_PROG_ID" != "FAIL" ] && [ -n "$AGENT_PROG_ID" ]; then
  pass "Agent created programme: $AGENT_PROG_ID"
else
  fail "Agent failed to create programme"
  echo "$AGENT_PROG" | head -2
fi

echo ""
echo "── 17. Agent Role — List (should only see own) ──"
AGENT_LIST=$(api_get "$AGENT_TOKEN" "/api/programmes/")
AGENT_LIST_COUNT=$(echo "$AGENT_LIST" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$AGENT_LIST_COUNT" = "1" ]; then
  pass "Agent sees only 1 programme (own)"
else
  warn "Agent sees $AGENT_LIST_COUNT programmes (expected 1)"
fi

# ─── TEST 18: AGENT — SOIL ANALYSIS ──────────────────────────
echo ""
echo "── 18. Agent — Soil Analysis + Targets ──"
AGENT_SOIL=$(api_post "$AGENT_TOKEN" "/api/soil/run" '{
  "soil_values": {"pH (H2O)": 5.8, "K": 90, "Ca": 800, "Mg": 200, "P (Bray-1)": 12, "N (total)": 25},
  "crop_name": "Maize",
  "yield_target": 8
}')
AGENT_CLS=$(echo "$AGENT_SOIL" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('classifications',{})))" 2>/dev/null)
AGENT_TGT=$(echo "$AGENT_SOIL" | python3 -c "import json,sys; d=json.load(sys.stdin); t=d.get('targets',[]); print(len(t) if t else 0)" 2>/dev/null)
if [ "$AGENT_CLS" -gt 0 ] 2>/dev/null; then
  pass "Agent got $AGENT_CLS classifications, $AGENT_TGT targets"
else
  fail "Agent soil analysis failed"
fi

# ─── TEST 19: AGENT — RECORD APPLICATION ──────────────────────
echo ""
echo "── 19. Agent — Record Application ──"
AGENT_BLOCK_ID=$(echo "$AGENT_PROG" | python3 -c "import json,sys; d=json.load(sys.stdin); blocks=d.get('programme_blocks',d.get('blocks',[])); print(blocks[0]['id'] if blocks else 'FAIL')" 2>/dev/null)
AGENT_APP=$(api_post "$AGENT_TOKEN" "/api/programmes/$AGENT_PROG_ID/applications" "{
  \"block_id\": \"$AGENT_BLOCK_ID\",
  \"actual_date\": \"2026-03-20\",
  \"actual_rate_kg_ha\": 600,
  \"product_name\": \"Generic NPK\",
  \"product_type\": \"granular\",
  \"is_sapling_product\": false,
  \"method\": \"broadcast\"
}")
AGENT_APP_ID=$(echo "$AGENT_APP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id','FAIL'))" 2>/dev/null)
if [ "$AGENT_APP_ID" != "FAIL" ]; then
  pass "Agent recorded competitor application"
else
  fail "Agent application failed"
fi

# ─── TEST 20: AUDIT — COMPETITOR EVENTS ───────────────────────
echo ""
echo "── 20. Admin Audit — Competitor Events ──"
AUDIT=$(api_get "$ADMIN_TOKEN" "/api/admin/audit-log?event_type=competitor_product&limit=10")
AUDIT_COUNT=$(echo "$AUDIT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else len(d.get('events',d.get('data',[]))))" 2>/dev/null)
if [ "$AUDIT_COUNT" -ge 1 ] 2>/dev/null; then
  pass "Found $AUDIT_COUNT competitor_product audit event(s)"
else
  warn "Competitor audit events: $AUDIT_COUNT (check audit log format)"
fi

# ─── TEST 21: QUICK BLEND — PELLETISED LABEL ─────────────────
echo ""
echo "── 21. Quick Blend — Pelletised Label Check ──"
BLEND_PAGE=$(curl -s "http://localhost:3000/quick-blend" 2>/dev/null)
if echo "$BLEND_PAGE" | grep -q "Pelletised Blend"; then
  pass "Quick Blend shows 'Pelletised Blend' label"
else
  fail "Quick Blend still shows old 'Dry Blend' label"
fi
if echo "$BLEND_PAGE" | grep -q "Dry Blend"; then
  fail "Quick Blend still contains 'Dry Blend' text"
else
  pass "No 'Dry Blend' text found"
fi

# ─── CLEANUP ──────────────────────────────────────────────────
echo ""
echo "── Cleanup ──"
# Delete test programmes
api_post "$ADMIN_TOKEN" "/api/programmes/$PROG_ID/delete" '{}' > /dev/null 2>&1 && echo "  🗑  Deleted test programme $PROG_ID"
api_post "$ADMIN_TOKEN" "/api/programmes/$COLD_ID/delete" '{}' > /dev/null 2>&1 && echo "  🗑  Deleted cold start programme $COLD_ID"
api_post "$AGENT_TOKEN" "/api/programmes/$AGENT_PROG_ID/delete" '{}' > /dev/null 2>&1 && echo "  🗑  Deleted agent programme $AGENT_PROG_ID"

# Delete test analysis
if [ -f /tmp/sapling_test_analysis_id ]; then
  AID=$(cat /tmp/sapling_test_analysis_id)
  if [ "$AID" != "SKIP" ]; then
    curl -s "$API/api/soil/$AID" -X DELETE -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null 2>&1 && echo "  🗑  Deleted test analysis $AID"
  fi
fi

# ─── SUMMARY ──────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  RESULTS: $PASS passed, $FAIL failed, $WARN warnings"
echo "═══════════════════════════════════════════════════════"
echo ""

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
