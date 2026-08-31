# Gaal

Development repository for **Gaal** and its first application, **Seldon**.

Gaal is the communications-intelligence engine. Seldon is the personal email
briefing product that provides Gaal's first concrete use case and reference
application.

Seldon is a personal productivity assistant created to review overnight and
weekend work email and produce a concise, prioritised morning briefing.

Its purpose is simple:

- Reduce the time spent understanding a busy inbox.
- Identify work requiring immediate attention.
- Separate human communication from automated system traffic.
- Present a concise summary before the working day begins.

The original Seldon prototype operated as a personal tool using a read-only
mailbox, OpenClaw, and a Telegram control interface. That prototype is the
source of the requirements recorded here; it is not an implementation in this
repository.

The repository now contains the first standalone Python slice: static work
schedules, delegated read-only Microsoft 365 mail ingestion, deterministic
classification and briefings, SQLite audit state, and a dry-run CLI.

## Reasoning providers

Model reasoning extracts a strict set of facts and evidence from bounded mail
summaries. Deterministic Gaal policy still assigns the final briefing colour.

- `ollama` is the local-first default in the example configuration. Its endpoint
  is restricted to the local machine.
- `openai` is an explicit metered option and reads its key from
  `OPENAI_API_KEY` (or another configured environment variable). Requests set
  `store` to false.
- `disabled` retains the deterministic rules-only path.

No provider may deliver notifications or mutate the mailbox. Configuration,
token caches, API keys, model files, and SQLite state are machine-local and are
not committed, which keeps the checkout portable to Gaalframe.

The deterministic briefing categories are red (immediate impact or blocking),
black (accumulating material risk), orange (action required), blue (overlooked
or previously unescalated), yellow (waiting or uncertain), and green
(informational or routine). Age alone never turns an item red or black.

Reasoning providers also produce a short factual briefing sentence. Gaal keeps
the bounded source preview and evidence separately; the model cannot alter the
trusted sender or message identity.

Rendered briefings expose only stable short `[olk:…]` references derived from
provider IDs. Raw mailbox message identifiers remain internal.

SQLite tracks hashed conversation keys, first/last observation, counts and the
last deterministic classification without storing mail content. A later action
request in a previously green/yellow thread becomes blue. Delivered scheduled
windows are idempotent; dry runs remain repeatable.

Reasoning may set `ticket_recommended` with a short in-memory reason. The
briefing shows a ticket marker and SQLite retains only the boolean. No ticket
destination is called, and a recommendation never authorises creation.

Telegram delivery is an explicit outbound action. The CLI remains stdout
dry-run by default; only `--deliver-telegram` selects the configured private
chat and permits a send. Tokens come from an environment variable or macOS
Keychain, chat identity is hashed in audit state, and duplicate delivery of a
scheduled window is blocked. Briefings over Telegram's single-message limit
fail before sending rather than risk partial duplicate delivery.
The private chat ID may also be loaded from Keychain and need not appear in
configuration.

Deterministic conflict rules override model ambiguity: routine automated mail
cannot become yellow merely because the model also marked it uncertain or
waiting. Concrete action, exceptions, impact and other stronger evidence still
take precedence.

## Documentation model

- [SYSTEM.md](SYSTEM.md) defines the product vision and enduring principles.
- [docs/scope.md](docs/scope.md) defines the Seldon product boundary.
- [docs/history.md](docs/history.md) records project history.
- [docs/reference/seldon/](docs/reference/seldon/) records observed prototype
  behaviour and migration evidence.
- [docs/architecture.md](docs/architecture.md) describes Gaal's target
  architecture, not current repository functionality.
- [docs/reference/seldon/migration-notes.md](docs/reference/seldon/migration-notes.md)
  is the current implementation-requirements inventory.
