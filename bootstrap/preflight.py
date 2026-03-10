#!/usr/bin/env python3
"""
n8n-ops Preflight Check
========================
Validates all n8n infrastructure is reachable and correctly configured.
Run at the start of every AI session before any work.

Usage:
    python3 preflight.py <n8n_base_url> <api_key>
    
Example:
    python3 preflight.py https://mmurawala.app.n8n.cloud eyJhbG...

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

import json
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def _request(url, method="GET", data=None, headers=None, timeout=30):
    """Low-level HTTP request. Returns (status_code, parsed_json_or_string)."""
    hdrs = headers or {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    
    req = Request(url, data=body, headers=hdrs, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except:
            return e.code, raw
    except URLError as e:
        return 0, {"_network_error": str(e.reason)}
    except Exception as e:
        return 0, {"_error": str(e)}


def check_api_auth(base_url, api_key):
    """Check 1: n8n REST API is reachable with correct auth."""
    status, body = _request(
        f"{base_url}/api/v1/workflows?limit=1",
        headers={"X-N8N-API-KEY": api_key}
    )
    if status == 200 and isinstance(body, dict) and "data" in body:
        return True, f"API auth OK (HTTP {status}, {len(body['data'])} workflow returned)"
    elif status == 401:
        return False, f"API key rejected (HTTP 401) — key may be expired or revoked"
    else:
        return False, f"Unexpected response: HTTP {status}, body={str(body)[:200]}"


def check_critical_workflows(base_url, api_key, config):
    """Check 2: All critical workflows exist and are active."""
    critical = config.get("critical_workflows", {})
    if not critical:
        return False, "No critical workflows found in session config"
    
    inactive = []
    for name, info in critical.items():
        if not info.get("active"):
            inactive.append(name)
    
    if inactive:
        return False, f"Inactive critical workflows: {', '.join(inactive)}"
    
    return True, f"All {len(critical)} critical workflows active"


def check_datatable_access(base_url, api_key, config):
    """Check 3: All DataTables are accessible and have data."""
    table_status = config.get("table_status", {})
    if not table_status:
        return False, "No table status in session config"
    
    failures = []
    for name, status in table_status.items():
        if status.get("status") != "ok":
            failures.append(f"{name}: {status.get('message', 'unknown error')}")
    
    if failures:
        return False, f"DataTable failures: {'; '.join(failures)}"
    
    return True, f"All {len(table_status)} DataTables accessible"


def check_session_config_webhook(base_url, api_key):
    """Check 4: Session config webhook is reachable and returns valid config."""
    status, body = _request(
        f"{base_url}/webhook/session-config",
        method="POST",
        data={},
        headers={"X-N8N-API-KEY": api_key, "Content-Type": "application/json"},
        timeout=60
    )
    
    if not isinstance(body, dict):
        return False, None, f"Non-JSON response: {str(body)[:200]}"
    
    # Validate required fields
    required_fields = [
        "auth_patterns", "shell_constraints", "webhook_paths",
        "critical_workflows", "table_ids", "table_status",
        "e2e_notes", "phase_status"
    ]
    missing = [f for f in required_fields if f not in body]
    if missing:
        return False, body, f"Missing fields in config: {', '.join(missing)}"
    
    # Validate no table IDs are NOT_SET
    for name, table_id in body.get("table_ids", {}).items():
        if table_id == "NOT_SET":
            return False, body, f"Table ID for '{name}' is NOT_SET — variable missing"
    
    return True, body, f"Config valid ({len(body.get('webhook_paths', {}))} webhooks, {len(body.get('critical_workflows', {}))} critical workflows)"


def check_e2e_webhook(base_url, api_key, config):
    """Check 5: E2E test suite webhook is reachable."""
    e2e_path = config.get("e2e_notes", {}).get("trigger_path")
    if not e2e_path:
        return False, "E2E trigger path not found in config"
    
    # The E2E webhook responds with 'Workflow was started' on success (async mode)
    status, body = _request(
        f"{base_url}{e2e_path}",
        method="POST",
        data={"dry_run": True},
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        timeout=30
    )
    
    if isinstance(body, dict) and body.get("message") == "Workflow was started":
        return True, f"E2E webhook reachable at {e2e_path} (async trigger confirmed)"
    elif status == 404:
        return False, f"E2E webhook 404 at {e2e_path} — workflow may be inactive"
    else:
        # Any non-error response means the webhook is reachable
        if status in (200, 201, 202):
            return True, f"E2E webhook reachable at {e2e_path} (HTTP {status})"
        return False, f"E2E webhook error: HTTP {status}, body={str(body)[:200]}"


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 preflight.py <n8n_base_url> <api_key>")
        print("Example: python3 preflight.py https://mmurawala.app.n8n.cloud eyJhbG...")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip("/")
    api_key = sys.argv[2]
    
    print("=" * 64)
    print("n8n-ops PREFLIGHT CHECK")
    print("=" * 64)
    print(f"Target: {base_url}")
    print(f"Time:   {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    
    all_passed = True
    config = None
    
    # Check 1: API Auth
    print("CHECK 1: n8n REST API auth...")
    ok, msg = check_api_auth(base_url, api_key)
    print(f"  {'✅' if ok else '❌'} {msg}")
    if not ok:
        print("\n❌ PREFLIGHT FAILED — cannot proceed without API access")
        sys.exit(1)
    
    # Check 2: Session Config Webhook (must come before 3-5 since they depend on it)
    print("\nCHECK 2: Session config webhook...")
    ok, config, msg = check_session_config_webhook(base_url, api_key)
    print(f"  {'✅' if ok else '❌'} {msg}")
    if not ok:
        all_passed = False
        if config is None:
            print("\n❌ PREFLIGHT FAILED — session config unreachable, cannot validate remaining checks")
            sys.exit(1)
    
    # Check 3: Critical Workflows
    print("\nCHECK 3: Critical workflow status...")
    ok, msg = check_critical_workflows(base_url, api_key, config)
    print(f"  {'✅' if ok else '❌'} {msg}")
    if not ok:
        all_passed = False
    
    # Check 4: DataTable Access
    print("\nCHECK 4: DataTable access...")
    ok, msg = check_datatable_access(base_url, api_key, config)
    print(f"  {'✅' if ok else '❌'} {msg}")
    if not ok:
        all_passed = False
    
    # Check 5: E2E Webhook
    print("\nCHECK 5: E2E test webhook...")
    ok, msg = check_e2e_webhook(base_url, api_key, config)
    print(f"  {'✅' if ok else '❌'} {msg}")
    if not ok:
        all_passed = False
    
    # Summary
    print()
    print("=" * 64)
    if all_passed:
        print("✅ ALL PREFLIGHT CHECKS PASSED")
        print()
        print("Session config available at: POST /webhook/session-config")
        print(f"Auth patterns: {list(config.get('auth_patterns', {}).keys())}")
        print(f"Active workflows: {config.get('total_active_workflows')}")
        print(f"Webhook endpoints: {config.get('total_webhook_endpoints')}")
        print(f"Phase status: {json.dumps(config.get('phase_status', {}))}")
    else:
        print("❌ PREFLIGHT FAILED — fix issues above before proceeding")
    print("=" * 64)
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
