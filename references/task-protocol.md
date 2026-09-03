# Pro commander task protocol

## State machine and identifiers

```text
PRECHECK -> PACKAGED -> PLAN_PENDING -> PLAN_ACCEPTED -> EXECUTING
                                                       |
DONE <- REVIEW_PASSED <- REVIEW_PENDING <- EVIDENCE_READY
                          |-- REVISE -> EXECUTING (one repair only)
                          |-- BLOCKED
                          `-- ERROR
```

`DONE`, `BLOCKED`, and `ERROR` are terminal. A new objective gets a new UUID `task_id`; follow-ups retain the same task and conversation. Each PLAN/REVIEW request gets a UUID `message_id`; each Pro response gets a UUID `response_id`. Use a fresh `[[PRO_COMMANDER_REPLY_<32 lowercase hex characters>]]` marker for every request. Iteration 1 is initial execution; iteration 2 is the only automatic repair.

## Request

Start the browser message with:

````markdown
PRO_COMMANDER/1 REQUEST

```json
{
  "protocol": "PRO_COMMANDER/1",
  "task_id": "<UUID>",
  "message_id": "<UUID>",
  "phase": "PLAN|REVIEW",
  "iteration": 1,
  "reply_marker": "[[PRO_COMMANDER_REPLY_<32 lowercase hex characters>]]",
  "workspace": "<project directory name only>",
  "objective": "<user objective>",
  "acceptance_criteria": ["<verifiable criterion>"],
  "authorized_actions": ["<authorized action>"],
  "forbidden_actions": ["<prohibited or unauthorized action>"],
  "known_facts": ["<locally verified fact>"],
  "unknowns": ["<decision still required>"]
}
```

Act as the technical commander using only evidence actually attached. For PLAN, produce a decision-complete implementation plan, tradeoffs, risks, sequence, and real test standards. For REVIEW, evaluate the actual diff, test output, and unknowns against the original objective. Do not claim local access or local execution. Provide a concise rationale, not hidden chain-of-thought. Use the exact RESPONSE schema and put reply_marker on the last line.
````

Run `scripts/validate_request.py` before sending. REVIEW remains in the same conversation and uses the iteration just executed.

## Response

````markdown
PRO_COMMANDER/1 RESPONSE

```json
{
  "protocol": "PRO_COMMANDER/1",
  "task_id": "<original task_id>",
  "response_id": "<new UUID>",
  "in_reply_to": "<request message_id>",
  "phase": "PLAN|REVIEW",
  "iteration": 1,
  "verdict": "NONE|PASS|REVISE|BLOCKED",
  "next_action": "EXECUTE|COMPLETE|REPAIR|STOP",
  "reasoning_brief": "<concise assumptions, evidence weighting, tradeoffs, and strongest counterargument>",
  "plan_or_findings": ["<plan item or finding>"],
  "acceptance_checks": ["<required or assessed check>"],
  "risks": ["<risk or unverified item>"],
  "evidence_used": ["<actual attachment and relative path/evidence>"]
}
```

[[PRO_COMMANDER_REPLY_<exact request value>]]
````

PLAN requires `NONE -> EXECUTE`. REVIEW requires `PASS -> COMPLETE`, `REVISE -> REPAIR`, or `BLOCKED -> STOP`. Reject missing/extra fields, mismatched IDs or phase, incomplete generation, or a missing/non-final marker. Run `validate_reply.py` and use its ledger to prevent duplicate consumption.

Codex gates only authorization, safety, reproducible facts, dependencies, and acceptance feasibility. When necessary, send a new correction request in the same conversation with a new message ID, marker, and confirmation. REVIEW(1) may trigger one repair and REVIEW(2); another `REVISE` or inability to pass ends `BLOCKED`. Repairs cannot expand scope.
