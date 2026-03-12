# Session Continuity File

## Purpose

This file is produced at the end of every session. It is the bootstrap artifact for the next session. When a session completes partially (items remain), the next session reads this file to pick up exactly where the last one left off.

## File Location

`/home/claude/session-continuity.json`

Also pushed to GitHub alongside the Session Issue Report.

## Schema

```json
{
  "session_id": "string — [TITLE]-[DATE]",
  "model": "string — claude-opus-4-6 or claude-sonnet-4-6",
  "skill_version": "string — from VERSION file",
  "started_at": "string — ISO 8601 timestamp",
  "completed_at": "string — ISO 8601 timestamp",
  "operating_mode": "string — non-stop | checkpoint | research-first",

  "items_total": "integer",
  "items_completed": [
    {
      "item": "integer — item number",
      "title": "string",
      "status": "COMPLETED",
      "validation": "PASS",
      "git_tag": "string — post-item-N"
    }
  ],
  "items_remaining": [
    {
      "item": "integer",
      "title": "string",
      "status": "NOT_STARTED | IN_PROGRESS",
      "notes": "string — any relevant context for the next session"
    }
  ],
  "items_blocked": [
    {
      "item": "integer",
      "title": "string",
      "status": "BLOCKED",
      "reason": "string — why it is blocked",
      "unblock": "string — what is needed to unblock",
      "git_tag": "string — pre-item-N (reverted state)"
    }
  ],

  "instance_state": {
    "workflows_modified": ["string — workflow IDs that were changed"],
    "workflows_needing_toggle": ["string — workflow IDs that need off/on toggle in UI"],
    "datatables_modified": ["string — DataTable IDs that were changed"],
    "variables_created": ["string — variable names created this session"],
    "manual_cleanup_needed": [
      {
        "type": "string — datatable_rows | variable | other",
        "description": "string — what needs manual cleanup",
        "location": "string — where"
      }
    ]
  },

  "discovered_issues": [
    {
      "issue_number": "integer",
      "description": "string",
      "classification": "string — permanently_fixed | band_aid | worked_around | deferred | self_corrected",
      "affects_remaining_items": "boolean"
    }
  ],

  "git_snapshot": "string — final commit hash",
  "governing_spec_url": "string — URL used for spec fetch",

  "next_session_bootstrap": "string — exact command or instructions for the next session to start",
  "next_session_notes": "string — anything the next session needs to know"
}
```

## Usage in Next Session

The next session's handover doc should include:

```markdown
## Previous Session
Continuity file: [GitHub URL to session-continuity.json]
Load this file at bootstrap. Skip completed items. Resume from remaining items.
```

The next session's bootstrap sequence:
1. Load the skill
2. Fetch the continuity file
3. Verify completed items are still valid (spot-check 1-2)
4. Resume from remaining items
