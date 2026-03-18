# ADR-001: n8n Platform Governance Architecture

**Status:** FINAL
**Author:** Lead Engineer (Claude Opus, Cowork session March 18 2026)
**Reviewer:** Mishaal Murawala, Founder, Ascend GTM
**Date:** March 18, 2026

---

## 1. Problem Statement

The Ascend GTM n8n Cloud instance is the runtime for an AI agent crew — currently 3 agents, 34 APIs, 50 workflows. The trajectory is hundreds of agents and hundreds of APIs, modified daily by multiple AI tools (Claude, ChatGPT, Perplexity, and potentially others) across parallel sessions.

Today, any tool with the API key can modify any workflow at any time with no backup, no logging, no conflict detection, and no notification. This has caused:

- **Google Ads broken for weeks** because a registry entry had the wrong client value. No tool detected it. Every session that investigated flagged the same symptoms but misdiagnosed the root cause or claimed to fix it.
- **WordPress broken for weeks** because it had no handler and no tool noticed.
- **24 hardcoded URLs** across 11 workflows — a governing spec violation that accumulated over multiple sessions.
- **Stale documentation** across GitHub, DataTables, and session state — each session left the platform slightly more confused than it found it.
- **Repeated work** — every new AI session starts blind, re-discovers the same issues, and sometimes re-introduces problems that were already fixed.

The cost isn't technical. It's **time**. Hundreds of hours lost re-fixing things that should just work.

## 2. Decision Required

How should the n8n Cloud instance be governed so that:

1. Multiple AI tools can modify it simultaneously without breaking each other's work
2. Every change is documented automatically
3. Any change can be rolled back
4. New sessions start with full context, not blind
5. The system scales from 50 workflows to 500+ without the governance breaking down

## 3. Constraints

- **n8n Cloud is the runtime.** Self-hosted is a future option, not current.
- **AI tools manage everything.** No human review of PRs. Tools must self-govern.
- **Changes happen daily, multiple times per day.** The governance layer cannot add friction that slows velocity.
- **n8n Cloud API limitations:** DataTable rows cannot be deleted or updated (only inserted). Workflow PUT overwrites the entire workflow with no history. No native locking.

## 4. Options Considered

### Option A: Full GitOps (Git → CI/CD → n8n)

Git is the source of truth. All workflow JSON lives in a repo. Changes are made as commits/PRs. A CI/CD pipeline deploys from Git to n8n.

**Pros:** Industry standard. Full version history. Merge conflict detection. Rollback is `git revert`.

**Cons:** Requires AI tools to work through Git, not the n8n API directly. Adds a deployment step between "change made" and "change live." n8n Cloud doesn't have native import — deployment requires PUT for every workflow, which can fail mid-deploy. AI tools currently modify n8n directly; changing that behavior requires reconfiguring every MCP connection.

**Verdict:** Right long-term architecture. Wrong for today. The migration from "direct n8n API" to "Git-first" is a project in itself, and it would halt all forward progress while it's being built.

### Option B: Gateway-Enforced Governance (current direction)

The gateway's handover domain becomes the governance layer. All modifications go through `safe_modify_workflow` which enforces snapshot → modify → log → notify. Direct API access is revoked.

**Pros:** Works today. No new infrastructure. Every AI frontend already connects through the gateway.

**Cons:** Governance logic lives inside the system it governs — if the handover handler breaks, governance disappears. Locking via DataTable is fragile (rows can't be deleted, so locks can become orphaned). Doesn't handle merge conflicts — last write still wins.

**Verdict:** Good transitional step. Solves the immediate "no backups, no logs" problem. But not the long-term answer for hundreds of workflows.

### Option C: Hybrid — Git as Record + Gateway as Enforcer (RECOMMENDED)

Combine both: the gateway enforces governance at write time, and Git serves as the version-controlled record of every change. Not GitOps (Git doesn't deploy), but Git as the audit trail and rollback mechanism.

**How it works:**

1. **Before any change:** `safe_modify_workflow` snapshots the current workflow JSON to GitHub (timestamped file in `snapshots/{workflow_id}/`).
2. **Apply the change:** PUT to n8n API.
3. **After the change:** Log to platform_changelog DataTable + Slack notification.
4. **Nightly:** A full export of all workflows to GitHub (not just changed ones). This is the "known good state" baseline.
5. **Rollback:** Any tool can restore a workflow from a GitHub snapshot by reading the snapshot and PUTting it back via `safe_modify_workflow`.
6. **Context:** `get_platform_context` gives every session the current state, recent changes, and gotchas — no session starts blind.

**Conflict handling:** Not merge-based (too complex for AI tools). Instead: snapshot-before-write ensures no change is lost, even if two sessions modify the same workflow. The changelog shows exactly what each session changed and when. If a conflict causes a problem, rollback to the pre-change snapshot.

**Migration to full GitOps later:** When the instance moves to self-hosted or the workflow count exceeds what the gateway can manage, the Git repo already has every workflow versioned. The migration is: add a CI/CD pipeline that deploys from the repo, then stop allowing direct writes.

## 5. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI TOOLS (write path)                  │
│         Claude · ChatGPT · Perplexity · Custom           │
└──────────────────────┬──────────────────────────────────┘
                       │ MCP / webhook
                       ▼
┌─────────────────────────────────────────────────────────┐
│              GATEWAY (orchestrate-v2)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │  handover domain (governance layer)               │   │
│  │                                                    │   │
│  │  get_platform_context  → READ: health + changes   │   │
│  │  safe_modify_workflow  → WRITE: snapshot + PUT     │   │
│  │  log_change            → LOG: any platform change  │   │
│  │  run_audit             → CHECK: governing spec     │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │  GitHub   │  │ n8n API  │  │  Slack   │
   │ snapshots │  │  PUT/GET │  │ #alerts  │
   │ + nightly │  │          │  │          │
   └──────────┘  └──────────┘  └──────────┘
```

### 5.1 The Rules (for every AI tool)

These rules must be embedded in the governing spec, the session state, and the `get_platform_context` response. Every tool reads them before doing work.

1. **Read before write.** Call `get_platform_context` before making any change. Know what's healthy, what's broken, and what was recently changed.

2. **Use the safe path.** Modify workflows through `safe_modify_workflow`, not raw PUT. This ensures snapshot + log + notify.

3. **Log non-workflow changes.** For DataTable inserts, variable updates, or config changes, call `log_change` with what you did and why.

4. **Run the audit after changes.** Call `run_audit` after any session that modifies workflows. Verify zero governing spec violations.

5. **Don't fix what isn't broken.** If `get_platform_context` shows a service as healthy, don't re-investigate it. Trust the verified state.

6. **Update the verified state.** If you fix something, call `update_session_state` with the new verified state so the next session knows.

### 5.2 What This Doesn't Solve (Yet)

- **True concurrency control.** Two sessions can still modify the same workflow simultaneously. The snapshot ensures no change is silently lost, but the last write wins. For hundreds of workflows, collisions become unlikely (each session works on different workflows). If it becomes a problem, add a lock DataTable.

- **Automated rollback.** If a change breaks something, a human or AI must manually restore from the GitHub snapshot. No auto-revert on failure — that's dangerous at scale (the "fix" might be worse than the break).

- **Direct n8n UI edits.** If someone edits a workflow in the n8n Cloud UI, it bypasses everything. Mitigation: the nightly full export catches it retroactively.

## 6. Implementation Phases

### Phase 0: What Already Exists (done this session)

- `safe_modify_workflow` — snapshot + PUT + webhook re-register + log + Slack ✓
- `log_change` — changelog DataTable logging ✓
- `get_platform_context` — health + changes + gotchas + verified IDs ✓
- `platform_changelog` DataTable — change audit trail ✓
- GitHub snapshots directory — pre-change workflow snapshots ✓
- `run_audit` — governing spec violation scanner ✓

### Phase 1: Nightly Full Export (next)

Add workflow JSON export to the daily backup job. Every night, all 50+ workflows are exported to GitHub at `exports/workflows/{id}.json`. This is the "known good state" that any rollback targets.

**Effort:** Small — modify existing backup workflow to also export workflows.

### Phase 2: Gateway Failure Alerting (next)

Add a failure counter to the gateway's response path. When a domain returns `ok: false` more than N times in a window, trigger a Slack alert with the domain, error type, and affected client. This catches the "silent routing failure" problem that let Google Ads stay broken for weeks.

**Effort:** Small — add a Code node to the gateway's error response path.

### Phase 3: Governing Spec Enforcement in get_platform_context

When any tool calls `get_platform_context`, the response should include a `rules` section with the 6 rules above. The tool reads the rules and follows them. This is convention-based enforcement — it works because AI tools follow instructions when they're given clearly.

**Effort:** Small — update the `get_platform_context` action to include rules.

### Phase 4: Rollback Action

Add `rollback_workflow` to the handover domain. Takes a workflow ID + snapshot timestamp, reads the snapshot from GitHub, and applies it via `safe_modify_workflow`. One-command rollback.

**Effort:** Small.

### Phase 5: Full GitOps Migration (future, when self-hosted)

When the instance moves to self-hosted n8n or workflow count exceeds 200+:

1. The GitHub repo already has every workflow versioned (from nightly exports + snapshots).
2. Add a GitHub Actions CI/CD pipeline that deploys workflow JSON to n8n on merge to main.
3. Reconfigure AI tool access to submit changes as Git commits instead of gateway calls.
4. The gateway governance layer becomes the CI/CD gatekeeper instead of the write enforcer.

This is a natural evolution, not a rewrite. Everything built in Phases 0-4 feeds into it.

## 7. What Success Looks Like

- **No session starts blind.** Every tool calls `get_platform_context` and knows the current state.
- **No change is undocumented.** Every modification appears in the changelog and GitHub.
- **No change is un-recoverable.** Every workflow has a pre-change snapshot. Nightly exports provide baseline recovery.
- **No silent failures.** Gateway routing errors trigger Slack alerts in real-time.
- **Time spent re-fixing drops to near zero.** Tools trust the verified state and don't re-investigate working services.

## 8. Engineering Decisions

### 8.1 API Key Strategy: Keep a Break-Glass Key, Rotate External to Read-Only

**Decision:** Three-tier key model.

- **Tier 1 — Internal write key** (`$vars.N8N_INTERNAL_API_KEY`): Lives inside n8n, accessible only to workflows. The gateway uses this for all modifications. No external tool can read it. This is the only key that writes to production.
- **Tier 2 — External read-only key** (VPS + monitoring): Used by external tools for health checks, audits, workflow reads, and execution history. Cannot modify workflows, DataTables, or variables. Rotate the current full-access VPS key to read-only scopes: `workflow:read`, `execution:read`, `execution:list`, `dataTableRow:read`, `variable:list`.
- **Tier 3 — Break-glass full-access key**: Stored encrypted in the GitHub repo (not on VPS in plaintext). Only used when the gateway or handover handler is broken and cannot self-repair. Every use is logged. After use, rotate immediately.

**Reasoning:** Revoking all external write access forces everything through the gateway — good. But if the gateway breaks, you're locked out. The break-glass key solves this without keeping a god-mode key sitting on the VPS in plaintext (which is the current situation). Enterprise break-glass patterns (AWS IAM emergency access, Kubernetes RBAC elevation) all follow this principle: emergency access exists but is audited, time-bounded, and stored separately from routine access.

### 8.2 Failure Alerting: 3 Failures per Domain in 5 Minutes

**Decision:** Alert when the same domain returns `ok: false` 3 or more times within a 5-minute window. Alert goes to Slack #n8n-alerts with domain name, error type, affected client, and last 3 error messages.

**Reasoning:** The circuit breaker pattern (from Netflix Hystrix, now Resilience4j) uses 3 consecutive failures as the industry minimum to distinguish transient failures (network blip, cold start) from systemic issues (wrong config, expired credential). A 5-minute window is appropriate for this platform — changes happen throughout the day, so detection must be fast (not daily or weekly health checks). But 60 seconds would be too aggressive — a temporary gateway restart would trigger false alarms.

The counter resets when the domain returns `ok: true`. The alert fires once per incident, not per failure (no alert storms).

**What this catches:** The Google Ads scenario — a misconfigured registry entry causing every request to fail with a "no registry entry" error. Within 5 minutes of anyone trying to use Google Ads, Slack gets an alert.

### 8.3 Backup Scope: Workflows + DataTable Rows + DataTable Schemas

**Decision:** The nightly backup exports three things:

1. **Workflow JSON** — all workflow definitions at `exports/workflows/{workflow_id}.json`. This is the rollback target.
2. **DataTable rows** — already implemented, continues as-is.
3. **DataTable schemas** — column names, types, and constraints at `exports/schemas/{table_name}.json`. A workflow referencing a deleted or renamed column fails silently — the schema backup catches this.

**Reasoning:** Infrastructure-as-code platforms (Terraform, Pulumi) version both the resource definitions and the state. For n8n, workflows are the definitions and DataTables are the state. Backing up one without the other means you can restore workflows that reference tables that no longer have the right columns. The schema export closes this gap.

**Retention:** 30 days of nightly exports in GitHub. GitHub handles versioning — each commit shows the diff from the previous night.

### 8.4 Alert Routing: Slack Only, No AI Auto-Response

**Decision:** All alerts go to Slack #n8n-alerts. No PagerDuty, no email, no SMS. AI tools do not receive alerts and do not auto-remediate.

**Reasoning:** This is a one-person operation. Mishaal lives in Slack. Adding PagerDuty is overhead with zero value when there's one person on call. Email and SMS are slower and less actionable than a Slack message with structured context.

AI tools must NOT receive alerts or auto-fix issues, for one critical reason: **an AI tool caused the problem in the first place** (e.g., wrong client value in the registry, missing handler). Letting AI tools auto-respond to alerts creates a feedback loop where the same tool that introduced the bug tries to fix it with the same (mis)understanding.

Instead: AI tools can READ alert history via `get_platform_context` so they know what's been failing. But the decision to investigate and fix is initiated by a human or by a deliberate new session — not by an automated trigger.

**When to revisit:** If the team grows beyond one person, add PagerDuty for on-call rotation. If self-hosted n8n is deployed, add infrastructure-level alerting (container health, DB connections).
