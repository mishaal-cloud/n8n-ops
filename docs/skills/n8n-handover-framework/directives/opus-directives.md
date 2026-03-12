# Opus 4.6 Directives

## Thinking Configuration

You run adaptive thinking at high effort by default. This is correct for complex items. Do not add self-instructions like "think carefully" — you are already proactive. These cause overthinking loops.

**Think deeply on:**
- Code node rewrites that must satisfy multiple spec principles
- Debugging failures where the root cause is not obvious from the error message
- Architecture decisions (new workflow structure, node layout, data flow design)
- Validation audits where you cross-reference code against the governing spec
- Any task where getting it wrong means re-doing 30+ minutes of work

**Skip extended reasoning on:**
- DataTable row inserts with known values
- Variable creation
- File operations (copy, move, create)
- Git snapshots
- Toggling workflows off/on after API updates
- Re-running a validation script you have already written

When executing a known procedure with no ambiguity, respond directly without extended reasoning.

## Anti-Patterns to Avoid

**Overthinking trivial choices:** You tend to reason extensively about things like whether a variable should be named `DEFAULT_CLIENT` or `DEFAULT_TENANT`. Pick the most descriptive name, commit, move on. The spec says "config-driven" — it does not specify naming conventions. Do not invent constraints.

**Reasoning loops:** If you catch yourself reconsidering the same decision 3+ times, stop. Pick the best-evidence approach, commit, execute. Do not revisit unless new evidence contradicts your reasoning.

**Unnecessary depth on simple tasks:** You sometimes generate superfluous explanations for straightforward operations. A DataTable insert does not need architectural commentary. Match output verbosity to task complexity.

## Strengths to Leverage

**128K output limit:** Use this for single-pass audit reports. Consolidate all validation into one comprehensive response rather than chunking across multiple turns.

**Strong context recall:** At 200K tokens, cross-reference the governing spec directly. Re-read the actual spec text during audits — do not work from memory of what it says.

**First-attempt correctness:** You have higher first-attempt accuracy than Sonnet on multi-constraint tasks. Take the extra thinking time on Code node rewrites — the cost of thinking is lower than the cost of a fix-and-re-push cycle.

**Agentic persistence:** You sustain quality across long sessions (METR measured 14.5-hour task horizon). Do not ask for confirmation between items. The handover doc is your authorization.

## Self-Review Checklist

Before pushing ANY Code node, verify:
1. Any hardcoded IDs, URLs, or tenant names? → Must use `$vars`
2. Any secrets loaded but unused? → Remove dead references
3. Any missing error handling or try/catch? → Add
4. Any missing runbook header? → Add
5. Does it respect all known platform bugs? → Check governing spec
6. Any HTML injection risk in user-facing output? → Sanitize
7. Does it comply with n8n Cloud design principles? → Zero hardcoding, frontend-agnostic, scalable, multi-client ready, flexible, secure, simple

## Compaction Thresholds

These override the defaults in the compaction strategy protocol:
- **50% context capacity:** Dump session state to `/home/claude/session-state.json`
- **70% context capacity:** Switch to terse output — actions and results only, no explanations
- **85% context capacity:** Do NOT start new items. Finalize current item. Produce exit artifacts.

## Error Diagnosis

Read full error responses, not just status codes. You can diagnose root causes from error message text faster than workarounds can be built. Before any workaround: search for the official fix first. Your research ability is your primary advantage.

## Session Discipline

- Front-load the hardest item while context is freshest
- Git snapshot before AND after each item
- Run automated principle audit after every push — do not eyeball it
- Maintain the running issue log in session-state.json for the mandatory Session Issue Report
