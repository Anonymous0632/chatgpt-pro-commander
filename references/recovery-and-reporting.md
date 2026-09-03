# Recovery and reporting

## Duplicate-safe sending

Each outgoing message has its own state file:

- `NOT_SENT`: no send attempt occurred; sending is allowed only after revalidation and confirmation.
- `UNKNOWN`: the state is armed or the click/result could not be proven; never resend.
- `SENT`: submission evidence was observed; never resend.

Create state with `dispatch_state.py init`. After the final checks and user confirmation, run `arm` immediately before one click; this writes `UNKNOWN` and attempt count 1. Run `mark-sent` only after new page evidence proves submission. Never delete or reset a `SENT/UNKNOWN` record to bypass duplicate protection.

## Recover the original conversation

Store the conversation URL only in private local evidence. Prefer the existing tab; otherwise use that URL and the task marker to locate the one original conversation. Verify the latest user message's `task_id`, `message_id`, and marker before waiting or extracting. If the original conversation cannot be uniquely identified, end as `ERROR`.

## Wait and extract

Check generation state every 30–60 seconds without refreshing, prompting “continue,” or resubmitting. Give the user concise progress at least every 60 seconds. A stage may wait up to 45 minutes, then reconnect and inspect the same conversation once before reporting `BLOCKED` or `ERROR`. Extract only the latest complete assistant turn, normalize escaped underscores, require the exact marker as the final line, and run `validate_reply.py`.

## Failure rules

- Authentication: pause for the user, then resume PRECHECK.
- Pro unavailable: `BLOCKED`; no model or API fallback.
- Missing attachment: re-upload only while `NOT_SENT`; otherwise recover the original conversation.
- Incomplete composer: do not send; re-read and verify it.
- Missing marker after completed generation: `ERROR`.
- Pro requests unauthorized work: return the boundary and evidence; ask the user only for genuinely expanded authority.
- Test failure: preserve the real output and enter REVIEW; never report it as a pass.

## Final report

Report task/final state, private conversation link, browser/model gate, send confirmations, Git and attachment baseline, Pro PLAN, actual changes, Pro REVIEW and repairs, passed/failed/not-run tests, residual risk, and exact local/commit/push/PR/deployment/release status. Write “not run” or “not verified” when evidence is absent.
