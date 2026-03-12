# Rollback Contract

## Per-Item Recovery Procedure

For each item in the handover doc:

1. **Git snapshot BEFORE** starting (tagged: `pre-item-N`)
2. **Execute** the item per its implementation plan
3. **Validate** using the validation protocol
4. **If validation fails:**
   a. Attempt fix #1 — diagnose, fix, re-push, re-validate
   b. If still failing: attempt fix #2 — different approach, re-push, re-validate
   c. If still failing after 2 attempts:
      - Revert to `pre-item-N` snapshot
      - Log the item as **BLOCKED** in session-state.json
      - Record root cause, both fix attempts, and what information would unblock it
      - Continue to the next item
5. **Git snapshot AFTER** completion (tagged: `post-item-N`)

## Isolation Guarantee

- Reverting item N MUST NOT revert previously completed items (1 through N-1)
- Items are independent unless the handover doc's Execution Order explicitly states a dependency
- If item N depends on item M, and item M is BLOCKED, item N is automatically BLOCKED with reason: "Depends on blocked item M"

## Revert Procedure

When reverting to a pre-item snapshot:

1. Fetch the workflow JSON from the `pre-item-N` git state
2. Push that JSON to the n8n instance via API (overwriting the broken version)
3. Toggle the workflow off/on to re-register webhooks
4. Verify the workflow is back to its pre-item state
5. If DataTable rows were modified: there is no API DELETE for DataTable rows — document the orphaned rows in the Session Issue Report as "Requires manual cleanup"
6. If variables were created: variables cannot be deleted via API — document in Session Issue Report

## Cascading Failure Prevention

If 3 consecutive items are BLOCKED:
- Stop execution
- Produce a diagnostic report: what is the common failure pattern?
- If the root cause is systemic (instance issue, auth failure, API change), flag as a session-level blocker
- Produce exit artifacts (Session Issue Report, Session Continuity File) and inform the operator
