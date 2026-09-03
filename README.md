# ChatGPT Pro Commander

Use the verified ChatGPT Web **Pro** mode as the planning and review authority while Codex performs the authorized local implementation and testing.

This repository contains a Codex Skill. It does not replace Codex's underlying model and it does not provide API access to a ChatGPT subscription. It coordinates a browser-based ChatGPT Pro conversation with local Codex work through explicit evidence, protocol, and safety gates.

## What it does

- ChatGPT Web Pro defines the implementation plan, tradeoffs, risks, and review criteria.
- Codex reads the repository, changes local files, runs real tests, and records evidence.
- The same ChatGPT conversation reviews the actual diff and test results.
- PLAN and REVIEW messages use structured UUIDs, phases, iterations, and reply markers.
- An outgoing message uses `NOT_SENT`, `UNKNOWN`, and `SENT` duplicate-protection states.
- Source packages are scanned and hashed before they are shared with ChatGPT.
- A single automatic repair is allowed after `REVISE`; another failed review ends as `BLOCKED`.

## Important boundaries

- Only an active, semantically verified `Pro` selection in ChatGPT Web Chat counts. A Pro subscription badge, Work mode, an API model, a standard model, or Codex reasoning is not a substitute.
- Scripts automate preparation, validation, and duplicate protection. They do not bypass the browser's action-time confirmation before an external send.
- Do not provide cookies, browser storage, passwords, tokens, API keys, private keys, verification codes, or session databases to the skill.
- Pro recommendations never expand the user's authorization. Commits, pushes, pull requests, deployments, releases, migrations, production changes, and real-user data operations require explicit authorization in the current task.
- This project has not been live end-to-end tested against a ChatGPT Pro account in this repository release. Complete the first-live-validation procedure before treating it as production-proven.

## Install

Copy the folder into the Codex user Skills directory:

```bash
cp -R /path/to/chatgpt-pro-commander ~/.codex/skills/chatgpt-pro-commander
```

Restart Codex or start a new task so the Skill is discovered. The Skill is explicit by default through:

```text
$chatgpt-pro-commander Use verified ChatGPT Web Pro to plan and review this task while Codex executes locally.
```

To invoke it automatically for new objectives, manually merge [`references/global-agents-snippet.md`](references/global-agents-snippet.md) into `~/.codex/AGENTS.md`, then enable the persistent state:

```bash
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py enable
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py status --json
```

The state supports `enable`, `pause`, `resume`, `disable`, and `status`. An explicit Skill invocation can run once while the global state is disabled. The state file fails closed as disabled when it is missing or invalid.

## Typical workflow

1. Codex performs repository and authorization preflight.
2. `prepare_packet.py` creates a source ZIP, Markdown bundle, safety report, and manifest with Git and SHA-256 evidence.
3. The selected browser verifies ChatGPT Web Chat and the active Pro model control.
4. Codex prepares a PLAN request and asks for the browser's required action-time confirmation before sending.
5. Pro returns a validated plan; Codex checks authorization and reproducible facts, then implements and tests locally.
6. Codex prepares REVIEW evidence and asks for confirmation before sending it to the same conversation.
7. Pro returns `PASS`, `REVISE`, or `BLOCKED`. Only one automatic repair is permitted.

If a send result is uncertain, the message becomes `UNKNOWN` and is never submitted again. Codex recovers the original conversation instead.

## File layout

```text
chatgpt-pro-commander/
├── SKILL.md                         # Skill entrypoint and routing
├── agents/openai.yaml               # UI metadata and invocation policy
├── references/                      # Protocol, browser, attachment, recovery, and usage guides
├── scripts/
│   ├── prepare_packet.py             # Safe source package, scan, manifest, and hashes
│   ├── validate_browser_gate.py     # Exact Chat/Pro evidence gate
│   ├── validate_request.py           # PLAN/REVIEW request validation
│   ├── validate_reply.py             # Pro response and ledger validation
│   ├── dispatch_state.py             # NOT_SENT/UNKNOWN/SENT state machine
│   └── mode_control.py               # Persistent enable/pause/resume/disable state
├── tests/                           # Unit and static behavior-contract tests
└── evals/evals.json                 # Machine-readable behavior scenarios
```

## Validate locally

From the repository root:

```bash
python3 -m py_compile scripts/*.py tests/*.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/run_behavior_evals.py
```

The official Codex Skill validator can also be run with the `skill-creator` Skill's `quick_validate.py` script.

## First live validation

After ChatGPT Pro is available, use a small non-sensitive test project. Verify the model selector, upload a minimal TASK and source set, complete PLAN, make one harmless local change, complete REVIEW, and inspect the saved marker, manifest, and SHA-256 evidence. Record missing live evidence as unverified; do not call static or simulated checks production validation.

## License

No license is asserted by this repository. Add a license file before accepting external contributions or redistributing the Skill.
