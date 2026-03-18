# Agent Workflow Best Practices

**Last updated:** 2026-03-18
**Based on:** Live audit of 5 agent workflows on mmurawala.app.n8n.cloud

---

## Current Agent Inventory

| Agent | ID | Schedule | Status |
|-------|----|----------|--------|
| Demand Gen Manager | bagVDDbXxmwTg5P1 | Daily 7am CT | Active |
| Content Strategist | glYqXUNxp98d5JEh | Mon 8am CT | Active |
| Data Analyst | JxeVdBljlv9HJ48p | Mon 9am CT | Active |
| OAuth Auto-Healer | iERXHDDaJ0V3w8RM | Daily 7am + Sun 6am CT | Active |
| VPS Bridge | CeCnsN9yRb5X8pie | On-demand | Active |

## Required Pattern for Every Agent

Every agent workflow MUST follow this structure:

```
Schedule Trigger ──┐
                   ├──> Core Logic (Code) ──> Format Output ──> Deliver Report
Webhook Trigger ───┘         │
                         Error Branch ──> Error Handler
```

### 1. Dual Triggers

Every agent must have BOTH:
- **Schedule Trigger** — the automated run (daily, weekly, etc.)
- **Webhook Trigger** — for on-demand execution and testing

This follows Governing Spec Principle 5 (Flexible): workflows support multiple execution paths.

### 2. Error Handling (MISSING TODAY)

Current gap: none of the 3 core agents have error handling. If a gateway call fails, the entire workflow crashes.

**Required pattern:**
```javascript
// In every Code node that calls the gateway:
try {
  const result = await this.helpers.httpRequest({
    method: 'POST',
    url: $vars.N8N_HOST + '/webhook/handler-marketing-ads',
    headers: {'x-handler-secret': $vars.GW_HANDLER_INTERNAL_SECRET},
    body: JSON.stringify(payload)
  });
  if (!result.ok) {
    // Log the failure, continue with partial data
    failedSources.push({domain, error: result.error});
  } else {
    data[domain] = result.data;
  }
} catch (e) {
  // Gateway unreachable — log and continue
  failedSources.push({domain, error: e.message});
}
```

**Key principle:** Partial reports are better than no reports. If Google Ads is down, the agent should still deliver GA4 + Apollo data with a note that Google Ads was unavailable.

### 3. Gateway Calls via $vars

Never hardcode gateway URLs. Always use:
```javascript
const N8N_HOST = $vars.N8N_HOST;
const HANDLER_SECRET = $vars.GW_HANDLER_INTERNAL_SECRET;
```

All 3 core agents are now clean on this (fixed 2026-03-18).

### 4. Workflow Description Sticky Note

Every agent must have a sticky note containing:
- Agent purpose
- Schedule
- Data sources (which gateway domains/actions it calls)
- Delivery channels (Slack, email, DataTable)
- Owner/maintainer

All 3 core agents have this (P5 fix from handover doc).

### 5. Memory and State

Agents that need cross-run context should use:
- **agent_memory DataTable** (TmUGB90Wg1quE9Up) — shared observations and insights
- **agent_tasks DataTable** (wGiRrwpDnJ3lQUlT) — task queue for inter-agent coordination

Write to these tables via the n8n DataTable API, not direct node access (per Known Bug #2).

### 6. Output Format

Every agent report should include:
```json
{
  "agent": "Demand Gen Manager",
  "run_at": "2026-03-18T12:00:00Z",
  "status": "partial",
  "data": { ... },
  "failed_sources": [{"domain": "google_ads", "error": "..."}],
  "recommendations": [...]
}
```

The `status` field should be `complete` (all sources returned), `partial` (some failed), or `failed` (no data).

### 7. Delivery

Agents should deliver reports to Slack via the Google Suite handler:
```javascript
await this.helpers.httpRequest({
  method: 'POST',
  url: $vars.N8N_HOST + '/webhook/handler-google-suite',
  headers: {'x-handler-secret': $vars.GW_HANDLER_INTERNAL_SECRET},
  body: JSON.stringify({
    domain: 'slack', action: 'post_message', client: 'ascend',
    params: { channel: '#agent-reports', text: report }
  })
});
```

### 8. Scaling to Hundreds of Agents

When building new agents:
- **One agent = one workflow.** Don't combine multiple agents into one workflow.
- **Use the Task Orchestrator** (J3rRZIm7Qa5XkqrG) for multi-agent coordination.
- **Register in agent_tasks DataTable** so the orchestrator knows about it.
- **Follow the naming convention:** emoji + "Agent:" + name (e.g., "📈 Agent: Revenue Tracker").
- **Use safe_modify_workflow** for any changes to existing agents.

## Checklist for New Agent Development

- [ ] Dual triggers (schedule + webhook)
- [ ] Error handling with graceful degradation
- [ ] All URLs from $vars (zero hardcoding)
- [ ] Sticky note with purpose, schedule, data sources
- [ ] Output format includes status + failed_sources
- [ ] Registered in agent_tasks DataTable
- [ ] Tested via webhook trigger before activating schedule
- [ ] Logged in platform_changelog via log_change
