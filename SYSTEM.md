# Gaal system definition

Version: 0.2

## Identity

Gaal is a standalone morning-briefing system for work communications.

It reviews information received while its user is away from work and presents
what deserves attention at the start of the next working period. Its first and
current source is Microsoft 365 email; its current delivery destination is a
private Telegram chat.

Gaal is the continuation of Seldon as independent software. Seldon established
the behaviour and operating need; Gaal owns that behaviour now. The distinction
is historical, not an engine/product split.

## Operational purpose

Gaal exists to prevent important work from disappearing into communication
volume.

It must help the user answer:

- What is already affecting service or blocking work?
- What risk is quietly accumulating?
- What requires action from me?
- What may have been overlooked?
- What am I waiting for or uncertain about?
- What can safely remain informational?

The result is a bounded, explainable briefing—not a general summary of every
message and not a substitute for reading the underlying correspondence.

## System contract

For each scheduled run, Gaal must:

1. Derive the input window from explicit work-schedule configuration.
2. Read only communications visible to the authorised user.
3. Bound and normalise source data before model processing.
4. Preserve trusted source identity independently of model output.
5. Extract facts and evidence separately from policy classification.
6. Apply deterministic precedence rules to the final category.
7. Produce concise output with stable opaque references.
8. Record enough content-free state to explain the run and prevent duplicate
   delivery.
9. Fail closed when authentication, reasoning, validation or delivery is
   incomplete.

A dry run must be repeatable. A live scheduled window must not be delivered
twice.

## Categories and precedence

Gaal uses six operational categories:

1. **Red:** immediate impact or blocking work.
2. **Black:** material risk accumulating without adequate resolution.
3. **Orange:** concrete action is required.
4. **Blue:** a thread was previously overlooked or insufficiently escalated.
5. **Yellow:** waiting, uncertain or requiring confirmation.
6. **Green:** informational or routine.

These colours express operational meaning, not a generic severity score. Age
alone cannot make an item red or black. Model uncertainty cannot promote
routine automated traffic when stronger deterministic facts say otherwise.

## Authority

Gaal observes, classifies, explains, summarises and recommends. The user retains
authority over every external action.

Gaal must not:

- send, reply to, move or delete email;
- mark mailbox items read or otherwise alter mailbox state;
- create tickets merely because one was recommended;
- contact a customer or colleague;
- make a promise, commitment or operational decision;
- conceal a failed or partial run;
- broaden its own permissions.

Adding an action destination in future requires an explicit product decision,
an approval boundary and its own audit behaviour. An interface or placeholder
does not confer that authority.

Telegram briefing delivery is a narrow exception: it is an explicitly selected
output to a configured private destination, not general permission to message
people.

## Reasoning boundary

Models assist with semantic extraction and concise language. They are neither
the source of truth nor the policy engine.

A reasoning provider may return:

- action and waiting signals;
- deadlines and service-impact facts;
- uncertainty, exceptions and accumulating-risk signals;
- evidence tied to bounded source text;
- a short factual briefing summary;
- a ticket recommendation and reason.

Gaal validates that output against a strict schema. A provider cannot add or
remove messages, change message identity, choose a destination or cause an
external action. Invalid or incomplete output fails the reasoning stage.

Provider selection is configuration, but provider capability is not assumed to
be equal. OpenAI is the currently proven operational provider. Local and
disabled modes must remain safe when less capable, even if their briefing
quality is lower.

## Data handling

All communication content is private.

Gaal must minimise what it retrieves, bound what it sends to a model, and
not persist message bodies or generated briefing content in its SQLite audit
store. Persistent state may contain:

- run times and input windows;
- hashed conversation and destination identifiers;
- first and last observation times;
- observation counts;
- deterministic classifications;
- ticket-recommendation booleans;
- delivery and failure status.

Credentials, token caches, configuration and database files belong to the host,
not the repository. Logs and errors must not expose tokens, raw model responses
or mailbox content.

## Failure behaviour

Silence is not success.

Gaal must distinguish authentication, source, reasoning, policy, audit and
delivery failures. It must not send a partial Telegram briefing, and it must not
record a failed delivery as successful. A release failure must preserve or
restore the last verified revision.

Operational monitoring should make a missed scheduled briefing visible through
a route independent of the briefing itself.

## Deployment model

Gaal is personal, standalone software. It may run on a user's computer or on a
private always-on host. The current production shape is one user, one mailbox,
one schedule, one state database and one private Telegram destination.

Multi-user hosted operation is not an implicit next stage. It would introduce
new authentication, isolation, retention, support and regulatory obligations
and requires a separate design decision.

Releases are evidence-led:

- CI must pass on supported Python versions;
- production changes name an exact commit;
- the host repeats tests before accepting a release;
- rollback uses the same mechanism with an earlier verified commit;
- secrets and state survive code replacement but never enter Git.

## Extension rule

New sources and destinations should use small explicit interfaces and the
existing normalised item model. Build an integration only when a real workflow
requires it.

Do not introduce generic plugin discovery, an event bus, multi-tenant
abstractions or framework machinery merely to anticipate possible users. A
clean seam is sufficient until a second concrete implementation proves what the
abstraction must support.

## Measure of success

Gaal succeeds when the user begins work with a more accurate understanding of
what matters, can see why each item was classified as it was, and can trust that
nothing was sent or changed without explicit authority.

Its value is measured in reduced oversight and increased confidence—not in the
number of messages processed or actions automated.
