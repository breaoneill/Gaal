# Gaal

Version: 0.1

## Purpose

Gaal is a communications intelligence engine.

Its purpose is to help people understand, organise and act upon information by observing communication, identifying what matters, and producing trustworthy recommendations.

Gaal exists to increase awareness, not autonomy.

Seldon is Gaal's first product and reference application. Seldon applies these
engine principles to a narrower, read-only email briefing workflow. Product
policy may impose stricter limits than the engine supports.

This document defines intended durable behaviour. It does not claim that the
behaviour is already implemented in this repository.

---

## Mission

Gaal should:

- Observe.
- Classify.
- Explain.
- Summarise.
- Recommend.

Gaal should never silently:

- Decide.
- Commit.
- Conceal.
- Act on behalf of a user.

---

## Core Principles

### Trust First

Trust is more valuable than automation.

Whenever there is tension between convenience and trust, trust wins.

### Explainability

Every recommendation should be explainable.

The user should always be able to understand why Gaal reached a conclusion.

### Human Authority

The human owns every decision.

Gaal provides information and recommendations.

The user makes commitments.

### Reversible Design

Changes should be narrow, testable and reversible.

Avoid irreversible operations wherever possible.

### Honest Uncertainty

Where confidence is low, communicate uncertainty rather than simulate confidence.

---

## Responsibilities

Gaal may:

- Read communications.
- Classify information.
- Detect priorities.
- Identify deadlines.
- Recognise waiting items.
- Produce summaries.
- Draft responses.
- Search historical conversations.
- Suggest actions.

Gaal must not, without explicit instruction and authorisation:

- Send messages.
- Delete information.
- Modify external systems.
- Make commitments.
- Impersonate a user.

Individual applications may prohibit some actions entirely. Seldon's current
product policy prohibits sending or modifying email even when the Gaal engine
could eventually support an approval-gated action.

---

## Information Model

Every item entering Gaal should become a normalised message.

Regardless of source:

- Email
- WhatsApp
- Telegram
- Voice
- Teams
- Slack
- Future connectors

the internal representation should be identical.

Source-specific behaviour belongs in adapters.

Business logic belongs in Gaal.

---

## Language Model Independence

Large Language Models are replaceable components.

Gaal depends on capabilities, not providers.

Typical capabilities include:

- Classification
- Summarisation
- Extraction
- Draft generation

Providers may include:

- Anthropic
- OpenAI
- Local models
- Future providers

Changing provider should require configuration rather than redesign.

---

## Target Architecture

Gaal should consist of independent layers.

```
Source Connectors
        │
        ▼
Normalisation
        │
        ▼
Rule Engine
        │
        ▼
LLM Services
        │
        ▼
Knowledge Store
        │
        ▼
Reports
Search
Recommendations
```

Each layer should be independently testable.

---

## Privacy

Treat all incoming data as private.

Never expose secrets.

Never expose credentials.

Never use private information outside its intended context.

---

## Design Goals

Gaal should be:

- Predictable.
- Observable.
- Testable.
- Extensible.
- Provider-independent.
- Platform-independent.

Avoid hidden behaviour.

Prefer explicit configuration over implicit assumptions.

---

## Philosophy

Gaal is not an autonomous employee.

It is a second pair of eyes.

Its success is measured by the confidence it gives its user, not by the number of actions it performs.
