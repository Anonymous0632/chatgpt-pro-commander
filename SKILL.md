---
name: chatgpt-pro-commander
description: When the ChatGPT Pro commander workflow is globally enabled, or the user explicitly invokes $chatgpt-pro-commander, use the verified Pro mode in the signed-in ChatGPT Web Chat interface to plan, decide, and review a new task while Codex independently performs local work and real tests. Do not use for workflow control requests, a task the user explicitly exempts from Pro, or a continuation already bound to a task_id.
---

# ChatGPT Pro Commander

Send each new objective to the exact `Pro` mode in ChatGPT Web for planning, let Codex execute locally, and return real results to the same Pro conversation for final review. Pro is the technical commander. Codex is the only local file writer, command executor, and test runner.

## Non-substitutable boundaries

- Accept only a semantically verified `Pro` selection in the official ChatGPT Web **Chat** interface. A subscription badge, text mentioning Pro, a standard model, Work mode, an API model, or Codex reasoning is not a substitute.
- Follow the current action-time confirmation rules of the selected browser surface before sending. Scripts may prepare content, validate state, and prevent duplicates, but may not replace the user's required send confirmation through extensions, CDP, coordinate clicks, or page injection.
- Never read or reuse cookies, browser storage, login tokens, passwords, verification codes, or session databases.
- Pro advice never expands user authorization. Commits, pushes, pull requests, deployments, releases, database migrations, production configuration, and real-user data operations still require explicit authorization in the current task.
- Pro may not claim to have read a local path, changed a local file, or run a local test. Only actually uploaded attachments and execution evidence recorded by Codex count.
- If the model cannot be verified, attachment delivery is uncertain, a response is incomplete, or protocol markers do not match, stop and report the condition. Never silently fall back to another model.

## Reference routing

For every new task, read [Task protocol](references/task-protocol.md).

- Before the first ChatGPT Web action, read [Model and browser gates](references/model-and-browser-gates.md).
- Before sharing local files, source, logs, or test evidence, read [Attachment and safety policy](references/attachment-policy.md).
- For uncertain sends, long generation, interrupted pages, or final reporting, read [Recovery and reporting](references/recovery-and-reporting.md).
- For installation, workflow controls, global default invocation, and examples, read [Usage](references/usage.md).

## Responsibilities

### ChatGPT Pro

- Define the problem, success criteria, implementation plan, tradeoffs, risks, and test decision rules.
- Produce `PLAN` and `REVIEW` responses based only on evidence actually received.
- Return `PASS`, `REVISE`, or `BLOCKED` during REVIEW.
- Provide a concise rationale, assumptions, evidence weighting, and strongest counterargument. Do not request or expose hidden chain-of-thought.

### Codex

- Read repository rules and establish the baseline, authorization, and executable environment.
- Select the smallest sufficient evidence set, build safe attachments, and scan for credentials.
- Check that the Pro plan stays within authorization and agrees with source facts and command output.
- Perform only authorized local changes and commands, and preserve actual test results.
- When a Pro judgment conflicts with reproducible facts, return concrete evidence to the same conversation for reconsideration.

## Workflow

1. **Mode check:** For implicit invocation, confirm the persistent workflow state is enabled. An explicit `$chatgpt-pro-commander` invocation may run once even when the workflow is paused or disabled.
2. **Local preflight:** Read applicable `AGENTS.md` files, project documentation, dependency manifests, the Git branch, and working-tree status. Preserve existing changes.
3. **Task model:** Generate a UUID `task_id` and record the objective, acceptance criteria, scope, prohibited operations, verified facts, unknowns, and decisions required from Pro.
4. **Evidence package:** Build the source ZIP, Markdown bundle, safety report, and manifest. Record commit, branch, status, size, and SHA-256.
5. **Web preflight:** Use the browser surface explicitly selected by the user, or the runtime default when none was specified. Verify login, Chat mode, and the exact Pro selection.
6. **PLAN:** Start a new ChatGPT conversation, prepare the protocol request and attachments.
7. **Plan gate:** Validate task, message, phase, and unique reply marker. Check authorization, safety, and source facts before execution. Return minimal correction evidence to the same Pro conversation when necessary.
8. **Execution:** Codex changes local files and runs tests. Preserve failures; never represent mocks, static checks, or a successful build as real-device, production, or hosted validation.
10. **Closure:** After `PASS`, perform a final local fact check. One `REVISE` permits one repair and another REVIEW. A second non-`PASS` result ends as `BLOCKED`.
11. **Delivery:** Separate the plan, actual changes, tests, Pro verdict, residual risks, and the exact commit/push/PR/deployment/release status.

## Evidence gate

Codex may refuse execution or return a decision to Pro only when it is:

- outside user authorization or product scope;
- contrary to safety, privacy, repository rules, or irreversible-operation boundaries;
- dependent on unavailable files, tools, permissions, or environments;
- inconsistent with locatable source, command output, file hashes, or real test results; or
- unable to satisfy explicit acceptance criteria.

Implementation preferences remain Pro decisions. When this gate fires, provide concrete file locations, error text, test results, or authorization boundaries.

## Stop conditions

- Pause for the user when login, account selection, a verification code, passkey, or two-factor authentication is required.
- If exact Pro cannot be seen or semantically verified, end as `BLOCKED`.
- Never resend while state is `SENT` or `UNKNOWN`; recover only the original conversation.
- Missing markers, uncertain attachment delivery, truncated responses, or protocol mismatches end as `ERROR`.
- After one initial execution and one repair, another failure ends as `BLOCKED`.
- Stop the current phase and preserve evidence when the user pauses, revokes authorization, or changes the objective.

## Final output

Report at least:

- `task_id`, final state, and ChatGPT conversation link;
- verified active model label, browser surface, and confirmation result;
- source baseline plus attachment names, sizes, and SHA-256 values;
- Pro PLAN, actual Codex work, and final Pro REVIEW;
- requested repairs and the result of each repair;
- tests actually run, pass/fail/not-run states, and unverified risks; and
- whether the result is only local or was committed, pushed, opened as a PR, deployed, or released.
