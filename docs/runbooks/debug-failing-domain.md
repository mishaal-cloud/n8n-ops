# Runbook: Debug a Failing Domain

## Step 1: Check platform context
```
handover.get_platform_context
```
Look at `health.down` and `health.degraded`. Check `recent_changes` for anything that might have caused the failure.

## Step 2: Test the domain directly
```
execute_action domain=<failing_domain> action=<any_action> client=kahuna
```
Note the error: is it 404, 500, or an error body with `ok: false`?

## Step 3: Diagnose by error type

### HTTP 404 from gateway
The handler webhook is unreachable. Causes:
- Handler workflow was updated via API but webhook not re-registered → **Fix:** Toggle handler OFF/ON
- Handler workflow is inactive → **Fix:** Activate it
- Wrong webhook path in Prepare Infra URLs → **Fix:** Check the path matches the handler's Webhook Trigger node

### HTTP 500 from gateway (or `ok: false` with error body)
The handler ran but failed internally. Causes:
- Wrong credential type (e.g., `httpBasicAuth` when it should be `wordpressApi`) → **Fix:** Check credential type in the Call node
- API version sunset → **Fix:** Check handler code for API version, compare to official docs
- Missing required params → **Fix:** Check `get_action_schema` for required params

### `No registry entry for domain X client Y`
The api_registry_v2 doesn't have a matching entry. Causes:
- Entry has wrong `client` value (e.g., `ascend` instead of `all`) → **Fix:** Insert a new row with `client=all`
- Entry was never created → **Fix:** Follow the add-new-api runbook

### `Unknown action X for domain Y`
The action_map_v2 doesn't have the action. Causes:
- Action was never registered → **Fix:** Insert a row in action_map_v2
- Typo in action name → **Fix:** Check exact spelling in action_map

### Handler returns `Unknown API: <domain>`
The handler's Code node doesn't have this domain in its apiConfigs. Causes:
- Domain was added to registry but not to the handler → **Fix:** Add domain to handler via `safe_modify_workflow`

## Step 4: After fixing
1. Call `log_change` with what you fixed and why
2. Call `run_audit` to verify zero violations
3. Re-test the domain
4. Call `update_session_state` if the fix changes the platform's verified state

## Step 5: Check if this was a known gotcha
Review the `gotchas` in `get_platform_context`. If your fix addresses a new failure mode, add it to the gotchas by updating the verified state.
