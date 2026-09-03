# Attachment and safety policy

ChatGPT Web cannot read a local path by name. Source, configuration, documentation, logs, images, and test results that affect a decision must be uploaded or included in the Markdown bundle.

## Scope

- Share the smallest sufficient evidence set. Use a few source files for small work; use one source ZIP plus one searchable Markdown bundle for multi-file work.
- Never package Home, Documents, Downloads, Desktop, or a multi-project parent directory.
- Use project-relative paths only. Do not expose personal absolute paths.
- Give independent complex tasks separate packages and conversations.

## Hard exclusions

Never include `.env` variants, passwords, authentication configuration, API keys, tokens, JWTs, authorization/cookie headers, private keys, browser profiles/storage, Codex `auth.json`, `.git`, dependencies, virtual environments, build output, caches, databases, runtime state, symlink targets, out-of-root files, or unverified binaries.

Ordinary source and authorized business content need no gratuitous redaction. Email addresses, phone numbers, and similar data are warnings, not automatic redactions; disclose their category during the required send confirmation.

## Build a package

Create a task evidence directory outside the project, then run:

```bash
python3 <skill-dir>/scripts/prepare_packet.py \
  /absolute/path/to/project \
  --task-file /absolute/path/to/TASK.md \
  --task-id <task-uuid> \
  --output-dir /absolute/path/outside/project/run
```

Git projects include tracked and unignored untracked files; non-Git projects recursively select ordinary files. Use repeated `--include relative/path` options to narrow scope. The script produces source ZIP, Markdown bundle, manifest, and safety report; records Git state and artifact hashes; and blocks ZIP/bundle creation on high-confidence credentials or personal absolute paths. Reports never copy matched secret values.

## Upload and retain evidence

Follow the chosen browser skill's file-upload procedure. After upload, re-read attachment elements and verify every expected filename plus the request prefix, `task_id`, and marker. Attachment cards prove selection, not that Pro read the content; `evidence_used` must match actual attachments.

Persist task/response IDs, Git baseline, attachment names/sizes/hashes, safety report, extracted PLAN/REVIEW, test evidence, and final report in a private task evidence directory. Never retain cookies, tokens, raw accessibility trees, account email, or browser session data.
