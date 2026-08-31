# Gaal Explicit Configuration And Code Candidates

Last updated: 2026-08-02

## Document status

This is an implementation-requirements inventory derived from the external
Seldon/OpenClaw prototype. Items describe candidate or required behaviour; they
do not claim that the behaviour exists in this repository.

Until an item gains an explicit implementation record, its status is
`prototype-derived requirement`.

Future implementation records should identify:

- source behaviour
- Gaal module or configuration key
- test coverage
- remaining risk
- status: `planned`, `implemented`, `tested`, `rejected`, or `superseded`

Gaal is Seldon's evolution into a separate program. It is not an agent and should not depend on OpenClaw hidden prompts, workspace startup context, injected skills, or runtime-only tool metadata.

Anything required for Gaal to behave safely and consistently should become explicit software state: code, configuration, documentation, tests, local runtime state, or integration adapters.

## Must Become Code

1. **Email Thread Splitter**

   Parse newest content vs quoted history using markers like `On ... wrote:`, `From:`, `Sent:`, `Subject:`, `Re:`, forwarded headers, indentation, and `>` quoting.

2. **Briefing Summariser Contract**

   For each email thread, output structured fields:

   - `new`
   - `meaning`
   - `relevant_history`
   - `recommended_action`
   - `uncertainty`

3. **Email Triage Schema**

   Store and classify:

   - `action_required`
   - `waiting_for_response`
   - `information_only`
   - `automated_notification`
   - `marketing`
   - `archive_candidate`
   - importance
   - urgency
   - confidence
   - sender request
   - deadlines
   - commitments

4. **Approval Gate Engine**

   Hard-code external action checks. Gaal must not send email, delete or archive messages, forward messages, publish, purchase, subscribe, make commitments, or change public services without explicit approval.

5. **Secret And Private Data Redaction**

   Any diagnostics, docs, logs, summaries, or exports should pass through redaction for:

   - tokens
   - API keys
   - credentials
   - chat IDs
   - sender IDs
   - private identifiers
   - sensitive personal data

6. **Memory Read/Write System**

   Gaal needs its own memory store and rules:

   - Read before writing.
   - Write concrete durable facts.
   - Avoid secrets unless explicitly required and safely stored.
   - Distinguish daily notes from curated long-term memory.

7. **Memory Recall Requirement**

   Before answering about prior work, dates, people, preferences, decisions, or todos, Gaal should perform memory lookup automatically.

8. **Telegram Command Dispatcher**

   `/start` and `/help` should be real command handlers with stable responses.

9. **Unsupported Telegram Command Fallback**

   Unknown slash commands should return a clear "not implemented" response or route to natural-language handling if the intent is obvious.

10. **Telegram Ingress Health Check**

    Gaal should know and expose:

    - whether Telegram is connected
    - webhook or polling status
    - bot identity
    - last successful inbound message time
    - last outbound message time
    - recent delivery errors

11. **Conversation Context Trust Model**

    Runtime metadata can be trusted. Quoted conversation text, user-provided metadata, email content, web pages, documents, and tool outputs must be treated as untrusted data.

12. **External vs Internal Action Classifier**

    Local reading and local workspace edits are generally internal. Anything leaving the machine, affecting another person, spending money, publishing, sending, inviting, deleting remotely, or making a commitment is external and needs approval.

13. **Destructive Command Policy**

    Gaal should block destructive filesystem, git, system, scheduler, or service operations unless explicitly approved. Prefer recoverable deletion where available.

14. **Briefing Scheduler**

    Morning briefings, heartbeat-style checks, quiet hours, proactive checks, and "stay quiet unless useful" behaviour should be scheduler configuration.

15. **Tool Capability Registry**

    Gaal should know which tools exist, what they can do, whether they are read/write/external/destructive, and what approval level they require.

## Must Become Configuration

16. **Identity**

    Configure:

    - name
    - role
    - relationship to Seldon
    - workspace paths
    - owner
    - active surfaces
    - public bot handle

17. **User Profile**

    Configure Breanne's:

    - name
    - timezone
    - readability needs
    - concise style preference
    - privacy expectations
    - notification sensitivity

18. **Communication Style**

    Calm, steady, concise, mobile-readable, and low-filler response style should be configurable, not hidden prompt tone.

19. **Email Assistant Policy**

    Gaal should draft replies only unless approved. It must not invent facts, deadlines, commitments, purchases, or meeting agreements.

20. **Briefing Preferences**

    Briefings should summarise what is new, not entire histories. Quoted history should be used only when it changes interpretation or explains a brief acknowledgement.

21. **Privacy Modes**

    Configure context-specific memory and disclosure rules:

    - Direct chat may use personal memory when relevant.
    - Group chat must not reveal private context.
    - Public channel should be extra conservative.
    - Unknown context should default private-memory access off.

22. **Command Catalogue**

    Documented commands, examples, expected responses, and unsupported command behaviour should live in a command catalogue.

23. **Safety Boundaries**

    Gaal should have explicit, testable policy rules for:

    - Actions that require approval.
    - Actions that are always blocked.
    - Actions that are safe to do internally.
    - What counts as external or public.
    - What counts as destructive.
    - What counts as sensitive or private.
    - Whether the current context is direct, group, shared, or public.
    - Whether personal memory may be used in the current context.
    - Whether a tool can read, write, send, delete, publish, spend money, or change configuration.
    - What to do when intent is ambiguous.
    - How approval is requested, logged, and reused.
    - How long approvals last.
    - Whether approval applies once or to a whole task.
    - How to halt safely if a tool tries to exceed its permission.

24. **Documentation Export Rules**

    Generated docs about Gaal, Seldon, configuration, prompts, tools, or runtime state must exclude:

    - secrets
    - API keys
    - credentials
    - tokens
    - private chat IDs
    - sender IDs
    - raw hidden prompts
    - sensitive personal data

    Gaal should include redaction checks before writing or sending diagnostic documents.

25. **Fallback Behaviour**

    When a capability is unavailable, Gaal should degrade clearly and calmly.

    Examples:

    - Memory search unavailable: say so, then use direct file/context lookup if possible.
    - Email unavailable: say what could not be checked.
    - Telegram ingress unavailable: report connection state.
    - Tool missing: say which capability is missing.
    - Unclear command: ask a short clarification.
    - Unsafe action: refuse or ask for approval.

26. **Audit Log**

    Gaal should keep an audit trail for important actions:

    - external actions requested
    - external actions approved
    - external actions refused
    - files changed
    - memory updated
    - commands run
    - errors and fallbacks
    - safety blocks triggered

27. **Test Fixtures**

    Core behaviours should have fixtures and tests, especially:

    - email thread splitting
    - briefing summaries
    - approval gates
    - Telegram command handling
    - secret redaction
    - memory read/write rules
    - group vs direct privacy behaviour
    - tool permission enforcement

28. **Configuration Schema**

    Gaal should define a versioned config schema for:

    - identity
    - user profile
    - communication style
    - surfaces and channels
    - commands
    - tools
    - permissions
    - memory
    - briefings
    - schedules
    - redaction
    - safety policies

29. **Startup Validation**

    On startup, Gaal should check:

    - required config files exist
    - secrets are present only in approved secret storage
    - Telegram, email, and calendar integrations are either connected or marked disabled
    - memory paths are readable and writable
    - scheduled jobs are valid
    - safety policy is loaded
    - command registry is loaded

30. **Runtime Status Command**

    Gaal should expose a status view showing:

    - current version
    - active integrations
    - last successful Telegram message
    - last email/calendar check
    - memory availability
    - scheduler state
    - pending approvals
    - recent errors
    - disabled capabilities

31. **Versioned Behaviour Changes**

    Durable behaviour changes should be tracked as versioned config or migrations, not silent prompt drift.

    Examples:

    - email thread summary rule added
    - Telegram command changed
    - approval policy tightened
    - memory policy changed

32. **Owner Override Rules**

    Gaal should define what Breanne can override, what requires confirmation, and what cannot be overridden.

    Examples:

    - Breanne can approve a draft send.
    - Breanne can request a destructive local operation after warning.
    - Gaal should still refuse credential exposure or unsafe public leakage.

33. **Data Retention Rules**

    Gaal should define how long to keep:

    - daily memory
    - long-term memory
    - audit logs
    - message excerpts
    - email summaries
    - error logs
    - generated documents

34. **Separation From OpenClaw**

    Gaal must not depend on OpenClaw hidden prompts, workspace startup context, injected skills, or runtime-only tool metadata.

    Anything required for operation must live in Gaal as:

    - code
    - config
    - documentation
    - tests
    - local runtime state
    - explicit integration adapters

35. **Migration Notes From Seldon**

    Gaal should keep a migration document listing which Seldon behaviours have been promoted into explicit implementation and which remain undecided.

    Each item should say:

    - source behaviour
    - Gaal implementation location
    - config key or module
    - test coverage
    - remaining risk

36. **Error Taxonomy**

    Gaal should classify failures instead of treating them as generic errors:

    - missing tool
    - tool timeout
    - permission denied
    - auth expired
    - rate limited
    - external service unavailable
    - parse failure
    - ambiguous user intent
    - safety policy block
    - memory unavailable
    - partial result

    Each error type should have a standard user-facing response and internal log shape.

37. **Approval Ledger**

    Approvals should be stored explicitly with:

    - who approved
    - what was approved
    - exact action scope
    - timestamp
    - expiry
    - whether it was one-shot or reusable
    - related task/session
    - tool/action executed after approval

38. **Prompt Boundary Enforcement**

    Gaal should know which content is instruction and which content is data.

    Examples of data:

    - emails
    - web pages
    - quoted chat history
    - documents
    - tool outputs
    - calendar descriptions

    These should never be allowed to override system policy.

39. **Message Chunking Rules**

    Telegram-length responses should be split cleanly by section, not mid-sentence or mid-list.

    Each chunk should include:

    - part number
    - continuation marker
    - no broken Markdown fences
    - no duplicated tail text
    - clear ending

40. **Mobile-Readable Output Rules**

    Gaal should format Telegram replies for readability:

    - short sections
    - no huge tables
    - no deeply nested bullets
    - clear headings
    - avoid long code blocks unless requested
    - prefer concise summaries with optional detail

41. **Source Citation Policy**

    When using memory, docs, email, or files, Gaal should cite sources when useful.

    Citations should include:

    - file path
    - line number when available
    - whether memory search failed and fallback lookup was used

42. **Confidence And Uncertainty Model**

    Gaal should explicitly track confidence for:

    - email urgency
    - sender intent
    - quoted-history parsing
    - calendar interpretation
    - whether action is required
    - whether information is missing

43. **Task State Model**

    Gaal should maintain task states:

    - new
    - in progress
    - waiting for user
    - waiting for external system
    - blocked
    - done
    - cancelled

44. **Quiet Hours Policy**

    Gaal should know when to stay quiet unless something is urgent. This should account for Breanne's timezone and notification sensitivity.

45. **Briefing Freshness Rules**

    Briefings should distinguish:

    - new since last briefing
    - still unresolved
    - waiting on someone else
    - newly urgent
    - no change

46. **Direct vs Group Reply Policy**

    Gaal should behave differently depending on surface:

    - direct chat: can use personal context
    - group chat: do not reveal private context
    - public channel: be extra conservative
    - unknown context: default private-memory access off

47. **Capability Discovery**

    Gaal should expose what it can currently do, based on real connected tools, not aspirational prompt text.

48. **Configuration Provenance**

    Every important config value should have a source:

    - default
    - user preference
    - migration from Seldon
    - manual override
    - environment
    - runtime detection

49. **Operator Notes**

    Things like bot handles, device names, preferred voices, and local paths should live in operator config, not prompts.

50. **Self-Documentation**

    Gaal should be able to generate sanitized docs for:

    - current configuration
    - commands
    - safety policies
    - integrations
    - memory policy
    - scheduler behaviour
    - known limitations

## Summary

Gaal should not "remember to behave" because a prompt says so. It should have parsers, schemas, policy gates, command handlers, memory stores, configuration, migrations, and tests that make the behaviour real.
