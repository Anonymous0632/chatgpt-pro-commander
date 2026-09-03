# Global AGENTS.md snippet

This is a manual merge example. Never overwrite an existing `AGENTS.md` automatically.

```markdown
## ChatGPT Pro Commander

For every new user objective, first read the persistent state for the installed
`chatgpt-pro-commander` Skill.

- If the user asks to enable, pause, resume, disable, or inspect the workflow, handle that
  control request locally without consulting Pro.
- If the user says the current task must skip Pro, bypass it once without
  changing the persistent state.
- If the workflow is enabled, invoke `$chatgpt-pro-commander` before making a
  substantive plan, implementation decision, or local change.
- A follow-up that continues an existing `task_id` stays in that same workflow
  and ChatGPT conversation; do not start another consultation.
- An explicit `$chatgpt-pro-commander` invocation runs once even when the
  persistent workflow is disabled.
- The workflow never expands user authorization and never bypasses the
  browser's action-time confirmation before sending.
- If state is absent, unreadable, or invalid, treat the workflow as disabled
  and report that fact instead of guessing.
```

Merge only this short block into global instructions and keep implementation details in the skill.
