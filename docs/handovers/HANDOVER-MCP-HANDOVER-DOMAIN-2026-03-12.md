# MCP Handover Domain — Platform Ops Tools

**Date:** 2026-03-12
**Operating Mode:** Non-stop execution
**Skill:** n8n-handover-framework (load before starting)
**Governing Spec:** https://raw.githubusercontent.com/mishaal-cloud/n8n-ops/main/docs/governing-spec.md

## Success Criteria

- [ ] `handover` domain registered in api_registry_v2 with handler routing
- [ ] 7 actions registered in action_map_v2 and functional
- [ ] Handler workflow deployed, active, and reachable via gateway
- [ ] All 7 MCP tools callable from claude.ai via the Ascend MCP Gateway
- [ ] All 7 actions pass E2E test via gateway orchestrate-v2 endpoint
- [ ] E2E test manifest updated with handover domain test cases
- [ ] Zero governing spec violations in handler workflow

## Constraints

**ABSOLUTE** (zero exceptions):
- DO NOT modify Gateway v2 orchestrator (m3BWxESfNCs1ccws) routing logic — the gateway already discovers handler domains from the registry
- DO NOT modify any existing handler workflow (GitHub, Google Suite, etc.)
- DO NOT hardcode any URLs, IDs, secrets, or tenant names in the handler
- DO NOT store session state in n8n variables — use DataTable

**SOFT** (may violate with documented justification):
- Prefer existing DataTables over creating new ones when schema fits
- Prefer GitHub raw content fetch over storing docs in DataTables

## Key Resources

### Workflow IDs

| Workflow | ID | Status | Notes |
|----------|----|--------|-------|
| Gateway v2 (PRIMARY) | m3BWxESfNCs1ccws | Active | DO NOT MODIFY — routes to handler via registry |
| GitHub Handler | eZlzhG7YHsdWnArf | Active | Reference pattern for handler architecture |
| Google Suite Handler | RKoOuaqcnbSYfLLp | Active | Reference pattern for multi-action handler |
| Handover Handler | [TO BE CREATED] | — | New workflow this session builds |

### DataTables

| Table | ID | Variable | Purpose |
|-------|----|----------|---------|
| api_registry_v2 | vJ9KqqQsohwv0ZzM | REGISTRY_V2_API_TABLE_ID | Domain registration — add handover domain here |
| action_map_v2 | sGzFu49QUE6vBmxO | REGISTRY_V2_ACTION_TABLE_ID | Action registration — add 7 actions here |
| e2e_test_manifest | 2pg9Nm0o7Jd6kU1m | E2E_MANIFEST_TABLE_ID | Add test cases for handover actions |
| session_state | [TO BE CREATED OR EXISTING] | — | Session state persistence for get/update_session_state |

### Variables

| Variable | Purpose |
|----------|---------|
| N8N_HOST | Instance base URL |
| N8N_INTERNAL_API_KEY | API key for self-calls |
| GW_HANDLER_INTERNAL_SECRET | Handler auth secret |
| REGISTRY_V2_API_TABLE_ID | api_registry table ID |
| REGISTRY_V2_ACTION_TABLE_ID | action_map table ID |

### GitHub Repository

| Item | Value |
|------|-------|
| Owner | mishaal-cloud |
| Repo | n8n-ops |
| Governing spec path | docs/governing-spec.md |
| Handover template path | docs/skills/n8n-handover-framework/templates/handover-doc-template.md |
| Skill version path | docs/skills/n8n-handover-framework/VERSION |

### Current Registry Schema

**api_registry_v2 columns:** api_name, client, category, base_url, auth_type, auth_header, auth_prefix, credential_var, credential_id, credential_type, handler_workflow_id, metadata, rate_limit_rpm, enabled, version

**action_map_v2 columns:** api_name, action, method, endpoint, body_mode, description, enabled

**Current state:** 274 actions across 35 domains. The `handover` domain will be domain #36.

## Items

### Item #1: Create Handover Handler Workflow (HIGH)

**Problem:** The handover framework's operational tools (spec retrieval, preflight, audit, session state) are currently only available as local scripts within Claude's container. They need to be accessible from any AI frontend via MCP.

**Scope:** Create one new workflow: `Gateway: Handover`. Follow the same architectural pattern as `Gateway: GitHub` (eZlzhG7YHsdWnArf) — webhook trigger + execute workflow trigger, normalize input with internal secret auth, action-based routing via Code node, and formatted response.

**Implementation:**

1. **Study the GitHub handler pattern.** Fetch workflow eZlzhG7YHsdWnArf via API. The architecture is: Webhook Trigger → Normalize Input (auth check) → Build API Request (action router) → Execute → Format Response → Respond. Replicate this exact pattern.

2. **Build the handler workflow** with these nodes:
   - `Webhook Trigger` — path: `handler-handover`, method: POST, webhookId: `handover-handler-v1`
   - `Execute Workflow Trigger` — for direct gateway calls
   - `Normalize Input` — verify `x-handler-secret` matches `$vars.GW_HANDLER_INTERNAL_SECRET`. Reject unauthorized calls with 403.
   - `Action Router` (Code node) — switch on `action` field. Route to appropriate logic per action.
   - **Action logic nodes** (see Item #2 for each action's implementation)
   - `Format Response` — standardize output format
   - `Respond Success` / `Respond Error` — webhook responses

3. **All config via $vars.** The handler must read N8N_HOST, N8N_INTERNAL_API_KEY, GW_HANDLER_INTERNAL_SECRET from variables. Zero hardcoded values.

4. **Activate and test** webhook is reachable.

**Test Cases:**
1. POST to `/webhook/handler-handover` without secret → 403 Unauthorized
2. POST with correct secret + `action: get_governing_spec` → Returns spec content
3. Call via Execute Workflow Trigger with same payload → Same result

**Acceptance Criteria:**
- [ ] Workflow created and active
- [ ] Auth gate rejects unauthorized calls
- [ ] Both trigger paths (webhook + execute workflow) work
- [ ] Zero hardcoded values — audit.py passes clean

---

### Item #2: Implement 7 MCP Actions (HIGH)

**Problem:** Each action needs specific logic inside the handler's Action Router. These are the operational tools that make the handover framework callable from any AI frontend.

**Scope:** Implement all 7 actions within the handler workflow's Action Router Code node (or sub-nodes if complexity warrants).

**Actions to implement:**

#### Action 2a: `get_governing_spec`
- Fetches `docs/governing-spec.md` from GitHub via the GitHub handler (or direct API call to raw.githubusercontent.com)
- Returns: full spec content as text
- No params required

#### Action 2b: `get_handover_template`
- Fetches `docs/skills/n8n-handover-framework/templates/handover-doc-template.md` from GitHub
- Returns: template content as text
- No params required

#### Action 2c: `run_preflight`
- Executes preflight checks against the live n8n instance: API connectivity, workflow count, variable count, session-config webhook
- Uses the same logic as `scripts/preflight.py` but implemented in JavaScript within the Code node
- Returns: JSON with pass/fail per check
- No params required

#### Action 2d: `run_audit`
- Fetches one or more workflows by ID, scans Code nodes for governing spec violations
- Uses the same logic as `scripts/audit.py` but in JavaScript
- Params: `{ workflow_ids: ["id1", "id2"] }` or `{ all: true }` for full scan
- Returns: JSON with violations grouped by severity

#### Action 2e: `get_session_state`
- Reads session state from a DataTable (or GitHub file)
- Params: `{ session_id: "..." }` — optional, returns latest if omitted
- Returns: JSON session state object

#### Action 2f: `update_session_state`
- Writes/updates session state to a DataTable
- Params: `{ session_id: "...", state: { ... } }` — full state object
- Returns: confirmation with row ID

#### Action 2g: `get_skill_version`
- Fetches VERSION file from GitHub + reads SKILL.md description
- Returns: `{ version: "1.0.0", description: "...", last_updated: "..." }`
- No params required

**Test Cases:**
1. `get_governing_spec` → Returns markdown string containing "Core Design Principles"
2. `get_handover_template` → Returns markdown string containing "Governing Spec:"
3. `run_preflight` → Returns JSON with `api_connectivity.status: "PASS"`
4. `run_audit` with gateway ID m3BWxESfNCs1ccws → Returns violations array (we know it has 5 from earlier)
5. `get_session_state` with no session_id → Returns empty or latest state
6. `update_session_state` with test payload → Returns confirmation, then `get_session_state` returns same payload
7. `get_skill_version` → Returns `{ version: "1.0.0" }`

**Acceptance Criteria:**
- [ ] All 7 actions return expected results
- [ ] Error handling: invalid action returns clear error message with available actions list
- [ ] Error handling: each action handles failures gracefully (GitHub unreachable, workflow not found, etc.)
- [ ] All GitHub fetches use `$vars.N8N_HOST` or derived URLs — no hardcoded repo paths in Code nodes (repo owner/name can be in a variable or passed as handler_workflow metadata)

---

### Item #3: Register Domain and Actions in Registry (HIGH)

**Problem:** The gateway discovers domains and actions from the registry DataTables. The handover domain needs to be registered for the gateway to route to it.

**Scope:** Insert rows into api_registry_v2 and action_map_v2.

**Implementation:**

1. **Insert api_registry_v2 row:**

```json
{
  "api_name": "handover",
  "client": "all",
  "category": "platform_ops",
  "base_url": "",
  "auth_type": "handler",
  "auth_header": "",
  "auth_prefix": "",
  "credential_var": "",
  "credential_id": "",
  "credential_type": "",
  "handler_workflow_id": "[NEW WORKFLOW ID]",
  "metadata": "{\"github_owner\":\"mishaal-cloud\",\"github_repo\":\"n8n-ops\"}",
  "rate_limit_rpm": 30,
  "enabled": true,
  "version": 1
}
```

2. **Insert 7 action_map_v2 rows:**

| api_name | action | method | endpoint | body_mode | description | enabled |
|----------|--------|--------|----------|-----------|-------------|---------|
| handover | get_governing_spec | POST | /handler | handler | Fetch latest governing spec from GitHub | true |
| handover | get_handover_template | POST | /handler | handler | Fetch lean handover doc template from GitHub | true |
| handover | run_preflight | POST | /handler | handler | Validate n8n instance connectivity and configuration | true |
| handover | run_audit | POST | /handler | handler | Scan workflows for governing spec violations | true |
| handover | get_session_state | POST | /handler | handler | Retrieve session state for multi-session continuity | true |
| handover | update_session_state | POST | /handler | handler | Write session state for multi-session continuity | true |
| handover | get_skill_version | POST | /handler | handler | Get current handover framework skill version | true |

3. **Verify** the gateway can discover and route to the new domain by calling orchestrate-v2 with `domain: "handover"`.

**Test Cases:**
1. Gateway call: `{domain: "handover", action: "get_governing_spec", client: "ascend"}` → Returns spec
2. Gateway call: `{domain: "handover", action: "invalid_action", client: "ascend"}` → Returns error with available actions
3. MCP call from claude.ai: Ask the Ascend MCP Gateway to "get the governing spec" → Returns spec content

**Acceptance Criteria:**
- [ ] api_registry_v2 has handover domain row
- [ ] action_map_v2 has all 7 action rows
- [ ] Gateway routes to handler successfully
- [ ] MCP tools list includes handover actions

---

### Item #4: Create Session State DataTable (MEDIUM)

**Problem:** `get_session_state` and `update_session_state` need persistent storage. DataTables are the correct storage for this — cloud-native, API-accessible, no external dependencies.

**Scope:** Create one new DataTable for session state persistence.

**Implementation:**

1. **Create DataTable** via API: `POST /data-tables`
   - Name: `session_state`
   - Columns: `session_id` (string), `model` (string), `state` (string — JSON blob), `updated_at` (string — ISO timestamp)

2. **Create n8n variable:** `SESSION_STATE_TABLE_ID` pointing to the new table ID.

3. **Handler reads/writes** using this variable, not a hardcoded ID.

**Test Cases:**
1. Write a test session state → Read it back → Data matches
2. Update the same session_id → Read back → Updated data returned
3. Read non-existent session_id → Returns empty/null cleanly

**Acceptance Criteria:**
- [ ] DataTable created
- [ ] Variable created and points to correct ID
- [ ] Handler uses variable, not hardcoded ID

---

### Item #5: Add E2E Test Cases to Manifest (MEDIUM)

**Problem:** The E2E test suite needs test cases for the handover domain to include it in weekly regression testing.

**Scope:** Insert rows into e2e_test_manifest DataTable for each handover action.

**Implementation:**

Insert 7 rows into e2e_test_manifest (2pg9Nm0o7Jd6kU1m), one per action. Follow the existing manifest schema — check a few existing rows to match the column structure exactly before inserting.

**Test Cases:**
1. Trigger E2E test suite → Handover domain actions appear in results
2. All 7 handover actions pass in E2E run

**Acceptance Criteria:**
- [ ] 7 test manifest rows inserted
- [ ] E2E suite discovers and tests handover actions
- [ ] All 7 pass

---

### Item #6: Update Governing Spec (LOW)

**Problem:** The governing spec in GitHub doesn't document the handover domain yet. It needs to be updated with the new workflow ID, DataTable, and actions.

**Scope:** Update `docs/governing-spec.md` in GitHub via the GitHub handler.

**Implementation:**

1. Add the handover handler to the Gateway Architecture > Core Components table
2. Add session_state DataTable to the Registry DataTables table
3. Add SESSION_STATE_TABLE_ID to the operational config
4. Add a brief "Handover Domain" section describing the 7 MCP tools

Push via the GitHub handler's `create_or_update_file` action.

**Test Cases:**
1. Fetch governing spec via `get_governing_spec` action → Contains handover domain documentation

**Acceptance Criteria:**
- [ ] Governing spec updated in GitHub
- [ ] Handover domain documented with workflow ID, actions, and purpose

---

### Item #7: Build API Skill Sync Workflow (LOW)

**Problem:** When skill files change in GitHub, the Claude API skill needs to be updated automatically. Currently this is manual.

**Scope:** Create a new n8n workflow that syncs skill files from GitHub to the Claude API /v1/skills endpoint.

**Implementation:**

1. **Trigger:** Schedule (daily) or GitHub webhook (on push to `docs/skills/**`)
2. **Step 1:** Fetch all files from `docs/skills/n8n-handover-framework/` via GitHub handler `get_tree` + `get_file` actions
3. **Step 2:** Check if skill exists via `GET /v1/skills` (needs Anthropic API key in a variable)
4. **Step 3:** If exists → `POST /v1/skills/{id}/versions` with updated files. If not → `POST /v1/skills` to create.
5. **Step 4:** Store returned skill_id in `$vars.HANDOVER_SKILL_ID`

**Prerequisite:** This requires an Anthropic API key with workspace access stored in an n8n variable. If one doesn't exist, create the variable placeholder and document the manual step of adding the key value.

**Test Cases:**
1. Manual trigger → Skill created/updated in Claude API
2. Verify skill_id stored in variable
3. API call with `container.skills` referencing the skill_id → Skill loads

**Acceptance Criteria:**
- [ ] Workflow created and functional
- [ ] Skill synced to Claude API
- [ ] skill_id stored in $vars
- [ ] OR: If API key not available, workflow is built and ready — just needs the key added

## Execution Order

1. Bootstrap (skill handles this — preflight, prefetch, state file)
2. Item #1 — Handler workflow (everything depends on this)
3. Item #2 — Action implementations (core value delivery)
4. Item #4 — Session state DataTable (needed by actions 2e/2f)
5. Item #3 — Registry entries (makes it routable — depends on #1 being deployed)
6. Item #5 — E2E manifest (depends on #3 being registered)
7. Item #6 — Governing spec update (depends on all above being done)
8. Item #7 — API skill sync (independent, lowest priority)
9. After all items: Full validation via audit.py + E2E test run
10. Produce exit artifacts (skill handles this)
