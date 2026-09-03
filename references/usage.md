# Installation and usage

## Prerequisites

- A ChatGPT plan that exposes `Pro` in the ChatGPT Web model selector.
- A signed-in supported in-app browser or Chrome profile and its corresponding Codex browser-control skill.
- Python 3.10 or newer.
- Authorization to share the selected project files with ChatGPT.

## Manual installation

Copy the complete `chatgpt-pro-commander` folder into the Codex user skills directory so the entrypoint is `~/.codex/skills/chatgpt-pro-commander/SKILL.md`, then restart or refresh Codex. Invoke it explicitly with:

```text
$chatgpt-pro-commander Have verified ChatGPT Web Pro plan and review this task while Codex executes it.
```

To make it the default for new objectives, manually merge [global-agents-snippet.md](global-agents-snippet.md) into the existing global `~/.codex/AGENTS.md` without overwriting other instructions, then run:

```bash
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py enable
```

## Controls

```bash
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py status
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py enable
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py pause
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py resume
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py disable
```

An absent or invalid state fails closed as disabled. Explicit invocation permits one run even while globally paused or disabled. “Do not use Pro for this task” bypasses only the current task without changing global state.

## Per-task behavior

Codex checks the repository and authorization, builds and hashes a safe evidence package, verifies exact Pro in ChatGPT Web, prepares PLAN, and requests action-time confirmation immediately before sending. After local execution and real tests, it packages REVIEW evidence and requests confirmation again. Pro returns `PASS`, `REVISE`, or `BLOCKED`; only one automatic repair is allowed. A normal task therefore has two sends, with extra sends only for correction or the one repair.

## First live validation

After Pro is available, use a small non-sensitive project to verify model selection, attachment upload, PLAN, one harmless local change, REVIEW, conversation recovery, markers, manifest, and hashes. Until this succeeds, describe the skill as statically and synthetically tested, not live end-to-end verified.

## Limitations

- ChatGPT Web UI and labels can change; always inspect the live semantic control.
- A Pro subscription is not API credit; this skill has no API fallback.
- Scripts automate preparation, validation, and duplicate protection, not action-time send confirmation.
