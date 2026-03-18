# Ascend GTM — n8n Platform Session Handover

**Session Date:** March 18, 2026
**Session Type:** Infrastructure audit, fix, and governance buildout
**Lead Engineer:** Claude Opus (Cowork)
**Duration:** ~5 hours
**Status:** All P0s and P1s complete. P2s scoped for next session.

---

## Executive Summary

Mishaal asked: "Can you confirm this handover document is done?" The answer was no — not the document, but the actual tasks it described. Google Ads had been broken for weeks, WordPress had no handler, 24 workflows had hardcoded URLs, and every AI session that touched the platform left it slightly more confused than it found it.

This session fixed the broken services, built a governance layer so tools stop breaking things, and created an architecture plan (ADR-001) for how the platform should be managed long-term.

---

## Part 1: What Was Broken and How It Was Fixed

### Fix 1: Google Ads — Broken for Weeks

**Symptom:** Every Google Ads request returned "No registry entry for domain google_ads client kahuna."

**What everyone thought:** OAuth credential expired. Mishaal re-authed "a million times."

**Actual root cause:** The `api_registry_v2` DataTable entry for google_ads had `client=ascend` instead of `client=all`. When any request came in with `client=kahuna`, the gateway's Resolve Config couldn't find a matching entry. The credential was fine. Re-authing would never fix it.

**How I found it:** Traced the actual gateway execution (execution #24528). The Resolve Config node returned `{resolved: false, error: "No registry entry for domain google_ads client kahuna"}`. Then I checked the registry table and found the client mismatch.

**Fix applied:**
1. Inserted a new `api_registry_v2` row: `google_ads, client=all, handler=6e9ooA3kc0zAPWyy`
2. Patched the gateway's Resolve Config Code node with fallback logic: if a matched entry has an empty `handler_workflow_id`, fall back to the `client=all` entry

**Why it must be done this way:** n8n Cloud's DataTable API does not support DELETE or UPDATE on rows. You can only INSERT. So the old `client=ascend` row still exists — we can't remove it. The fallback logic ensures the correct `client=all` row is preferred.

**Verification:** 36 Google Ads campaigns returned with live metrics (impressions, clicks, cost).

### Fix 2: WordPress — No Handler Existed

**Symptom:** WordPress requests returned HTTP 500 with "Unknown API: wordpress."

**Actual root cause:** Two problems stacked:
1. The `api_registry_v2` entry for wordpress had an empty `handler_workflow_id`
2. WordPress wasn't in any handler's domain list

Without a handler_workflow_id, requests fell through to the gateway's passthrough path, which has a code bug (`ReferenceError: Cannot access 'body' before initialization`). Even if the passthrough worked, WordPress uses n8n credential auth (`wordpressApi` type), which passthrough can't inject — it only handles API keys stored in `$vars`.

**Fix applied:**
1. Added WordPress to the Google Suite handler (workflow `RKoOuaqcnbSYfLLp`):
   - Added `wordpress` to the `apiConfigs` object with all 8 WP REST API v2 endpoints
   - Added "WordPress" condition to the Route by Domain Switch node
   - Added "Call WordPress" HTTP Request node with `wordpressApi` credential (`jIBRhrEDzCgVi5ru`)
   - Connected: Switch → Call WordPress → Format Response
2. Inserted `api_registry_v2` row: `wordpress, client=all, handler=RKoOuaqcnbSYfLLp`

**Why this approach:** WordPress needs handler routing (not passthrough) because it authenticates via n8n's credential system, not an API key in `$vars`. The Google Suite handler already handles 15+ similar APIs with the same pattern.

**Gotcha encountered:** First attempt used `httpBasicAuth` credential type — wrong. The actual credential type is `wordpressApi`. n8n credential types must match exactly or you get "Credential does not exist for type X."

**Verification:** Full blog post data returned from kahunaworkforce.com (63.9KB response).

### Fix 3: 24 Hardcoded URLs Across 11 Workflows

**What:** 11 workflows had `https://mmurawala.app.n8n.cloud` hardcoded in Code nodes instead of `$vars.N8N_HOST`. This violates Governing Spec Principle 1 (Zero Hardcoding).

**Fix:** Replaced all 24 instances with `$vars.N8N_HOST`. Re-registered webhooks on all 8 webhook-triggered workflows (toggle OFF/ON required after API workflow updates).

**Affected workflows:** OAuth Credential Sentinel, Task Orchestrator, Data Analyst Agent, E2E Test Suite, Session Bootstrap, Add API Process, Demand Gen Agent, Content Strategist Agent, OAuth Auto-Healer, Cost Log Rotation, Error Notifier.

**Verification:** Audit scan shows 0 `hardcoded_url` violations (down from 24 critical).

### Fix 4: LinkedIn Ads — Re-Auth Worked

Mishaal re-authorized the LinkedIn Ads OAuth credential. It returned data immediately. The credential was genuinely expired for this one.

### Fix 5: Capabilities Catalog Stale Data

The `capability_catalog` DataTable had Google Ads API paths on v17 (sunset). The actual handler code was already on v23. This caused confusion — a previous session saw v17 in the catalog and reported it as the root cause of the Google Ads failure, which was wrong.

**Fix:** Inserted a corrected v23 entry. The catalog is documentation metadata, not used for routing.

### Fix 6: Credential Health Stale Data

The `credential_health` DataTable showed google_ads and wordpress as "unhealthy" — this was from the weekly E2E test (March 16, before fixes). Inserted corrected "healthy" entries with `source=live_test`.

### Fix 7: Registry Client Coverage Gaps

The drift detector (built later in this session) found 7 more domains with `client` set to a specific tenant instead of `all`: hubspot, salesforce, gong, gmail, google_drive, ollama, vercel. Plus `microsoft_ads` had no `handler_workflow_id`.

**Fix:** Inserted `client=all` rows for all 7. Set microsoft_ads handler to Marketing Ads handler (`6e9ooA3kc0zAPWyy`).

### Fix 8: VPS API Key Rotation

The VPS at `/opt/n8n-api-key-full.json` had a full-access API key with all scopes (including `workflow:delete`, `credential:delete`) sitting in plaintext. Per ADR-001 §8.1, rotated to a read-only key with only: `workflow:read`, `execution:read`, `execution:list`, `dataTableRow:read`, `dataTable:list`, `variable:list`.

---

## Part 2: Governance Infrastructure Built

### Problem This Solves

Before this session, any AI tool with the API key could modify any workflow at any time with no backup, no logging, no conflict detection, and no notification. This is how Google Ads stayed broken for weeks — no tool detected the failure, and each session that investigated either misdiagnosed it or claimed to fix it without actually testing.

### What Was Built

#### `get_platform_context` (handover action)
**Purpose:** Single call that gives any AI session everything it needs before doing work.
**Returns:** 6 governance rules, health status (28 healthy / 2 degraded / 3 down), recent changelog entries, verified state (healthy services, known issues, DataTable IDs), and gotchas.
**Rule:** Every session MUST call this before making any change.

#### `safe_modify_workflow` (handover action)
**Purpose:** The governed way to modify any workflow.
**What it does:**
1. GETs the current workflow JSON
2. Snapshots it to GitHub (`snapshots/{workflow_id}/{timestamp}.json`)
3. PUTs the modification
4. Re-registers webhooks if the workflow has webhook triggers
5. Logs to `platform_changelog` DataTable
6. Sends Slack notification to #n8n-alerts

**Rule:** Every workflow modification MUST go through this action. Never raw PUT.

#### `log_change` (handover action)
**Purpose:** Record non-workflow changes (DataTable inserts, variable updates, config changes).
**Rule:** Call this after any platform change that isn't a workflow modification.

#### `platform_changelog` DataTable (`kqKrSqKSsu8UbU89`)
**Purpose:** Audit trail of every platform change. Columns: timestamp, category, domain, summary, details, session_id.
**Variable:** `$vars.PLATFORM_CHANGELOG_TABLE_ID`

#### Daily Drift Detector (workflow `47iqwAKXzGrS4d1n`)
**Purpose:** Catches configuration drift before it causes failures.
**Schedule:** Daily 3am CT + on-demand via `/webhook/drift-check`
**Checks:**
- Registry entries with `client` not set to `all` (catches the google_ads scenario)
- Handler-type domains with empty `handler_workflow_id` (catches the wordpress scenario)
- Hardcoded URLs in Code nodes (catches Principle 1 violations)
- Stale credential health data (>7 days old)

**Alerts:** Critical drifts trigger Slack alert to #n8n-alerts.

#### Gateway Failure Alerting
**Purpose:** Catches silent routing failures in real-time.
**How:** When a domain returns `ok: false` 3 or more times within 5 minutes, fires a Slack alert to #n8n-alerts with domain, error type, client, and error message. Counter resets on success. Alert fires once per incident (no storms).
**Where:** Added to `Format Handler Response` Code node and new `Track Resolve Failure` Code node in the gateway.

#### Nightly Workflow + Schema Backup
**Purpose:** Version-controlled backup of all workflow definitions and DataTable schemas.
**What was added:** Modified the existing DataTable Backup workflow (`CAFbxMLIY2OjEpYH`) to also export:
- All workflow JSON to `exports/workflows/{workflow_id}.json`
- All DataTable schemas to `exports/schemas/{table_name}.json`

**Why schemas matter:** A workflow referencing a deleted or renamed DataTable column fails silently. The schema backup catches this.

### The 6 Rules (embedded in `get_platform_context`)

1. **Read before write.** Call `get_platform_context` before making any change.
2. **Use the safe path.** Modify workflows through `safe_modify_workflow`, not raw PUT.
3. **Log non-workflow changes.** Call `log_change` for DataTable inserts, variable updates, config changes.
4. **Run the audit after changes.** Call `run_audit` after any session that modifies workflows.
5. **Don't fix what isn't broken.** If `get_platform_context` shows a service as healthy, don't re-investigate.
6. **Update the verified state.** After fixing something, call `update_session_state` with the new verified state.

---

## Part 3: Architecture Decision (ADR-001)

**Full document:** `docs/ADR-001-platform-governance.md` on GitHub

**Decision:** Hybrid approach — Gateway enforces governance at write time, Git serves as the version-controlled record.

**Why not full GitOps:** Right long-term architecture, wrong for today. Requires AI tools to work through Git instead of the n8n API, adds a deployment step, and would halt forward progress during migration.

**Why not gateway-only:** Governance logic inside the system it governs is circular. If the handover handler breaks, governance disappears.

**The hybrid:** Gateway enforces snapshot + log + notify on every change. Git stores the snapshots and nightly exports. Rollback is: read snapshot from Git, apply via `safe_modify_workflow`. When the instance moves to self-hosted or exceeds 200+ workflows, the Git repo already has everything versioned for a CI/CD migration.

**API Key Model (§8.1):**
- Tier 1 (internal write): `$vars.N8N_INTERNAL_API_KEY` — inside n8n only
- Tier 2 (external read-only): `/opt/n8n-api-key.txt` on VPS — monitoring only
- Tier 3 (break-glass): n8n Cloud Settings > API — emergency only, rotate after use

**Failure Alerting (§8.2):** 3 failures per domain in 5 minutes → Slack #n8n-alerts.

**Backup Scope (§8.3):** Workflows + DataTable rows + DataTable schemas. 30-day retention.

**Alert Routing (§8.4):** Slack only. No PagerDuty. AI tools read alerts but don't auto-remediate.

---

## Part 4: What's Left (P2s for Next Session)

### P2-1: Google Suite Handler Monolith Split
**What:** The Google Suite handler has 16 APIs in one workflow with a 17K-char Code node. One bug breaks all 16 domains.
**Recommendation:** Split into smaller domain-specific handlers (Google Workspace, Social, CMS).
**Effort:** Large. Needs a fresh session with full context budget.
**Why it matters at scale:** When you're building hundreds of agents, each adding new API domains, the handler workflows need to be modular.

### P2-2: Gateway Latency — Cache Registry Data
**What:** Every gateway request makes 3+ internal HTTP calls to DataTables (registry lookup, action lookup, tenant config). No caching.
**Recommendation:** Cache registry + action map data in a Code node variable with 5-minute refresh.
**Effort:** Medium.
**Why it matters at scale:** With hundreds of agents making gateway calls, the HTTP overhead adds up.

### P2-3: Agent Error Handling
**What:** None of the 3 core agents (Demand Gen, Content Strategist, Data Analyst) have error handling. If a gateway call fails, the workflow crashes.
**Recommendation:** Add try/catch in every Code node that calls the gateway. Partial reports (some sources failed) are better than no reports.
**Pattern documented:** `docs/agent-best-practices.md` on GitHub.

---

## Part 5: Documentation Published to GitHub

All in `mishaal-cloud/n8n-ops` repo:

| File | Purpose |
|------|---------|
| `docs/ADR-001-platform-governance.md` | Architecture decision record — the plan |
| `docs/handovers/verified-state-2026-03-18.md` | Verified platform state — what's working, what's broken |
| `docs/DATATABLE-IDS-VERIFIED.md` | Canonical DataTable IDs (governing spec has stale ones) |
| `docs/BREAK-GLASS-KEY.md` | Emergency API key procedure |
| `docs/agent-best-practices.md` | Agent design patterns and checklist |
| `docs/runbooks/add-new-api.md` | Step-by-step: how to add a new API to the gateway |
| `docs/runbooks/debug-failing-domain.md` | Step-by-step: how to diagnose and fix a failing domain |
| `snapshots/` | Pre-change workflow snapshots (created by `safe_modify_workflow`) |

---

## Part 6: Known Gotchas

1. **Webhook re-registration required after API workflow updates.** Every PUT /workflows/{id} invalidates the webhook UUID. Must toggle OFF/ON. `safe_modify_workflow` does this automatically.

2. **Registry `client` field must be `all` for shared services.** If set to a specific client (e.g., `ascend`), requests from other clients silently fail with "No registry entry." This is what broke Google Ads.

3. **DataTable row DELETE not supported via n8n Cloud API.** You can only INSERT and READ. To fix stale entries, insert a corrected row and rely on the resolution logic to prefer the newest one (highest ID).

4. **Capabilities catalog may be stale.** It's documentation metadata, not used for routing. The actual API versions are in handler Code nodes. Always verify against handler code, not the catalog.

5. **Governing spec on GitHub has stale DataTable IDs.** The `DATATABLE-IDS-VERIFIED.md` file has the correct ones. Always check `$vars` at runtime.

6. **Build Dynamic Request passthrough has a body scoping bug.** It's been worked around (handler fallback logic prevents it from triggering), but the actual bug at line 30 should be fixed in a future session.

7. **E2E health data lags behind reality.** The weekly E2E test runs Mondays 8am CT. Between runs, the `credential_health` table may show stale data. Always verify with a live gateway call.

8. **n8n credential types must match exactly.** Using `httpBasicAuth` when the credential is `wordpressApi` returns "Credential does not exist." Check the actual type via the credentials API.

---

## Part 7: How the Next Session Should Start

```
1. Call handover.get_platform_context
2. Read the rules
3. Check health — is anything broken?
4. Check recent_changes — what happened since last session?
5. Check gotchas — what not to do
6. Then start working
```

If modifying workflows: use `safe_modify_workflow`. If modifying DataTables or variables: call `log_change`. If fixing something: call `update_session_state` afterward.

The platform will tell you what it needs. You just have to ask it first.
