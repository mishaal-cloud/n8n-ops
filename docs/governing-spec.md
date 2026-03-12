# n8n Cloud Platform Governing Spec

**Version:** 1.0.0
**Last Updated:** 2026-03-12
**Scope:** All workflows, DataTables, variables, and configurations on mmurawala.app.n8n.cloud

---

## Core Design Principles

Every change to this instance must satisfy ALL of these principles. No exceptions without documented justification.

### Principle 1: Zero Hardcoding

No hardcoded values that could change between environments. All instance-specific values must be read from `$vars` (n8n variables) or DataTables at runtime.

**Applies to:** URLs, API keys, DataTable IDs, credential IDs, tenant/client names, webhook paths, domain names in filter sets, port numbers, email addresses used in routing logic.

**How to verify:** Search Code node for literal strings matching `*.app.n8n.cloud`, `data-tables/[ID]`, API key patterns (`eyJ`, `pat-`, `sk-`), and tenant names (`kahuna`, `ascend`, `codiac`).

**Canonical variable resolution pattern:**
```javascript
const BASE = $vars.N8N_HOST; // not "https://mmurawala.app.n8n.cloud"
const KEY = $vars.N8N_INTERNAL_API_KEY; // not the literal key
const TABLE = $vars.REGISTRY_V2_ACTION_TABLE_ID; // not the literal ID
```

### Principle 2: Frontend-Agnostic

The gateway and all automation workflows must work identically regardless of which AI frontend (Claude, ChatGPT, Gemini, Perplexity, custom) sends the request. No frontend-specific logic in shared infrastructure.

### Principle 3: Multi-Client Ready

All workflows that serve multiple clients must read tenant configuration from the `tenant_config` DataTable, not from hardcoded client maps. Client-specific behavior is driven by config, not code branches.

**Tenant Config DataTable ID:** Stored in `$vars.TENANT_CONFIG_TABLE_ID`

### Principle 4: Scalable

New APIs, clients, and actions are added through DataTable rows (registry entries), not code changes. The gateway router, health monitor, and E2E test suite discover actions from the registry — they do not maintain independent lists.

### Principle 5: Flexible

Workflows must support multiple execution paths (webhook trigger, Execute Workflow trigger, MCP trigger) without modification. Handler sub-workflows accept input from any caller.

### Principle 6: Secure

- All secrets in `$vars`, never in Code nodes
- Handler sub-workflows verify `x-handler-secret` before executing
- OAuth credentials use proper refresh flows, not hardcoded tokens
- No HTTP 502 responses from webhooks (Cloudflare replaces the body)
- Internal secret: `$vars.GW_HANDLER_INTERNAL_SECRET`

### Principle 7: Simple

Prefer fewer nodes over more nodes. Prefer Code nodes with clear logic over complex node chains. Every Code node must have a header comment explaining its purpose (runbook header).

---

## Gateway Architecture (v2)

### Core Components

| Component | Workflow ID | Purpose |
|-----------|------------|---------|
| Gateway v2 (PRIMARY) | m3BWxESfNCs1ccws | Main orchestrator — webhook intake → auth → route → execute → respond |
| Gateway v1 (BACKUP) | WQCwEDVb2L6Xkuwd | Deactivated legacy gateway. Do not modify. |
| Health Monitor | umagu3RIeVRdpn17 | Periodic health checks against registered actions |
| AI Cost Tracker | g2tKvOZTS2HL8ch6 | Logs AI API costs |
| E2E Test Suite | SHHsZIpL2OuLcRhT | Weekly full regression (Monday 8am CT) |
| DataTable Backup | CAFbxMLIY2OjEpYH | Daily backup to GitHub |
| Google Suite Handler | RKoOuaqcnbSYfLLp | 7-way switch for Google + Slack + Notion + Outlook |
| GitHub Handler | eZlzhG7YHsdWnArf | GitHub API operations |
| Task Orchestrator | J3rRZIm7Qa5XkqrG | Webhook /webhook/task-orchestrator |

### Registry DataTables

| Table | Variable | Purpose |
|-------|----------|---------|
| api_registry_v2 | REGISTRY_V2_API_TABLE_ID (s4QNOZysL8K5QAEK) | Domain → credential mapping |
| action_map_v2 | REGISTRY_V2_ACTION_TABLE_ID (UFFQp3heMFys4gPB) | Domain + action → route type, test config |
| health_test_config | HEALTH_TEST_CONFIG_TABLE_ID (MmlcQmCuoz3M33pD) | Health check parameters |
| e2e_test_manifest | E2E_MANIFEST_TABLE_ID (2pg9Nm0o7Jd6kU1m) | 242 test cases |
| tenant_config | TENANT_CONFIG_TABLE_ID (NSkfB6vp9d4lcNii) | Client configuration |
| credential_health | CREDENTIAL_HEALTH_TABLE_ID (wCfdPfENLbe1jvc2) | Credential expiry tracking |
| ai_cost_log | AI_COST_TRACKER_TABLE_ID (t4tTjYDIkNYdfhdh) | AI API cost logging |
| task_queue | TASK_QUEUE_TABLE_ID (Q8a5XCTmoGhYIIDh) | Async task queue |

### Gateway Request Format

```json
POST /webhook/orchestrate-v2
{
  "domain": "hubspot",
  "action": "get_contacts",
  "client": "kahuna",
  "params": {
    "limit": 10
  }
}
```

### Routing Types

- **passthrough**: Gateway calls the API directly using stored credentials (API-key services)
- **handler**: Gateway delegates to a sub-workflow via Execute Workflow or HTTP Request to handler webhook

### Handler Authentication (TECH_DEBT_001)

Execute Workflow node has a known bug: "Unexpected end of JSON input" when passing complex payloads. Workaround: HTTP Request to handler webhooks with internal secret header.

```
Header: x-handler-secret: [value of $vars.GW_HANDLER_INTERNAL_SECRET]
```

This workaround must maintain security parity with Execute Workflow. Monitor workflow xdwUAWFiaT1gAmCU tracks this weekly.

---

## Known Platform Bugs

### Bug 1: HTTP Request jsonBody IF-chain Bug

**Issue:** HTTP Request node `jsonBody` expressions don't evaluate downstream of IF node chains (#15996, #18181).

**Workaround:** Use Code node + `this.helpers.httpRequest()` instead of HTTP Request node when downstream of IF chains.

### Bug 2: DataTable GET Node Bug

**Issue:** DataTable GET node returns incorrect results in certain configurations.

**Workaround:** Use HTTP Request to self-API (`$vars.N8N_HOST/api/v1/data-tables/[ID]/rows`) instead of native DataTable node.

### Bug 3: Execute Workflow "Unexpected end of JSON input" (TECH_DEBT_001)

**Issue:** Execute Workflow node fails with complex JSON payloads.

**Workaround:** HTTP Request to handler webhook with internal secret. See Handler Authentication above.

### Bug 4: Action Lookup Limit

**Issue:** DataTable API GET max is `limit=250`, not 200. Earlier implementations used 200 and missed rows.

**Fix:** All DataTable reads must use `limit=250`.

### Bug 5: HTTP 502 from Webhooks

**Issue:** Cloudflare replaces the response body on HTTP 502 from n8n webhooks.

**Fix:** Never return HTTP 502 from webhook-triggered workflows. Use 500 or custom error codes.

---

## MCP Access

| Platform | Method | Endpoint |
|----------|--------|----------|
| Claude.ai | First-party OAuth | Instance MCP at /mcp-server/http |
| ChatGPT | Instance MCP OAuth | App "Ascend Gateway", client_id 8644db3d-... |
| Claude Desktop | mcp-remote Bearer | MCP Server Trigger at /mcp/ai-gateway/sse |
| Perplexity macOS | mcp-remote Bearer | MCP Server Trigger at /mcp/ai-gateway/sse |
| Gemini | Not supported | No MCP support |

---

## Credential Management

### Credential Types

**Category A — Permanent (set once):** HubSpot PAT, Apollo, SEMrush, Gong, DeepSeek, OpenRouter, Groq API keys, WordPress Basic Auth.

**Category B — OAuth2 (periodic refresh):** Google (6-month inactivity timeout), Microsoft (90-day inactivity), Salesforce, LinkedIn, Slack.

### Key Credentials

| Service | Credential ID | Type | Notes |
|---------|--------------|------|-------|
| Google Ads | euQhyKgs68cdwZvF | OAuth2 | API v23+ only |
| GA4 | cYYciNg6xMKkfDMS | OAuth2 | Lacks analytics.edit scope |
| GSC | xPaCXKzEeh2H2nzO | OAuth2 | |
| Gmail | 0qXbdYRtwneXvwEO | OAuth2 | |
| HubSpot | fARJGurlZcFaVPDV | httpHeaderAuth | KAHUNA_HUBSPOT_HEADER_AUTH |
| Salesforce | WlkDj04MLYU1SyVD | OAuth2 | |
| WordPress (Kahuna) | jIBRhrEDzCgVi5ru | Basic Auth | |
| GTM | pfZZYFHJ55vdK6pf | OAuth2 | tagmanager.edit.containers + analytics.edit |
| GitHub | P5dXGKMH1H5qsTkU | githubApi | |

### Broken/Deprecated Credentials

- ~~n897XkdylqY96hx8~~ — Old kahuna_hubspot_prod. DELETED from UI 2026-03-11.
- HubSpot `hubspotAppToken` type — Broken. Always use `httpHeaderAuth` with cred fARJGurlZcFaVPDV.

---

## Client-Specific Configuration

### Kahuna

| Resource | Value |
|----------|-------|
| Google Ads customer_id | 4320252036 |
| GA4 property_id | 273714189 |
| GSC property | kahunaworkforce.com |
| Ads MCC | 9242618149 |
| GTM Container | GTM-NFPWVVL |

---

## Operational Rules

1. **Error Protocol:** FULL STOP on any error. Read official docs → search GitHub issues → try 3 documented fixes → workaround only with evidence of platform bug + security parity + monitoring + revert plan.

2. **Documentation Mandate:** Before using ANY tool, API, or connector — read its latest official docs first.

3. **Manual Work Rule:** Never assign manual n8n UI tasks to the operator unless there is zero programmatic path.

4. **DataTable API Rules:** POST /rows {data:[...]} for insert. GET /rows?limit=250 for reads (max 250). No PATCH/DELETE/column-add via API.

5. **Webhook Re-registration:** After API workflow updates, UI toggle OFF/ON is required to re-register webhooks (webhookId UUID binding).

6. **Google Ads API:** v23+ only. v17-v19 sunset. Always verify current version before making calls.

7. **GTM State:** V55 published 2026-03-04. Clean: 16 tags, 15 triggers, 30 variables. mishaal@ascendgtm.net is Administrator.
