# n8n-ops

Operational infrastructure for the Ascend GTM n8n Cloud instance.

## Purpose

This repo ensures **every AI session** (Claude, ChatGPT, Gemini, Cursor) starts with verified connectivity to the n8n infrastructure. No guessing auth headers, webhook paths, or table IDs.

## Runbook: Starting a Session

Every session follows this exact sequence:

### 1. Run Preflight

```bash
python3 bootstrap/preflight.py https://mmurawala.app.n8n.cloud <N8N_API_KEY>
```

This validates:
- n8n REST API auth (X-N8N-API-KEY header)
- Session config webhook reachability
- All critical workflows active
- All DataTables accessible
- E2E test webhook reachable

**If preflight fails, stop. Fix the failure before doing any work.**

### 2. Call Session Config

```bash
curl -s -X POST https://mmurawala.app.n8n.cloud/webhook/session-config \
  -H "X-N8N-API-KEY: <key>" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

The response contains everything needed:
- **auth_patterns**: Which header to use for each system (n8n API, gateway, MCP, handlers)
- **webhook_paths**: Every active webhook endpoint, dynamically read from live workflows
- **critical_workflows**: IDs and status of key infrastructure workflows
- **table_ids** + **table_status**: DataTable IDs and accessibility
- **e2e_notes**: How to trigger and poll E2E test results
- **phase_status**: Current project phase progress
- **shell_constraints**: Container shell is dash (not bash) — use python3

### 3. Never Guess

- **Auth headers**: Read from `auth_patterns` in session config
- **Webhook paths**: Read from `webhook_paths` in session config
- **Table IDs**: Read from `table_ids` in session config
- **Workflow IDs**: Read from `critical_workflows` in session config

## Key Auth Patterns

| System | Header | Notes |
|--------|--------|-------|
| n8n REST API | `X-N8N-API-KEY` | NEVER use `Authorization: Bearer` |
| Gateway V2 | `x-api-key` | Master key or per-client key |
| Internal handlers | `x-internal-secret` | Workflow-to-workflow calls |
| MCP gateway | `Authorization: Bearer` | MCP Server Trigger auth |

## Shell Constraints

The Claude.ai bash_tool container runs `/bin/sh` (dash), NOT bash. This means:
- No `source` command (use `.` or avoid entirely)
- No `declare -A` (associative arrays)
- No bash-specific syntax
- **Always use python3** for n8n API interaction

## Repo Structure

```
bootstrap/
  preflight.py      # Preflight validation script
  config.json       # Static fallback config (not primary — use live endpoint)
  README.md         # This file
workflows/
  session-config.json  # Exported Session Bootstrap Config workflow
logs/               # Session logs (gitignored)
docs/
  architecture.md   # Infrastructure architecture reference
  known-issues.md   # Documented bugs and workarounds
```
