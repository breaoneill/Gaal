# Gaal

Gaal is a standalone morning-briefing system for work communications. It reads
Microsoft 365 email received while its user is away from work, identifies what
needs attention, and delivers a concise, prioritised briefing before the next
working day begins.

Gaal is the direct successor to Seldon. Seldon proved the workflow inside
OpenClaw; Gaal preserves the useful behaviour as an independent Python
application with explicit configuration, tests, audit state and deployment.
OpenClaw is not a runtime dependency and Seldon is not a separate application
inside this repository.

## What Gaal does

A scheduled run:

1. Calculates the unattended window from the user's working pattern.
2. Reads that window from Microsoft 365 using delegated `Mail.Read` access.
3. Normalises bounded message data without modifying the mailbox.
4. Uses a configured reasoning provider to extract facts and concise summaries.
5. Applies deterministic policy to assign briefing categories.
6. Records content-free operational state in SQLite.
7. Prints a dry-run briefing or explicitly delivers it to a private Telegram
   chat.

Gaal currently runs once each working morning. It is not an inbox replacement,
continuous monitor, chatbot or autonomous agent.

## Briefing categories

The final category is assigned by Gaal's rules, not by the model:

- red — immediate service impact or a blocking issue;
- black — material risk accumulating without adequate resolution;
- orange — a concrete action is required;
- blue — an issue was previously overlooked or insufficiently escalated;
- yellow — waiting, uncertain or requiring confirmation;
- green — informational or routine.

Age alone never makes an item red or black. Deterministic conflict rules also
prevent routine automated mail from being promoted merely because a model
expressed uncertainty.

## Trust boundary

Gaal has read-only mailbox access. It does not send, reply to, move or delete
email. It does not create tickets, contact customers or make commitments.

A reasoning provider may extract facts, evidence and a short briefing sentence,
but it cannot change trusted sender or message identity, choose the final policy
category, deliver notifications or mutate an external system. A model may
recommend that a ticket should exist; that recommendation is not permission to
create one.

Telegram is the only implemented delivery destination. Delivery requires the
explicit `--deliver-telegram` flag, and a scheduled window cannot be delivered
twice. Oversized briefings fail before sending rather than risk a partial or
duplicated result.

## Privacy and state

Mailbox content is processed for the current run and is not stored in SQLite.
The audit database retains operational facts, hashed conversation and
destination identifiers, observation counts, classifications and delivery
status. Briefings expose short opaque `[olk:…]` references rather than raw
provider identifiers.

Configuration, token caches, API keys, model files and SQLite state are local
to the machine running Gaal and must not be committed. OpenAI requests set
`store` to false.

## Reasoning providers

Gaal has one provider boundary with three configurations:

- `openai` — the proven production path; explicit, metered and configured by
  environment variable;
- `ollama` — an optional workstation path for suitable local hardware;
- `disabled` — a model-free rules-only fallback.

OpenAI has been exercised end to end with a real mailbox. Rules-only operation
also completes end to end but currently lacks enough semantic extraction to
produce a useful briefing on its own. Ollama is not intended for the small
production host and remains experimental; invalid structured output is rejected
without delivery.

## Current implementation

Implemented:

- static working days, hours and timezone;
- delegated Microsoft 365 device-code authentication;
- bounded, read-only Inbox ingestion;
- deterministic six-category classification;
- provider-assisted fact extraction and summarisation;
- concise daily and reference briefings;
- SQLite audit, thread continuity and delivery idempotency;
- explicit Telegram delivery;
- ticket-recommendation plumbing without ticket creation;
- CLI dry runs and run inspection;
- Linux systemd scheduling;
- CI on Python 3.11 and 3.13;
- explicit, tested and rollback-capable server releases.

Not implemented:

- a web interface;
- multi-user or hosted operation;
- Teams or calendar ingestion;
- email or ticket creation;
- continuous monitoring;
- automatic production deployment.

Source and destination interfaces exist to keep these boundaries clean. They
are not a plugin system and do not imply that speculative integrations are
already supported.

## Configuration and operation

Start with `config/gaal.example.toml`. The CLI exposes three operations:

```text
gaal auth-microsoft365
gaal daily
gaal last-run
```

`gaal daily` is a dry run unless `--deliver-telegram` is supplied. See the
command help for required paths and timestamps.

The files in `deploy/systemd` run Gaal under a dedicated Linux account at 07:30
Europe/London, Monday to Thursday. Configuration lives in `/etc/gaal`, secrets
are supplied by a restricted environment file, and audit state lives in
`/var/lib/gaal`.

GitHub Actions runs tests, compilation and dependency checks on every push to
`main` and every pull request. Production deployment remains deliberate:

```text
update-gaal <full-commit-sha>
```

The updater accepts a commit from `origin/main`, repeats verification on the
host and restores the previous revision if deployment fails. Supplying an
earlier approved SHA performs a rollback.

## Documentation

- [SYSTEM.md](SYSTEM.md) defines Gaal's durable behavioural contract.
- [docs/scope.md](docs/scope.md) records the original Seldon product boundary.
- [docs/history.md](docs/history.md) records the route from Seldon to Gaal.
- [docs/reference/seldon/](docs/reference/seldon/) preserves prototype evidence
  and migration notes.
- [docs/architecture.md](docs/architecture.md) describes longer-term extension
  seams and should not be read as a list of implemented features.
