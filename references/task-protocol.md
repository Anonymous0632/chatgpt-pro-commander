# Pro 指挥任务协议

## 状态机

一个新的用户目标生成一个 `task_id`。同一目标的追问、纠错和复审继续使用同一任务与同一 ChatGPT 会话；明显独立的目标必须使用新的任务和会话。

```text
PRECHECK → PACKAGED → PLAN_PENDING → PLAN_ACCEPTED → EXECUTING
                                                      ↓
DONE ← REVIEW_PASSED ← REVIEW_PENDING ← EVIDENCE_READY
                         │
                         ├─ REVISE → EXECUTING（只允许第二次执行）
                         ├─ BLOCKED
                         └─ ERROR
```

`DONE`、`BLOCKED` 和 `ERROR` 是终态。终态任务不能复活；用户后续授权的进一步修正创建新的 `task_id`。

## 任务标识

- `task_id`：任务全程不变的 UUID。
- `message_id`：每次 PLAN 或 REVIEW 请求的新 UUID。
- `response_id`：Pro 每次回复的新 UUID。
- `reply_marker`：每次请求的随机完成标记，格式为 `[[PRO_COMMANDER_REPLY_<随机值>]]`。
- `iteration`：初始执行为 `1`，唯一一次自动修正为 `2`。

发送防重键是 `(task_id, message_id)`；回复防重键是 `(task_id, response_id)`。一个 `message_id` 最多消费一个有效回复。

## PLAN 请求

浏览器正文以此开头，并附上源码/证据包：

````markdown
PRO_COMMANDER/1 REQUEST

```json
{
  "protocol": "PRO_COMMANDER/1",
  "task_id": "<UUID>",
  "message_id": "<UUID>",
  "phase": "PLAN",
  "iteration": 1,
  "reply_marker": "[[PRO_COMMANDER_REPLY_<随机值>]]",
  "workspace": "<仅项目目录名>",
  "objective": "<用户目标>",
  "acceptance_criteria": ["<可验证标准>"],
  "authorized_actions": ["<本次允许动作>"],
  "forbidden_actions": ["<未授权或禁止动作>"],
  "known_facts": ["<已由本地证据确认的事实>"],
  "unknowns": ["<仍需判断的事项>"]
}
```

你是技术指挥者。请基于实际收到的附件制定决策完整的实施方案，明确取舍、风险、实施顺序和真实测试标准。不要声称读取未上传的本地路径，不要声称执行过本地命令。请提供简洁依据摘要，不要输出隐藏思维链。

严格使用下述 RESPONSE 格式，并以 reply_marker 作为最后一行。
````

在进入浏览器发送步骤前，使用 `scripts/validate_request.py` 校验请求正文；校验失败时不得发送。

## REVIEW 请求

复审继续使用同一会话，`phase` 改为 `REVIEW`，`iteration` 与刚完成的执行次数一致。附件必须包含实际修改、测试结果和未验证项。正文说明：

- 检查实现是否满足最初目标和验收标准；
- 区分确认缺陷、证据不足和可选改进；
- 只有无实质缺陷且真实必需检查通过时才返回 `PASS`；
- `REVISE` 必须给出最小、完整、可执行的修正；
- 无法判断或依赖外部条件时返回 `BLOCKED`。

## 唯一有效的 Pro 回复

````markdown
PRO_COMMANDER/1 RESPONSE

```json
{
  "protocol": "PRO_COMMANDER/1",
  "task_id": "<原 task_id>",
  "response_id": "<新 UUID>",
  "in_reply_to": "<请求 message_id>",
  "phase": "PLAN|REVIEW",
  "iteration": 1,
  "verdict": "NONE|PASS|REVISE|BLOCKED",
  "next_action": "EXECUTE|COMPLETE|REPAIR|STOP",
  "reasoning_brief": "<假设、证据权重、取舍和最强反方意见的简洁摘要>",
  "plan_or_findings": ["<计划项或发现>"],
  "acceptance_checks": ["<要运行或已判断的检查>"],
  "risks": ["<风险或未验证项>"],
  "evidence_used": ["<实际附件及其中的相对路径/证据>"]
}
```

[[PRO_COMMANDER_REPLY_<与请求完全相同的随机值>]]
````

PLAN 只能使用 `verdict: NONE` 与 `next_action: EXECUTE`。REVIEW 必须使用下列对应关系：

- `PASS` → `COMPLETE`
- `REVISE` → `REPAIR`
- `BLOCKED` → `STOP`

回复缺字段、增加未知顶层字段、ID 不匹配、阶段错误、标记缺失、标记不是最后一行或回复仍在生成时都不能推进状态。

使用 `scripts/validate_reply.py` 校验回复，并用 ledger 阻止重复消费。请求与回复的 marker 都必须符合 `[[PRO_COMMANDER_REPLY_<32 位小写十六进制随机值>]]`。

## 计划门禁与纠错

Codex 不盲目执行 PLAN。若发现越权、事实冲突、无法满足的依赖或测试标准不成立，应在同一会话发送一个新的 PLAN 纠错请求，附上最小证据并保留原 `task_id`。该纠错不消耗执行迭代，但仍需要新的 `message_id`、回复标记和发送确认。

Codex 只校验权限、安全和可复现事实；架构取舍、实现偏好和验收判断由 Pro 主导。

## 执行与复审预算

- 第一次被接受的 PLAN 进入 `iteration: 1`。
- REVIEW(1) 返回 `REVISE` 时，Codex 可按最小修正进入 `iteration: 2`。
- REVIEW(2) 再次返回 `REVISE` 或无法通过时，当前任务转为 `BLOCKED`。
- 修复预算不允许范围扩大。新的产品目标、部署、数据迁移或额外外部操作需要用户另行授权。
