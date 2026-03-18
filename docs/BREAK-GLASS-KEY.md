# Break-Glass API Key Procedure

**ADR-001 Section 8.1 — Three-Tier Key Model**

## When to Use

ONLY when the gateway or handover handler is broken and cannot self-repair through `safe_modify_workflow`. This is the emergency escape hatch.

## Key Location

The full-access API key (Tier 3) is stored in n8n Cloud Settings > API. It is labeled with the creation date. It is NOT stored on the VPS or in any file.

## Procedure

1. Go to n8n Cloud Settings > API
2. Find the full-access key
3. Use it to fix the broken handler/gateway
4. After fix is confirmed, rotate the key (delete and recreate)
5. Log the break-glass usage to platform_changelog via `log_change`

## Key Tiers

| Tier | Purpose | Location | Scopes |
|------|---------|----------|--------|
| 1 | Internal writes | `$vars.N8N_INTERNAL_API_KEY` (inside n8n) | All |
| 2 | VPS monitoring | `/opt/n8n-api-key.txt` on VPS | Read-only |
| 3 | Break-glass | n8n Cloud Settings > API (UI only) | All |

## VPS Read-Only Key Scopes

The VPS key can ONLY:
- Read workflows and executions
- Read DataTable rows
- List variables (values masked)
- List tags

It CANNOT modify workflows, DataTables, variables, or credentials.

**Last rotated:** 2026-03-18
