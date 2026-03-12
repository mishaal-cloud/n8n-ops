# Validation Protocol

Run after every item push and again after all items are complete.

## Step 1: Code Scan

Fetch every modified workflow via API. For every Code node, scan for:

- Hardcoded URLs not using `$vars`
- Hardcoded DataTable IDs not using `$vars`
- Hardcoded API keys or secrets
- Hardcoded tenant/client names not read from config
- Hardcoded domain names in filter sets
- Any value that could change between environments
- Missing try/catch or error handling
- Missing runbook headers
- References to known-broken patterns (see governing spec platform bugs)

Use the reusable audit script at `/home/claude/audit.py`. If it does not exist yet, copy it from the skill's `scripts/audit.py` and adapt it with current session constants.

**If any violation found:** Fix immediately, re-push, re-scan. Do not proceed to Step 2 until Step 1 passes cleanly.

## Step 2: Spec Compliance Matrix

For each item, verify compliance against every applicable governing spec principle. Build a matrix:

| Spec Principle | Applies? | Check | Result |
|----------------|----------|-------|--------|
| [principle name] | Yes/No | [what was checked] | PASS/FAIL |

**If any row fails:** Fix immediately, re-push, re-audit. Do not proceed to Step 3 until Step 2 passes.

## Step 3: Functional Test

Execute the test cases defined in the item's handover doc section. For each test case:

1. Send the test payload
2. Verify the expected behavior
3. Record actual result

Format:
```
Test N: [description]
  Input: [payload or action]
  Expected: [behavior]
  Actual: [what happened]
  Result: PASS / FAIL
```

**If any test fails:** Diagnose, fix, re-push, re-test. If the test fails after 2 fix attempts, trigger the rollback contract.

## Full Validation (After All Items)

After all items are complete, run a comprehensive pass:

1. Re-fetch ALL modified workflows
2. Run the full code scan across all of them in one script
3. Verify no cross-item regressions (item 5 did not break item 3)
4. If E2E test suite pass rate is a success criterion, trigger a test run and verify the target rate
