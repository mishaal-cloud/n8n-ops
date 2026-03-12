# Compaction Strategy

Context is a finite resource. As it fills, recall degrades (context rot). This protocol defines proactive behaviors tied to context usage thresholds to prevent information loss.

## How Compaction Works in claude.ai

When context approaches the window limit, the system automatically summarizes older conversation turns. This is "Infinite Chats." You cannot control when it fires, but you CAN:
1. Shape what survives by maintaining external state files
2. Reduce context growth rate by being terse on execution tasks
3. Avoid starting complex items near the threshold

## Token Threshold Behaviors

Your model directives file specifies exact percentages. The general framework:

### At Early Threshold (model-specific: 40-50%)

**Action:** Dump current session state to `/home/claude/session-state.json`

Include:
- All completed items with pass/fail status
- Current item in progress and its stage
- All workflow IDs, DataTable IDs, variable names referenced this session
- Running issue log (every error encountered so far)
- Key governing spec principles in summary form (the ones relevant to remaining items)

### At Mid Threshold (model-specific: 60-70%)

**Action:** Switch to terse output mode

- No explanations between tool calls
- Report only failures, not successes
- Skip verbose validation reports — just: `Item N: PASS` or `Item N: FAIL — [reason]`
- Do not re-explain context established in earlier turns

### At High Threshold (model-specific: 75-85%)

**Action:** Stop and finalize

- Do NOT start new items
- Finalize the current item (push, validate, snapshot)
- Update session-state.json with final state
- Produce Session Issue Report for completed items
- Produce Session Continuity File for remaining items
- Inform the operator: "Context at [X]%. Completed [N/M] items. Remaining items require a new session. Session continuity file produced."

## Information That Must Survive Compaction

Whether compaction fires or not, these must be in session-state.json at all times:

1. All workflow IDs from the handover doc's Key Resources
2. All DataTable IDs and their variable name mappings
3. All n8n variables referenced or created
4. Current item number and execution stage
5. Running issue log with every error and resolution
6. Governing spec principles relevant to remaining items (abbreviated)
7. Instance access details (API URL, auth pattern)

## Self-Contained Scripts

Every script written during the session must define its own constants. Do not rely on variables printed in earlier turns — they may be summarized away after compaction.

```python
# GOOD - self-contained
BASE = "https://mmurawala.app.n8n.cloud/api/v1"
KEY = "..."  # from session bootstrap

# BAD - relies on earlier context
# Uses BASE and KEY defined 20 turns ago
```

## Compaction-Aware Item Ordering

When the execution order allows flexibility:
1. Front-load items requiring the most cross-referencing with the governing spec
2. Front-load items requiring the most inter-item coordination
3. Back-load pure execution items (DataTable inserts, variable creation, simple config)

This ensures complex work happens while the full spec is in active context.
