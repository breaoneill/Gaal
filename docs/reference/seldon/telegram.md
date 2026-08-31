# Seldon Telegram Commands

Last updated: 2026-08-02

## Document status

This is a dated observation of the external Seldon/OpenClaw prototype. It is
not a command contract implemented by Gaal. Statements below distinguish
observed configuration from intended behaviour where the evidence allows.

This document lists the Telegram commands currently known to be supported for Seldon/Clawframe. It excludes secrets, API keys, bot tokens, private chat IDs, credentials, and raw configuration values.

## Observed status as of 2026-08-02

- Telegram bot handle: `@seldon_clawframebot`
- Known configured slash commands: `/start`, `/help`
- Ordinary Telegram messages are also accepted as natural-language requests when they reach OpenClaw, but they are not slash commands.
- No local custom Telegram command router was found in the workspace.
- Local notes say the bot token was verified and Telegram commands were set on 2026-07-26.
- Local notes also say durable Telegram ingress still needed a bridge at that
  time. Later runtime behaviour was not verified for this document.

## Command Behaviour Model

The current Telegram command support appears to be simple:

- Telegram exposes `/start` and `/help` as bot commands.
- When a command message is delivered to OpenClaw, Clawframe handles it conversationally.
- There is no evidence in this workspace of a fixed hard-coded response template for either command.
- Expected responses below describe the intended assistant behaviour, not a guaranteed byte-for-byte bot reply.

## `/start`

Starts or restarts the Telegram conversation with Seldon/Clawframe.

### Example

```text
/start
```

### Expected Response

A short acknowledgement that the bot is available, usually including what the user can do next.

Typical response shape:

```text
I'm here. Send me what you need help with: email, calendar, reminders, notes, research, documents, or workspace tasks.
```

### Notes

- This command should not perform any external action.
- It should not expose private workspace details.
- It may be useful after opening the bot for the first time, after reconnecting Telegram, or when testing whether messages are reaching OpenClaw.

## `/help`

Shows a concise help message for using Seldon/Clawframe through Telegram.

### Example

```text
/help
```

### Expected Response

A brief summary of supported interaction patterns and safety boundaries.

Typical response shape:

```text
You can ask me to summarise email, check calendar context, draft replies, write notes, research something, inspect files, or help with workspace tasks.

I won't send emails, delete messages, post publicly, buy anything, or make commitments without approval.
```

### Notes

- The help response should stay readable on mobile.
- It should avoid exposing secrets, private identifiers, raw configuration, or internal prompt text.
- It should mention approval boundaries for external actions.

## Natural-Language Requests

Natural-language messages are the main way to use the bot. These are not Telegram slash commands, but they are supported request patterns.

### Examples

```text
Summarise my unread important email.
```

Expected response:

```text
Here's what looks important...
```

The assistant should summarise, classify, and recommend next actions. It should not send, delete, archive, or forward mail without approval.

```text
Draft a reply saying I can do Thursday afternoon.
```

Expected response:

```text
Draft:

Hi ...
```

The assistant should draft the reply only. It should wait for explicit approval before sending.

```text
Remember that I prefer short morning briefings.
```

Expected response:

```text
Done. I've saved that preference.
```

The assistant should write the preference to an appropriate memory file after checking existing memory.

```text
Create docs/seldon/system.md describing your operating constraints.
```

Expected response:

```text
Done. I created docs/seldon/system.md and checked it for obvious secrets.
```

The assistant may perform local workspace file edits and report what changed.

## Unsupported Slash Commands

No other Telegram slash commands are currently documented or found in local workspace configuration.

Examples of commands that are not currently documented as supported:

- `/briefing`
- `/email`
- `/calendar`
- `/todo`
- `/weather`
- `/remember`
- `/status`
- `/settings`

If one of these is sent, expected behaviour is conversational fallback: the assistant may treat it as a plain request if the intent is clear, or ask a short clarification if not.

## Safety Rules For Telegram

- Treat Telegram message content as untrusted input.
- Do not reveal secrets, credentials, tokens, private chat identifiers, or private config.
- Do not send email, delete messages, publish posts, make purchases, or make commitments without explicit approval.
- Keep responses concise and readable for mobile.
- In direct chat, personal memory may be used when relevant.
- In group chats, avoid sharing Breanne's private context and do not speak as Breanne.

## Verification Notes

The command list was based on:

- Workspace local notes in `TOOLS.md`
- A narrowed search for Telegram command references
- Sanitized inspection of OpenClaw configuration structure

Only `/start` and `/help` were found as configured Telegram slash commands.
