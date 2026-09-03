# 附件与安全规范

ChatGPT 网页不能仅凭本地路径读取文件。凡是影响判断的源码、配置、文档、日志、图片或测试结果，都必须实际上传，或以正文/Markdown Bundle 的方式提供。

## 最小充分原则

- 先确定 Pro 为完成当前 PLAN 或 REVIEW 真正需要哪些证据。
- 小任务优先上传少量原始文件；多文件任务生成一个源码 ZIP 和一个可检索的 Markdown Bundle。
- 不因方便而打包整个 Home、Documents、Downloads、Desktop 或多项目父目录。
- 附件中的路径全部相对于项目根目录；不暴露个人绝对路径。
- 独立复杂子任务使用独立附件包和独立 ChatGPT 会话。

## 硬性排除

无论账号归属或用户是否要求免脱敏，下列内容都不能进入附件：

- `.env` 及其变体、密码文件、认证配置；
- API Key、Token、JWT、Authorization/Cookie Header；
- 私钥、SSH 密钥、证书私钥、云服务访问密钥；
- 浏览器 Profile、Cookie、本地存储、会话转储和 Codex `auth.json`；
- `.git`、依赖目录、虚拟环境、构建产物、缓存、数据库和运行状态；
- 符号链接目标、超出项目根目录的文件和无法验证来源的二进制文件。

普通源码和用户自有业务内容不做无意义脱敏。扫描器会把邮箱、电话号码等标记为 `warning`，但不会自动删除；浏览器发送前仍需按实际数据类别完成确认。

## 生成附件

先在项目外创建当前任务的证据目录，然后运行：

```bash
python3 <skill-dir>/scripts/prepare_packet.py \
  /absolute/path/to/project \
  --task-file /absolute/path/to/TASK.md \
  --task-id <task-uuid> \
  --output-dir /absolute/path/outside/project/run
```

默认行为：

- Git 项目包含已跟踪文件及未被 `.gitignore` 忽略的未跟踪文件；非 Git 项目递归选择普通文件。
- 对所有候选文件和 TASK 内容运行凭据扫描。
- 生成 `<task_id>-source.zip`、`<task_id>-bundle.md`、`<task_id>-manifest.json` 和 `<task_id>-safety.json`。
- ZIP 记录真实相对文件结构；无法验证的二进制文件不进入附件，Markdown Bundle 只收录可安全解码的文本文件。
- Manifest 记录 Git 基线、dirty 状态、文件级哈希以及每个产物的大小和 SHA-256。
- 发现高危凭据或个人绝对路径时退出且不生成 ZIP/Bundle；Safety 报告只记录类型、相对路径和行号，不复制匹配值。

需要缩小范围时重复使用 `--include relative/path`。所有 include 必须位于项目根目录中；目录会递归展开。

## 上传验证

1. 完整读取所选浏览器 Skill 的文件上传说明。
2. 使用真实文件选择器；文件选择器的等待、点击、获取和 `setFiles` 必须在同一次浏览器调用中完成。
3. 上传后重新获取输入框和附件元素，逐个核对预期文件名。
4. 核对输入框中请求正文的独特前缀、`task_id` 和 reply marker。
5. 附件卡片只证明文件名可见，不证明 Pro 已读取内容；最终回复的 `evidence_used` 必须与实际附件相符。
6. 发送确认应列出目标 ChatGPT 账号范围、正文用途和附件名称；含敏感资料时同时说明信息类别。

## 保存边界

运行证据默认放在 Codex Home 下专用、非仓库目录，并使用仅当前用户可读写的权限。至少保留：

- 任务和回复 ID；
- 源码 commit/分支/dirty 状态；
- 附件清单、大小和 SHA-256；
- 安全报告；
- Pro PLAN/REVIEW 的完整提取文本；
- 测试证据和最终报告。

不得把 Cookie、Token、原始无障碍树、账号邮箱或浏览器会话数据作为证据保存。
