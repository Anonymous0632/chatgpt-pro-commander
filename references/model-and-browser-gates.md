# 模型与浏览器门禁

本文件用于每次 ChatGPT 网页路线。目标是证明消息发送时使用的是 Chat/聊天界面中的精确 `Pro` 模式，而不是套餐标签、相邻模型或其他产品界面。

## 选择控制面

1. 如果当前用户请求明确指定内置浏览器、Chrome 或其他受支持控制面，严格使用该控制面；一个明确名称就是排他选择，除非用户同时授权回退链。
2. 如果用户没有指定，按已安装浏览器 Skill 的规则选择运行时默认控制面。
3. 操作内置浏览器前完整读取已安装的 `browser:control-in-app-browser` Skill；操作 Chrome 前完整读取 `chrome:control-chrome` Skill。
4. 使用控制面自身要求的浏览器运行时和语义化 DOM/无障碍接口。不要改用独立 Playwright、页面脚本、浏览器 DevTools 注入或未授权控制器。
5. 不检查 Cookie、本地存储、密码、Profile、浏览器历史或会话数据库。

## 登录门禁

从新的或明确恢复的 ChatGPT 会话读取当前可见状态：

- 页面来自 `https://chatgpt.com/`；
- 存在可交互的消息输入区；
- 页面没有显示需要登录、选择账号、验证码、Passkey 或两步验证；
- 当前会话属于预期账号，但不记录账号邮箱或其他标识。

需要用户身份操作时停止并请用户在同一控制面完成。不要读取凭据，也不要切换到另一个账号规避验证。

## Chat 与 Pro 门禁

在输入任何任务内容前，以及每次发送前，分别进行一次新的语义化检查：

1. 确认当前是 Chat/聊天会话，而不是 Work/工作、任务进度页或其他产品界面。
2. 定位唯一的活动模型或能力控件。证据必须来自控件的可见标签、accessible name/value 或已选中菜单项。
3. 如果活动标签尚不包含独立的 `Pro` 词元，打开模型控件并选择可见、启用且语义明确的 Pro 选项。
4. 重新读取活动控件，确认 Pro 仍然选中；只看到列表选项而没有选中状态不算成功。
5. 记录完整活动模型标签、检查方式 `dom|ax`、选择路径 `already_pro|direct_option` 和时间。

以下内容一律不能作为 Pro 证据：

- 侧边栏、历史对话标题、提示词或回答正文中的 `Pro`；
- 账户套餐、付款页面或个人资料中的 Pro；
- `High`、`Extra High`、`Thinking`、`极高`、`超高` 等推理强度；
- 仅有 GPT 版本号但没有 Pro 的模型标签；
- 屏幕坐标或截图中的模糊视觉推断。

模型界面未来可能变化，因此不要把 GPT-5.x 版本号或私有 `data-testid` 写成唯一条件。只有语义化活动控件中的 Pro 选择才是持续有效的门禁。

## 发送确认

发送消息必须遵守当前浏览器控制面的动作时确认要求。脚本可以准备正文、校验附件和防止重复提交，但不能通过扩展、CDP、坐标点击或页面注入代替用户确认。

正常任务需要两次发送确认：PLAN 一次，REVIEW 一次。纠错或一次自动修正可能产生额外的发送，但每次发送都必须重新校验模型门禁并遵守确认要求。
## 门禁记录格式

将下面结构保存到当前任务证据目录，不保存原始 DOM、无障碍树或账号信息：

```json
{
  "schema_version": 1,
  "surface": "iab|chrome",
  "chat_selected": true,
  "work_active": false,
  "active_model_label": "<完整可见标签>",
  "pro_control_selected": true,
  "evidence_scope": "active_model_control",
  "inspection_method": "dom|ax",
  "selection_path": "already_pro|direct_option",
  "observed_at": "<ISO-8601>"
}
```

使用 `scripts/validate_browser_gate.py` 验证该记录。任何字段缺失或不一致都不得进入发送阶段。
