# Scope

## Document status

This document defines the Seldon product boundary. Its listed capabilities are
observed in the external OpenClaw prototype unless explicitly marked as
implemented in Gaal.

There is currently no standalone Gaal implementation in this repository.

## Purpose

Seldon reviews work email received during periods away from work and produces a
prioritised briefing.

## Observed prototype capabilities

- Retrieve email from a configurable time window.
- Read mailbox contents using read-only access.
- Distinguish automated traffic from human correspondence.
- Identify likely actions and priorities.
- Produce a structured morning briefing.
- Accept configuration changes through Telegram.

## Seldon product policy

Seldon does not:

- Send email.
- Reply to email.
- Delete or modify email.
- Move messages between folders.
- Create tickets automatically.
- Contact customers.
- Make decisions on behalf of the user.

Seldon assists decision making.

The user remains responsible for every action.

These restrictions are intentionally narrower than Gaal's potential engine
capabilities. A future Gaal application may support explicitly approved
external actions, but Seldon remains read-only unless this product policy is
deliberately revised.
