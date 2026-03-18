# Platform Verified State — March 18, 2026

**Verified by:** Cowork session (Claude Opus)  
**Method:** Live API tests through gateway  
**Audit result:** 0 hardcoded URL violations (down from 24 critical)

---

## Healthy Services (28 confirmed)

anthropic, apollo, deepseek, excel, ga4, gemini, github, gmail, gong,
**google_ads** ✓, google_drive, google_sheets, google_slides, google_tag_manager,
groq, hubspot, **linkedin_ads** ✓, meta_ads, notion, onedrive, openai, openrouter,
outlook, perplexity, salesforce, slack, **wordpress** ✓, youtube

Services in **bold** were fixed in this session.

## Known Issues (Out of Scope)

| Service | Status | Reason |
|---------|--------|--------|
| semrush | Down | Out of API tokens — service itself works |
| gamma | Down | 400 schema_error for 30+ days — unresolved |
| leonardo | Degraded | 2/3 actions pass; 1 returns 400 |
| twitter | Removed | 404 on all endpoints |
| linkedin_ads | Degraded | 3/6 actions pass; core actions work |

## Fixes Applied

### 1. Google Ads — Registry Client Mismatch
- **Root cause:** api_registry_v2 entry had `client=ascend` instead of `client=all`
- **Fix:** Inserted corrected row with `client=all`
- **Prevention:** Patched gateway Resolve Config with handler_workflow_id fallback logic
- **Verified:** 36 campaigns returned with live metrics

### 2. WordPress — Missing Handler
- **Root cause:** No handler workflow configured; empty handler_workflow_id caused passthrough path (which has a code bug)
- **Fix:** Added wordpress to Google Suite handler (RKoOuaqcnbSYfLLp) with wordpressApi credential
- **Verified:** Full blog post data returned from kahunaworkforce.com

### 3. Hardcoded URLs (24 instances across 11 workflows)
- **Root cause:** Principle 1 violation — `https://mmurawala.app.n8n.cloud` hardcoded in Code nodes
- **Fix:** Replaced all 24 with `$vars.N8N_HOST`, re-registered 8 webhooks
- **Verified:** Audit scan shows 0 hardcoded_url violations

### 4. Stale Data Cleanup
- Capabilities catalog: google_ads v17 → v23
- Credential health: google_ads + wordpress marked healthy
- Session state: verified state written
- VPS API key file updated

## Verified DataTable IDs

**IMPORTANT:** The governing spec on GitHub has stale IDs. These are the real ones (confirmed from `$vars`):

| Table | Variable | ID |
|-------|----------|----|
| api_registry_v2 | REGISTRY_V2_API_TABLE_ID | 8uXPK6pD52xG90Y0 |
| action_map_v2 | REGISTRY_V2_ACTION_TABLE_ID | nTBOiE9byj3KcHVQ |
| tenant_config | TENANT_CONFIG_TABLE_ID | IUOPfsksOPoFG7gV |
| credential_health | CREDENTIAL_HEALTH_TABLE_ID | wCfdPfENLbe1jvc2 |
| health_test_config | HEALTH_TEST_CONFIG_TABLE_ID | MmlcQmCuoz3M33pD |
| e2e_test_manifest | E2E_MANIFEST_TABLE_ID | 2pg9Nm0o7Jd6kU1m |
| session_state | SESSION_STATE_TABLE_ID | 2z5zRvsJZsGBtsmw |
| ai_cost_log | AI_COST_TRACKER_TABLE_ID | t4tTjYDIkNYdfhdh |
| agent_memory | (none) | TmUGB90Wg1quE9Up |
| agent_tasks | (none) | wGiRrwpDnJ3lQUlT |
| capability_catalog | (none) | mIzRq6aFd01J7MPZ |
| task_queue | TASK_QUEUE_TABLE_ID | Q8a5XCTmoGhYIIDh |

## Gotchas for Future Sessions

1. **Webhook re-registration** — After PUT /workflows/{id}, toggle OFF/ON to re-register webhooks
2. **Registry client field** — Use `client=all` for shared services, never a specific client
3. **DataTable DELETE not supported** — n8n Cloud API can only INSERT and READ rows
4. **Capabilities catalog lags** — Verify against handler code, not the catalog
5. **Governing spec IDs are stale** — Always check $vars at runtime
6. **Build Dynamic Request bug** — Passthrough path has body reference error (worked around via handler fallback)
7. **E2E health lags reality** — Always verify with live gateway calls, not just health table
