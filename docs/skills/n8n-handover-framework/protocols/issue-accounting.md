# Issue Accounting Protocol

This is a MANDATORY exit gate. The session is not complete until this report is produced and pushed to GitHub.

## Report Location

`docs/SESSION-ISSUE-REPORT-[NAME]-[DATE].md`

Where NAME is a short descriptor (e.g., "gateway-hardening") and DATE is ISO format (e.g., 2026-03-12).

## Report Structure

### Header

```markdown
# Session Issue Report: [Title]
**Date:** [ISO date]
**Model:** [claude-opus-4-6 or claude-sonnet-4-6]
**Skill Version:** [from VERSION file]
**Items Completed:** N / M
**Items Blocked:** N
```

### Section 1: Complete Issue List

Every error encountered during the session, no matter how small. For each:

| # | What Happened | When | Root Cause |
|---|--------------|------|------------|
| 1 | [exact error] | [item N, step M] | [root cause] |

### Section 2: Resolution Classification

Every issue classified as exactly ONE of:

| Category | Definition |
|----------|-----------|
| **Permanently fixed** | Root cause resolved. Will not recur. |
| **Band-aid** | Symptom addressed, root cause remains. |
| **Worked around** | Alternative path taken, original problem still exists. |
| **Ignored / Deferred** | Known issue, not addressed this session. |
| **Self-inflicted, self-corrected** | Execution mistake made and corrected during session. |

### Section 3: Resolution Details

For every issue:

```markdown
#### Issue #N: [brief title]
**Classification:** [one of the five categories]
**What I did:** [action taken]
**How I did it:** [technical details]
**Why this approach:** [reasoning for chosen resolution]
**Revert plan:** [how to undo if needed — required for band-aids and workarounds]
```

### Section 4: Summary Table

| Category | Count | Issue Numbers |
|----------|-------|---------------|
| Permanently fixed | N | #1, #3, ... |
| Band-aid | N | #5, ... |
| Worked around | N | ... |
| Ignored / Deferred | N | ... |
| Self-inflicted, self-corrected | N | ... |

### Section 5: Remaining Risks

Anything that could cause problems in future sessions or production. For each risk:
- What could happen
- Likelihood (low/medium/high)
- Impact (low/medium/high)
- Recommended mitigation

### Section 6: Spec Violations Found and Fixed

Every governing spec violation discovered during the session:

| Violation | Spec Principle | Where Found | How Fixed |
|-----------|---------------|-------------|-----------|
| [description] | [principle] | [workflow/node] | [fix applied] |

### Section 7: Scope Deviations

Any soft constraint violations (changes outside the defined scope):

| Deviation | Justification | Impact |
|-----------|--------------|--------|
| [what was changed outside scope] | [why it was necessary] | [what it affects] |
