# Error Escalation Ladder

When encountering an error during execution, follow this ladder in order. Do not skip levels.

## Level 1: Official Documentation

**Action:** Search official docs for the exact error or the operation that failed.

- n8n docs: https://docs.n8n.io
- n8n API docs: https://docs.n8n.io/api/
- Anthropic docs (if Claude API related): https://platform.claude.com/docs
- Google API docs, HubSpot API docs, etc. as relevant

**Use web_search.** Do not rely on training data for fast-moving platforms.

**Exit condition:** Found a documented solution → apply it → continue.

## Level 2: GitHub Issues

**Action:** Search GitHub issues for the exact error message or behavior.

- n8n GitHub: https://github.com/n8n-io/n8n/issues
- Search with the exact error text, not a paraphrase

**Exit condition:** Found a confirmed issue with a fix or workaround → proceed to Level 3 with evidence.

## Level 3: Apply Documented Fixes

**Action:** Try up to 3 DISTINCT documented fixes. Not 3 variations of the same fix.

For each attempt:
1. Document what you tried
2. Document the result
3. If it worked → continue execution
4. If it failed → try the next documented fix

**Exit condition:** One of the 3 fixes works → continue. All 3 fail → proceed to Level 4.

## Level 4: Classify as Platform Bug

**Requirements for classification:**
- 3 distinct fixes attempted and documented
- Evidence that this is a platform-level issue (GitHub issue exists, or behavior contradicts official docs)
- Not a configuration or user error

**If classified as platform bug:**
Apply a workaround ONLY if ALL of these conditions are met:
1. **Security parity:** The workaround does not reduce security posture
2. **Monitoring plan:** There is a way to detect when the upstream bug is fixed
3. **Revert procedure:** The workaround can be reverted cleanly when the fix ships
4. **Documented:** The workaround is fully documented in the Session Issue Report with classification "Worked around"

If any condition is not met → proceed to Level 5.

## Level 5: Mark as BLOCKED

**Action:**
- Document the error, all 3 fix attempts, and evidence
- Mark the item as BLOCKED in session-state.json
- Record what information or platform change would unblock it
- Continue to the next item

**Do NOT:**
- Apply undocumented workarounds without security parity
- Guess at fixes without evidence
- Spend more than 15 minutes at any single level before escalating
- Ask the operator for help with technical diagnosis (research it yourself)

## Cross-Reference: Known Platform Bugs

The governing spec contains a list of known platform bugs and their workarounds. Before starting Level 1, check if the error matches a known bug. If it does, apply the documented workaround directly — no escalation needed.

Known bugs change over time. Always verify the workaround is still necessary by checking if the upstream fix has shipped.
