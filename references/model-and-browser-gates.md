# Model and browser gates

Use these gates for every ChatGPT Web exchange. They prove that the message targets exact Pro mode in Chat, not a subscription label, adjacent model, or another product surface.

## Select the control surface

1. Use the in-app browser, Chrome, or other supported surface explicitly named by the user. Treat one named surface as exclusive unless the user authorizes fallback.
2. If none is named, follow the installed browser skill's default selection rule.
3. Read the complete installed skill for the chosen browser before operating it.
4. Use that surface's semantic DOM/accessibility interface. Do not switch to standalone Playwright, page scripts, DevTools injection, coordinate automation, or an unauthorized controller.
5. Never inspect cookies, local storage, passwords, profiles, history, or session databases.

## Login gate

Verify from the current visible page that it is on `https://chatgpt.com/`, has an interactive composer, and does not require login, account selection, a verification code, passkey, or two-factor authentication. Confirm the expected account without recording its email or identity. Pause for the user if authentication is required.

## Chat and Pro gate

Before entering task content and again immediately before each send:

1. Confirm this is a Chat conversation, not Work, a task-progress page, or another product surface.
2. Locate the single active model/capability control. Evidence must come from its visible label, accessible name/value, or selected menu item.
3. If the active label lacks a standalone `Pro` token, choose a visible, enabled, semantically unambiguous Pro option.
4. Re-read the active control and prove Pro remains selected. A visible option without selected state is insufficient.
5. Record the full model label, `dom|ax` inspection method, `already_pro|direct_option` selection path, and timestamp.

Never accept sidebar text, conversation titles, prompt/response text, subscription pages, `High`/`Thinking` effort labels, a version number without Pro, or uncertain screenshot/coordinate inference as evidence. Do not hard-code a GPT-5.x version or private test ID as the sole condition.

## Gate record

```json
{
  "schema_version": 1,
  "surface": "iab|chrome",
  "chat_selected": true,
  "work_active": false,
  "active_model_label": "<full visible label>",
  "pro_control_selected": true,
  "evidence_scope": "active_model_control",
  "inspection_method": "dom|ax",
  "selection_path": "already_pro|direct_option",
  "observed_at": "<ISO-8601 with timezone>"
}
```

Save only this minimal record in the task evidence directory and validate it with `scripts/validate_browser_gate.py`. Do not save raw DOM/accessibility trees or account data.
