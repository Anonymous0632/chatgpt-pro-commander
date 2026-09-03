# ChatGPT Pro Commander

> English version is followed by the complete Chinese version.

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

---

# ChatGPT Pro 指挥 Skill（中文版）

使用经过验证的 ChatGPT 网页 **Pro** 模式负责规划与复审，由 Codex 执行获得授权的本地修改和测试。

这个仓库包含一个 Codex Skill。它不会替换 Codex 的底层模型，也不提供 ChatGPT 订阅的 API 访问；它通过浏览器中的 ChatGPT Pro 会话、结构化协议、证据和安全门禁协调规划、执行与复审。

## 功能

- ChatGPT 网页 Pro 负责目标拆解、方案、取舍、风险和复审标准。
- Codex 读取仓库、修改本地文件、运行真实测试并记录证据。
- 同一个 ChatGPT 会话复审实际 diff 和测试结果。
- PLAN/REVIEW 使用任务 UUID、阶段、迭代次数和唯一回复标记。
- 发送状态使用 `NOT_SENT`、`UNKNOWN`、`SENT`，防止不确定结果导致重复提交。
- 源码包在上传前扫描并记录 Git 基线、文件清单、大小和 SHA-256。
- `REVISE` 后最多允许一次自动修正；再次未通过则结束为 `BLOCKED`。

## 重要边界

- 只有 ChatGPT 网页 Chat/聊天界面中语义化确认的活动 `Pro` 选项才算有效。套餐徽标、Work/工作模式、API 模型、普通模型或 Codex 推理均不能替代。
- 脚本只负责准备、校验和防重复发送，不能绕过浏览器在实际发送前要求的动作时确认。
- 不得向 Skill 提供 Cookie、浏览器存储、密码、Token、API Key、私钥、验证码或会话数据库。
- Pro 的建议不会扩大用户授权；提交、推送、PR、部署、发布、迁移、线上配置和真实用户数据操作仍需当前任务明确授权。
- 本仓库版本尚未在真实 ChatGPT Pro 账号上完成端到端验证；完成首次真实验证前，不得将其称为生产验证通过。

## 安装

将文件夹复制到 Codex 用户 Skills 目录：

```bash
cp -R /path/to/chatgpt-pro-commander ~/.codex/skills/chatgpt-pro-commander
```

重启 Codex 或新建任务后，可显式调用：

```text
$chatgpt-pro-commander 使用已验证的 ChatGPT 网页 Pro 规划并复审这个任务，由 Codex 在本地执行。
```

如需对所有新目标默认调用，先手动把 [`references/global-agents-snippet.md`](references/global-agents-snippet.md) 合并进 `~/.codex/AGENTS.md`，再启用持久状态：

```bash
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py enable
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py status --json
```

状态支持 `enable`、`pause`、`resume`、`disable` 和 `status`。状态文件缺失或无效时按停用处理；显式调用仍可单次运行。

## 典型流程

1. Codex 完成本地仓库和权限预检。
2. `prepare_packet.py` 生成源码 ZIP、Markdown Bundle、安全报告和 Manifest。
3. 浏览器控制面验证 ChatGPT Chat 和活动的精确 Pro 模式。
4. Codex 准备 PLAN，并在发送前遵守控制面的动作时确认。
5. Pro 返回计划；Codex 校验授权和可复现事实后执行并测试。
6. Codex 准备 REVIEW 证据，并在发送前再次遵守确认要求。
7. Pro 返回 `PASS`、`REVISE` 或 `BLOCKED`；最多自动修正一次。

如果发送结果不确定，状态变为 `UNKNOWN`，不得再次提交；只能恢复原会话。

## 目录结构

```text
chatgpt-pro-commander/
├── SKILL.md                         # Skill 入口和路由规则
├── agents/openai.yaml               # 显示元数据和调用策略
├── references/                      # 协议、浏览器、附件、恢复和使用说明
├── scripts/
│   ├── prepare_packet.py             # 安全打包、扫描、Manifest 和哈希
│   ├── validate_browser_gate.py      # Chat/Pro 精确门禁
│   ├── validate_request.py           # PLAN/REVIEW 请求校验
│   ├── validate_reply.py             # Pro 回复和 ledger 校验
│   ├── dispatch_state.py             # NOT_SENT/UNKNOWN/SENT 状态机
│   └── mode_control.py               # 启用/暂停/恢复/停用
├── tests/                           # 单元测试和行为契约测试
└── evals/evals.json                 # 机器可读行为场景
```

## 本地验证

在 Skill 根目录运行：

```bash
python3 -m py_compile scripts/*.py tests/*.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/run_behavior_evals.py
```

也可以使用 `skill-creator` Skill 提供的 `quick_validate.py` 执行官方结构校验。

## 首次真实验证

开通 Pro 后，使用无敏感数据的小型测试项目：验证模型选择器，上传最小 TASK 和源码，完成 PLAN，进行一次无害本地修改，再完成 REVIEW；检查 marker、Manifest、SHA-256 和会话恢复记录。静态或模拟检查不得被描述为生产验证。

## 许可证

本仓库未声明许可证。如需接受外部贡献或再分发，请先添加许可证文件。
