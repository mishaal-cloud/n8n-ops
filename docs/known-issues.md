# Known Issues

## Active Bugs

### TECH_DEBT_001: Execute Workflow Node Crash
- **Error**: "Unexpected end of JSON input" in getWorkflowInfo
- **Platform**: n8n Cloud
- **Workaround**: HTTP Request to handler webhooks with internal secret (`x-internal-secret` header)
- **Monitor**: Workflow `xdwUAWFiaT1gAmCU` runs weekly auto-test
- **Revert plan**: On fix, revert Call nodes to Execute Workflow, remove webhook infra from 4 handlers

### HTTP Request Node jsonBody Expression Bug
- **Error**: jsonBody expressions don't evaluate downstream of IF node chains
- **GitHub issues**: #15996, #18181
- **Workaround**: Code node + `this.helpers.httpRequest()` instead of HTTP Request node
- **Impact**: Any workflow with IF → HTTP Request chain using dynamic JSON body

### Webhook Re-registration After API Update
- **Behavior**: After PUT /workflows/{id}, webhooks may not re-register immediately
- **Workaround**: Wait 15-20 seconds after update before testing webhook
- **Alternative**: Deactivate, update, reactivate (most reliable sequence)

### Never Return HTTP 502 From Webhook
- **Behavior**: Cloudflare replaces the response body on 502
- **Impact**: Error details lost if webhook returns 502 status
- **Solution**: Always return 400/404/500 with structured error body, never 502

## Container Environment

### Shell is dash, not bash
- **Path**: /bin/sh → dash
- **Impact**: `source`, `declare -A`, bash arrays all fail silently
- **Solution**: Use python3 for all n8n API interaction
- **Bash exists at**: /usr/bin/bash (but not default)

## Resolved Issues

### GA4 Admin API 403
- **Cause**: GA4 credential lacks `analytics.edit` scope
- **Status**: Known limitation, GTM credential has the edit scopes instead

### DataTable API Row Limit
- **Was**: Hardcoded to 200 in several workflows
- **Fix**: Changed to 250 (actual max) across V2 gateway, E2E suite, and MCP gateway
