# Runbook: Add a New API to the Gateway

## Prerequisites
- Access to the gateway via MCP or webhook
- The API's base URL, auth type, and credential

## Steps

### 1. Read platform context
```
handover.get_platform_context
```
Check the rules. Follow them.

### 2. Create the n8n credential (if needed)
In n8n UI: Settings > Credentials > Add Credential.
Note the credential ID and type.

### 3. Add to api_registry_v2
Use `log_change` to document what you're doing, then insert a row:
```json
{"data": [{
  "api_name": "your_api",
  "client": "all",
  "category": "marketing",
  "base_url": "https://api.example.com",
  "auth_type": "header",
  "credential_id": "your_credential_id",
  "credential_type": "httpHeaderAuth",
  "handler_workflow_id": "",
  "enabled": true
}]}
```

If auth_type is `header` or `query` with a $vars key: set `handler_workflow_id` to empty (passthrough).
If auth_type is `oauth` or requires n8n credential injection: set `handler_workflow_id` to the appropriate handler.

### 4. Add actions to action_map_v2
Insert one row per action:
```json
{"data": [{
  "api_name": "your_api",
  "action": "list_items",
  "method": "GET",
  "endpoint": "/v1/items",
  "body_mode": "passthrough",
  "description": "List all items",
  "enabled": true
}]}
```

For handler-type actions, set `body_mode` to `handler` and leave `endpoint` empty (the handler builds the URL).

### 5. If handler-type: add to the handler workflow
Use `safe_modify_workflow` to modify the appropriate handler:
- Marketing Ads: `6e9ooA3kc0zAPWyy`
- Analytics: `EPFlvH1zLhvUUyS7`
- CRM: `WZtxStkDZ2pr9s3l`
- Google Suite: `RKoOuaqcnbSYfLLp`
- GitHub: `eZlzhG7YHsdWnArf`

Add the domain to the handler's `apiConfigs` object and Switch node.

### 6. Test
```
execute_action domain=your_api action=list_items client=ascend
```

### 7. Log and verify
```
handover.log_change — document what was added
handover.run_audit — verify zero violations
```

## Common Mistakes
- Setting `client` to a specific tenant instead of `all`
- Forgetting to set `handler_workflow_id` for handler-type domains
- Not toggling the handler workflow OFF/ON after modification (webhook re-registration)
- Using the wrong credential type (e.g., `httpBasicAuth` when the credential is `wordpressApi`)
