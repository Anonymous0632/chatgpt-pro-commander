# 安装与使用说明（中文版草案）

## 当前交付状态

本目录是供审阅的中文版 Skill。它没有安装到 Codex，也没有修改你的全局 `AGENTS.md`、`config.toml` 或浏览器设置。英文正式版应在中文版确认后另行生成。

## 前置条件

- 已开通能够在 ChatGPT 网页模型选择器中使用 `Pro` 的方案。
- 已在准备使用的内置浏览器或 Chrome Profile 中登录 ChatGPT。
- Codex 环境安装了相应的 Browser/Chrome 控制 Skill。
- 本机有 Python 3.10 或更高版本，用于附件、协议和状态脚本。
- 项目文件属于你或你已获得向 ChatGPT 上传的授权。

## 手动安装（以后执行）

将整个 `chatgpt-pro-commander` 文件夹复制到 Codex 用户 Skills 目录，确保最终路径类似：

```text
~/.codex/skills/chatgpt-pro-commander/SKILL.md
```

重启或刷新 Codex 后，可显式输入：

```text
$chatgpt-pro-commander 请让 ChatGPT Pro 规划并审查这个任务。
```

本次交付不执行上述安装。

## 全局默认调用（以后手动启用）

1. 打开 [global-agents-snippet.md](global-agents-snippet.md)。
2. 将其中示例片段合并进现有全局 `~/.codex/AGENTS.md`，不要覆盖原文件。
3. 启用持久状态：

```bash
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py enable
```

启用后，所有新的用户目标默认先调用 Pro 工作流。已有 `task_id` 的追问继续原会话，不会重复新建咨询。

## 启用、暂停和单次绕过

```bash
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py status
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py enable
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py pause
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py resume
python3 ~/.codex/skills/chatgpt-pro-commander/scripts/mode_control.py disable
```

也可以直接告诉 Codex：

- “启用 Pro 指挥工作流”
- “暂停 Pro 指挥工作流”
- “查看 Pro 指挥状态”
- “本次不使用 Pro”

状态文件缺失或损坏时默认视为停用。显式 `$chatgpt-pro-commander` 始终允许单次运行。
“本次不使用 Pro”只绕过当前任务，不改写全局状态。

## 每个任务会发生什么

1. Codex 检查仓库和权限，创建任务 ID。
2. Codex 在项目外生成源码/证据包和哈希。
3. Codex 打开 ChatGPT，选择并验证精确 Pro。
4. Codex 准备 PLAN 正文和附件；你在实际发送前确认一次。
5. Pro 给出实施计划，Codex 校验事实和权限后执行。
6. Codex 运行测试并准备 REVIEW 证据；你在复审发送前再次确认。
7. Pro 给出 PASS、REVISE 或 BLOCKED；最多自动修正一次。
8. Codex 汇总会话链接、哈希、修改、测试和发布状态。

因此，一个正常任务通常需要两次发送：一次 PLAN、一次 REVIEW。发生计划纠错或自动修正时可能增加确认次数。

## 示例

```text
$chatgpt-pro-commander 先让 Pro 设计这个登录重构，Codex 负责实现、测试并让 Pro 复审。
```

```text
本次不使用 Pro，直接解释这个错误信息，不修改文件。
```

```text
暂停 Pro 指挥工作流。
```

## 首次真实验证

开通 Pro 后先用一个无敏感数据的小型测试项目完成端到端验证：

1. 验证登录与模型选择器中的精确 Pro。
2. 上传一个 TASK 文件和两个小型源码文件。
3. 完成 PLAN、一次无害本地修改和 REVIEW。
4. 检查会话恢复、回复 marker、Manifest 和 SHA-256。
5. 确认最终报告没有把模拟检查称为生产验证。

在完成这次验证前，只能说 Skill 通过静态和模拟测试，不能声称真实 ChatGPT Pro 工作流已经验收。

## 限制

- ChatGPT 网页 UI 和模型标签可能变化，模型门禁应以实时语义化控件为准。
- Pro 会员不等于 API 额度；本 Skill 不使用 API 回退。
- 不包含自动点击发送的脚本、扩展或插件。
