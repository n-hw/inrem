#!/usr/bin/env bash
# QA smoke test — InRem backend end-to-end happy paths.
# 외부 호출 없이 docker-compose 위의 백엔드를 검증한다.
set -o pipefail

BASE="${BASE:-http://localhost:8000/api/v1}"
EMAIL="qa-$(date +%s)@example.com"
PASSWORD="qa-passw0rd!"

pass=0
fail=0
failed_tests=()

ok()   { echo "  ✅ $1"; pass=$((pass + 1)); }
nope() { echo "  ❌ $1"; fail=$((fail + 1)); failed_tests+=("$1"); }

req() {
    # req METHOD URL [BODY] [EXTRA_HEADERS]
    local method=$1 url=$2 body=${3:-} extra=${4:-}
    local args=(-sS -o /tmp/qa_body -w "%{http_code}" -X "$method" "${BASE}$url")
    [[ -n $body ]] && args+=(-H "Content-Type: application/json" -d "$body")
    [[ -n ${TOKEN:-} ]] && args+=(-H "Authorization: Bearer $TOKEN")
    [[ -n $extra ]] && args+=($extra)
    curl "${args[@]}"
}

assert_status() {
    local got=$1 want=$2 label=$3
    if [[ "$got" == "$want" ]]; then ok "$label ($got)"
    else nope "$label expected $want got $got — body: $(head -c 200 /tmp/qa_body)"
    fi
}

echo
echo "▶ Scenario A — Auth lifecycle"
status=$(req POST /auth/register "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
assert_status "$status" 201 "register"
TOKEN=$(jq -r .access_token /tmp/qa_body)
REFRESH=$(jq -r .refresh_token /tmp/qa_body)

status=$(req GET /auth/me)
assert_status "$status" 200 "GET /auth/me with access token"

# Login (form-encoded — OAuth2 password flow)
status=$(curl -sS -o /tmp/qa_body -w "%{http_code}" \
    -X POST "${BASE}/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$EMAIL&password=$PASSWORD")
assert_status "$status" 200 "login (form)"

status=$(req POST /auth/refresh "{\"refresh_token\":\"$REFRESH\"}")
assert_status "$status" 200 "refresh: valid refresh → new pair"
TOKEN=$(jq -r .access_token /tmp/qa_body)

# Cross-type: send access as refresh → 401
status=$(curl -sS -o /tmp/qa_body -w "%{http_code}" \
    -X POST "${BASE}/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\":\"$TOKEN\"}")
assert_status "$status" 401 "refresh rejects access-token-as-refresh"

echo
echo "▶ Scenario B — Login rate-limit (brute force defense)"
for i in 1 2 3 4 5; do
    status=$(curl -sS -o /dev/null -w "%{http_code}" \
        -X POST "${BASE}/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=brute$i@x.com&password=wrong")
done
# 6th from same email — different emails each don't share bucket; reuse 1
status=$(curl -sS -o /dev/null -w "%{http_code}" \
    -X POST "${BASE}/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=brute1@x.com&password=wrong")
# bucket is per (email,ip) — we hit each email once, so we'd need 6+ on same email
# Send 5 more on brute1 to exhaust quota.
for i in 1 2 3 4 5; do
    status=$(curl -sS -o /dev/null -w "%{http_code}" \
        -X POST "${BASE}/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=brute1@x.com&password=wrong")
done
assert_status "$status" 429 "6th login attempt (same email) → 429"

echo
echo "▶ Scenario C — Settings"
status=$(req GET /settings/policy)
assert_status "$status" 200 "GET settings/policy"

status=$(req PATCH /settings/policy '{"threshold_hours":6}')
assert_status "$status" 200 "PATCH settings/policy → strict"

status=$(req POST /settings/upsell/click '{"feature":"family_share","surface":"home"}')
assert_status "$status" 200 "upsell click logged"

status=$(req POST /settings/upsell/click '{"feature":"totally_made_up"}')
assert_status "$status" 422 "upsell click rejects unknown feature"

echo
echo "▶ Scenario D — Heritage Box"
status=$(req POST /heritage/assets \
    '{"name":"Instagram","type":"social_account","action_on_death":"memorialize","identifier":"@me","secret":"hunter2"}')
assert_status "$status" 201 "create asset with secret"
ASSET_ID=$(jq -r .id /tmp/qa_body)
HAS_SECRET=$(jq -r .has_secret /tmp/qa_body)
[[ "$HAS_SECRET" == "true" ]] && ok "asset.has_secret = true" || nope "has_secret should be true"

# Sensitive payload must NOT leak in response
if jq -e '.encrypted_payload // empty' /tmp/qa_body > /dev/null; then
    nope "asset response leaks encrypted_payload"
else
    ok "asset response does NOT leak encrypted_payload"
fi

status=$(req GET "/heritage/assets/$ASSET_ID/secret")
assert_status "$status" 200 "reveal secret (1st time)"
SECRET=$(jq -r .secret /tmp/qa_body)
[[ "$SECRET" == "hunter2" ]] && ok "decrypted secret matches plaintext" || nope "decryption mismatch"

# Search + filter
req POST /heritage/assets '{"name":"Netflix","type":"subscription","action_on_death":"delete"}' >/dev/null
status=$(req GET "/heritage/assets?search=netflix")
assert_status "$status" 200 "search?search=netflix"
COUNT=$(jq 'length' /tmp/qa_body)
[[ "$COUNT" -ge 1 ]] && ok "search returns ≥1 match" || nope "search returned 0 matches"

status=$(req GET "/heritage/assets?type=subscription")
assert_status "$status" 200 "filter ?type=subscription"

status=$(req GET /heritage/assets/summary)
assert_status "$status" 200 "summary"
TOTAL=$(jq -r .total /tmp/qa_body)
[[ "$TOTAL" -ge 2 ]] && ok "summary.total ≥ 2 (got $TOTAL)" || nope "summary.total = $TOTAL"

echo
echo "▶ Scenario E — Secret reveal rate-limit (10/min)"
ok_count=0
for i in $(seq 1 11); do
    status=$(req GET "/heritage/assets/$ASSET_ID/secret")
    if [[ "$status" == "200" ]]; then ok_count=$((ok_count + 1)); fi
done
status=$(req GET "/heritage/assets/$ASSET_ID/secret")
assert_status "$status" 429 "12th reveal → 429"

echo
echo "▶ Scenario F — Signal & Status (HomeScreen flow)"
status=$(req POST /signal/heartbeat '{"signal_type":"app_open"}')
assert_status "$status" 200 "heartbeat"

status=$(req GET /signal/status)
assert_status "$status" 200 "status (read-only)"

echo
echo "▶ Scenario G — Guardian flow"
status=$(req POST /guardian/invite)
assert_status "$status" 201 "create guardian invitation code"

# Invite rate-limit (5/hour)
for i in 1 2 3 4 5; do
    req POST /guardian/invite >/dev/null
done
status=$(req POST /guardian/invite)
assert_status "$status" 429 "6th invite → 429"

echo
echo "▶ Scenario H — Account deletion (PIPA flow)"
status=$(req DELETE /auth/me)
assert_status "$status" 200 "DELETE /auth/me (request deletion)"
SECONDS_REMAINING=$(jq -r .seconds_remaining /tmp/qa_body)
[[ "$SECONDS_REMAINING" -gt 0 ]] && ok "grace seconds_remaining > 0" || nope "no grace seconds"

status=$(req POST /auth/me/restore)
assert_status "$status" 200 "restore within grace"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RESULTS: $pass pass · $fail fail"
if [[ "$fail" -gt 0 ]]; then
    echo "Failed tests:"
    for t in "${failed_tests[@]}"; do echo "  - $t"; done
    exit 1
fi
exit 0
