#!/usr/bin/env python3
"""
n8n Handover Framework — Preflight Validation

Validates instance connectivity and returns essential configuration.
Run at session start before any item execution.

Usage:
  python3 preflight.py <BASE_URL> <API_KEY>

Example:
  python3 preflight.py https://mmurawala.app.n8n.cloud/api/v1 eyJhbG...

All parameters are positional arguments — no hardcoded values.
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone


def fetch(base, key, path):
    """Fetch from n8n API. Returns parsed JSON or None on error."""
    url = f"{base}{path}"
    req = urllib.request.Request(url, headers={"X-N8N-API-KEY": key})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "reason": str(e.reason), "url": url}
    except urllib.error.URLError as e:
        return {"error": "connection", "reason": str(e.reason), "url": url}
    except Exception as e:
        return {"error": "unknown", "reason": str(e), "url": url}


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 preflight.py <BASE_URL> <API_KEY>")
        sys.exit(1)

    base = sys.argv[1].rstrip("/")
    key = sys.argv[2]

    print(f"=== n8n Preflight Validation ===")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Instance: {base}")
    print()

    checks = {}

    # 1. API connectivity
    print("[1/4] Testing API connectivity...")
    result = fetch(base, key, "/workflows?limit=1")
    if isinstance(result, dict) and "error" in result:
        checks["api_connectivity"] = {"status": "FAIL", "detail": result}
        print(f"  FAIL: {result}")
    else:
        checks["api_connectivity"] = {"status": "PASS"}
        print("  PASS")

    # 2. Workflow count
    print("[2/4] Counting workflows...")
    result = fetch(base, key, "/workflows?limit=1")
    if isinstance(result, dict) and "error" not in result:
        count = result.get("count", result.get("nextCursor", "unknown"))
        # Fetch all to count
        all_wf = fetch(base, key, "/workflows?limit=250")
        if isinstance(all_wf, dict) and "data" in all_wf:
            wf_count = len(all_wf["data"])
            active = sum(1 for w in all_wf["data"] if w.get("active"))
            checks["workflows"] = {
                "status": "PASS",
                "total": wf_count,
                "active": active,
                "inactive": wf_count - active
            }
            print(f"  PASS: {wf_count} workflows ({active} active, {wf_count - active} inactive)")
        else:
            checks["workflows"] = {"status": "WARN", "detail": "Could not enumerate workflows"}
            print("  WARN: Could not enumerate")
    else:
        checks["workflows"] = {"status": "SKIP", "detail": "API connectivity failed"}
        print("  SKIP: API not reachable")

    # 3. Variables
    print("[3/4] Fetching variables...")
    result = fetch(base, key, "/variables?limit=250")
    if isinstance(result, dict) and "error" not in result:
        var_data = result.get("data", result) if isinstance(result, dict) else result
        if isinstance(var_data, list):
            var_count = len(var_data)
            var_names = [v.get("key", "unknown") for v in var_data]
        elif isinstance(var_data, dict) and "data" in var_data:
            var_count = len(var_data["data"])
            var_names = [v.get("key", "unknown") for v in var_data["data"]]
        else:
            var_count = 0
            var_names = []
        checks["variables"] = {"status": "PASS", "count": var_count, "names": var_names}
        print(f"  PASS: {var_count} variables")
    else:
        checks["variables"] = {"status": "FAIL", "detail": str(result)}
        print(f"  FAIL: {result}")

    # 4. Session config webhook
    print("[4/4] Testing session-config webhook...")
    try:
        webhook_url = base.replace("/api/v1", "") + "/webhook/session-config"
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps({"test": True}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            config = json.loads(resp.read().decode())
            checks["session_config"] = {"status": "PASS", "config": config}
            print("  PASS")
    except Exception as e:
        checks["session_config"] = {"status": "WARN", "detail": str(e)}
        print(f"  WARN: {e} (non-blocking)")

    # Summary
    print()
    print("=== Preflight Summary ===")
    failures = [k for k, v in checks.items() if v.get("status") == "FAIL"]
    warnings = [k for k, v in checks.items() if v.get("status") == "WARN"]

    if failures:
        print(f"FAILURES: {', '.join(failures)}")
        print("Session cannot proceed until failures are resolved.")
    elif warnings:
        print(f"PASS with warnings: {', '.join(warnings)}")
        print("Session can proceed.")
    else:
        print("ALL CHECKS PASSED. Session ready.")

    # Output full results as JSON for programmatic use
    print()
    print("=== JSON Output ===")
    print(json.dumps(checks, indent=2))

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
