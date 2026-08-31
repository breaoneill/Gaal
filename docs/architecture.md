# Architecture

## Document status

This document separates the observed Seldon prototype from Gaal's target
architecture. It does not describe code currently implemented in this
repository.

## Observed Seldon prototype

The OpenClaw-hosted prototype demonstrates five logical stages.

```
Mailbox
    │
    ▼
Retrieve messages
    │
    ▼
Classify
    │
    ▼
Prioritise
    │
    ▼
Generate briefing
    │
    ▼
Telegram
```

### Classification

Where practical, deterministic rules should be used before AI.

Examples include:

- sender
- mailing list
- monitoring systems
- backup reports
- GitHub notifications
- known automated mail

AI should only be used where judgement is required.

### Mailbox access

Mailbox access is read-only.

Seldon does not alter mailbox contents.

### Configuration

Runtime behaviour may be adjusted through Telegram commands.

Examples include:

- briefing period
- priority rules
- ignored senders
- reporting options

### Runtime

The current prototype is hosted using OpenClaw.

OpenClaw is the current execution environment and control interface.

It is not considered a permanent architectural dependency.

## Target Gaal architecture

Gaal should promote the prototype's useful behaviour into explicit,
independently testable layers.

```
Source adapters
      │
      ▼
Normalised messages and threads
      │
      ▼
Deterministic rules
      │
      ▼
Provider-independent model services
      │
      ▼
Knowledge and task state
      │
      ▼
Briefings, search and recommendations
```

Source-specific behaviour belongs in adapters. Business rules, safety policy,
and output contracts belong in Gaal. Seldon supplies email and Telegram
adapters plus a read-only product policy.

Implementation requirements and migration status are tracked separately in
[reference/seldon/migration-notes.md](reference/seldon/migration-notes.md).
