#!/usr/bin/env python3
"""
n8n Handover Framework — Principle Violation Scanner

Fetches workflow(s) via API and scans all Code nodes for common violations.
Designed to be run after every push and at session end.

Usage:
  python3 audit.py <BASE_URL> <API_KEY> <WORKFLOW_ID> [WORKFLOW_ID...]
  python3 audit.py <BASE_URL> <API_KEY> --all   # scan all workflows

All parameters are positional — no hardcoded values.
"""

import sys
import json
import re
import urllib.request
import urllib.error


def fetch(base, key, path):
    """Fetch from n8n API."""
    url = f"{base}{path}"
    req = urllib.request.Request(url, headers={"X-N8N-API-KEY": key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def scan_code_node(node_name, code, violations):
    """Scan a Code node's JavaScript for principle violations."""

    # Principle: No hardcoded URLs
    url_patterns = [
        r'https?://[a-zA-Z0-9\-]+\.app\.n8n\.cloud',
        r'https?://[a-zA-Z0-9\-]+\.n8n\.cloud/api',
        r'https?://[a-zA-Z0-9\-]+\.n8n\.cloud/webhook',
    ]
    for pattern in url_patterns:
        matches = re.findall(pattern, code)
        for match in matches:
            # Allow if it's in a comment
            for line in code.split('\n'):
                if match in line and not line.strip().startswith('//') and not line.strip().startswith('*'):
                    violations.append({
                        "node": node_name,
                        "type": "hardcoded_url",
                        "detail": f"Hardcoded URL found: {match}",
                        "severity": "HIGH"
                    })
                    break

    # Principle: No hardcoded DataTable IDs
    # DataTable IDs look like: alphanumeric strings 10+ chars used in API paths
    dt_pattern = r'data-tables/([a-zA-Z0-9]{10,})'
    matches = re.findall(dt_pattern, code)
    for match in matches:
        violations.append({
            "node": node_name,
            "type": "hardcoded_datatable_id",
            "detail": f"Hardcoded DataTable ID: {match}",
            "severity": "HIGH"
        })

    # Principle: No hardcoded API keys or secrets
    secret_patterns = [
        (r'eyJ[a-zA-Z0-9_-]{20,}\.eyJ[a-zA-Z0-9_-]{20,}', "JWT token"),
        (r'pat-na1-[a-zA-Z0-9]{8,}', "HubSpot PAT"),
        (r'sk-[a-zA-Z0-9]{20,}', "API secret key"),
        (r'Bearer\s+[a-zA-Z0-9_-]{20,}', "Bearer token"),
    ]
    for pattern, label in secret_patterns:
        if re.search(pattern, code):
            violations.append({
                "node": node_name,
                "type": "hardcoded_secret",
                "detail": f"Possible hardcoded {label}",
                "severity": "CRITICAL"
            })

    # Principle: No hardcoded tenant/client names in business logic
    tenant_patterns = [
        r'["\']kahuna["\']',
        r'["\']ascend["\']',
        r'["\']codiac["\']',
    ]
    for pattern in tenant_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            # Check if it's in config reading vs hardcoded logic
            for line in code.split('\n'):
                if re.search(pattern, line, re.IGNORECASE):
                    if 'config' not in line.lower() and 'param' not in line.lower():
                        violations.append({
                            "node": node_name,
                            "type": "hardcoded_tenant",
                            "detail": f"Possible hardcoded tenant name in: {line.strip()[:80]}",
                            "severity": "MEDIUM"
                        })
                        break

    # Principle: Error handling
    if 'try' not in code and 'catch' not in code and len(code.split('\n')) > 10:
        violations.append({
            "node": node_name,
            "type": "missing_error_handling",
            "detail": "Code node >10 lines with no try/catch",
            "severity": "MEDIUM"
        })

    # Principle: Runbook header
    if not code.strip().startswith('//') and not code.strip().startswith('/*'):
        if len(code.split('\n')) > 5:
            violations.append({
                "node": node_name,
                "type": "missing_runbook_header",
                "detail": "Code node >5 lines with no header comment",
                "severity": "LOW"
            })

    return violations


def audit_workflow(base, key, wf_id):
    """Fetch a workflow and scan all Code nodes."""
    wf = fetch(base, key, f"/workflows/{wf_id}")
    if not wf:
        return None, [{"node": "N/A", "type": "fetch_error", "detail": f"Could not fetch workflow {wf_id}", "severity": "HIGH"}]

    wf_name = wf.get("name", "Unknown")
    nodes = wf.get("nodes", [])
    violations = []

    for node in nodes:
        node_type = node.get("type", "")
        node_name = node.get("name", "Unknown")

        # Code nodes
        if node_type == "n8n-nodes-base.code":
            code = node.get("parameters", {}).get("jsCode", "")
            if code:
                scan_code_node(f"{wf_name} → {node_name}", code, violations)

        # Function nodes (legacy)
        elif node_type == "n8n-nodes-base.function":
            code = node.get("parameters", {}).get("functionCode", "")
            if code:
                scan_code_node(f"{wf_name} → {node_name}", code, violations)

        # HTTP Request nodes — check for hardcoded URLs
        elif node_type == "n8n-nodes-base.httpRequest":
            url = node.get("parameters", {}).get("url", "")
            if isinstance(url, str) and url and not url.startswith("="):
                # Static URL — check if it contains instance-specific values
                for pattern in [r'\.app\.n8n\.cloud', r'\.n8n\.cloud/api']:
                    if re.search(pattern, url):
                        violations.append({
                            "node": f"{wf_name} → {node_name}",
                            "type": "hardcoded_url_in_http_node",
                            "detail": f"Static URL in HTTP Request: {url[:80]}",
                            "severity": "HIGH"
                        })

    return wf_name, violations


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 audit.py <BASE_URL> <API_KEY> <WORKFLOW_ID> [WORKFLOW_ID...]")
        print("       python3 audit.py <BASE_URL> <API_KEY> --all")
        sys.exit(1)

    base = sys.argv[1].rstrip("/")
    key = sys.argv[2]
    targets = sys.argv[3:]

    # If --all, fetch all workflow IDs
    if targets == ["--all"]:
        print("Fetching all workflows...")
        result = fetch(base, key, "/workflows?limit=250")
        if result and "data" in result:
            targets = [w["id"] for w in result["data"]]
            print(f"Found {len(targets)} workflows")
        else:
            print("ERROR: Could not fetch workflow list")
            sys.exit(1)

    # Audit each workflow
    all_violations = {}
    total = 0

    for wf_id in targets:
        wf_name, violations = audit_workflow(base, key, wf_id)
        if violations:
            all_violations[f"{wf_name} ({wf_id})"] = violations
            total += len(violations)

    # Report
    print()
    print(f"=== Audit Report: {len(targets)} workflows scanned ===")
    print()

    if not all_violations:
        print("RESULT: CLEAN — Zero violations found")
    else:
        print(f"RESULT: {total} violation(s) found across {len(all_violations)} workflow(s)")
        print()

        by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        for wf, violations in all_violations.items():
            for v in violations:
                by_severity[v["severity"]].append(f"  [{v['type']}] {v['node']}: {v['detail']}")

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if by_severity[severity]:
                print(f"--- {severity} ({len(by_severity[severity])}) ---")
                for item in by_severity[severity]:
                    print(item)
                print()

    # JSON output for programmatic use
    print("=== JSON Output ===")
    print(json.dumps({
        "workflows_scanned": len(targets),
        "total_violations": total,
        "violations_by_workflow": all_violations
    }, indent=2))

    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
