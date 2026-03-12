# Lean Handover Document Template

Use this template for the session-specific part of a handover. The n8n-handover-framework skill handles all execution procedures, validation protocols, and reporting standards. This document handles only the **what** — items, constraints, resources, and success criteria.

---

## Copy Below This Line

---

# [Title]

**Date:** [YYYY-MM-DD]
**Operating Mode:** [Non-stop / Checkpoint / Research-first]
**Skill:** n8n-handover-framework (load before starting)
**Governing Spec:** [GitHub raw URL to governing-spec.md]

## Success Criteria

[Define what "done" looks like. Concrete, verifiable.]

- [ ] [criterion 1]
- [ ] [criterion 2]

## Constraints

**ABSOLUTE** (zero exceptions):
- [constraint]

**SOFT** (may violate with documented justification):
- [constraint]

## Parallel Sessions

[OPTIONAL — include only if other sessions are running]

A separate session is running on [description], covering:
- [item]

DO NOT touch these workflows: [list]

## Key Resources

### Workflow IDs

| Workflow | ID | Status | Notes |
|----------|----|--------|-------|
| | | | |

### DataTables

| Table | ID | Variable | Purpose |
|-------|----|----------|---------|
| | | | |

### Variables

| Variable | Purpose |
|----------|---------|
| | |

## Items

### Item #1: [Title] ([BLOCKER/HIGH/MEDIUM/LOW])

**Problem:** [What is broken and why it matters]

**Scope:** [Which workflows/tables to modify. Explicit boundaries.]

**Implementation:**
[Step-by-step plan. Code snippets where approach is non-obvious.]

**Test Cases:**
1. [Input → Expected output]
2. [Input → Expected output]

**Acceptance Criteria:**
- [ ] [verifiable criterion]
- [ ] [verifiable criterion]

### Item #2: [Title] ([Priority])

[Same structure as Item #1]

## Execution Order

1. Bootstrap (skill handles this)
2. Item #[N] — [reason for ordering]
3. Item #[N] — [reason for ordering]
4. After all items: Full validation
5. Produce exit artifacts (skill handles this)
