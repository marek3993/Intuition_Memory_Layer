# Intuition Memory Layer (IML)

## 1. Title

Intuition Memory Layer (IML)

## 2. One-paragraph summary

Intuition Memory Layer is an explicit decision-memory prototype for repeated decisions about the same entity over time. Instead of relying on a free-form summary, a vector-retrieval surface, or opaque latent state, it maintains a small inspectable profile with attribute values, confidence, freshness, unknownness, and contradiction load. Incoming events update that profile through explicit rules; time decay weakens stale evidence; revalidation is triggered when the profile becomes unreliable; and downstream routing uses visible thresholds to decide when a cheap path is acceptable versus when deeper reasoning is required.

## 3. Problem

Repeated decisions over long interaction histories are awkward for current memory patterns:

- Naive summary memory compresses history into text that is hard to update, decay, audit, or correct when early impressions were wrong.
- Opaque latent memory may be useful, but it is difficult to inspect what changed, why confidence moved, or why a later decision was routed a certain way.
- Re-running full-history reasoning on every decision is expensive, grows poorly with history length, and can become unstable as context accumulates.

## 4. Proposed approach

IML uses an explicit per-entity profile rather than a summary blob. The current MVP tracks interpretable attributes such as `trust`, `stability`, `predictability`, `cooperativeness`, and `risk`, along with profile-level control signals: `overall_confidence`, `unknownness`, `freshness`, and `contradiction_load`.

Each event is converted into small evidence units, applied to the profile, and recorded through an inspectable update path. Confidence and freshness decay over time so stale evidence naturally becomes less actionable. Contradictions raise an explicit contradiction load instead of being silently averaged away. When the profile becomes too stale, low-confidence, contradictory, or unknown, a revalidation step is triggered. Routing then uses explicit thresholds to decide whether a low-stakes decision can take a `fast_path` or should fall back to a `deep_path`.

## 5. Why this is different

- Unlike summary-only approaches, the memory state is structured, updateable, and decay-aware.
- Unlike pure retrieval, the main surface is not just a bag of recalled events; it is a maintained decision profile with explicit control signals for uncertainty, contradiction, and freshness.
- Unlike opaque latent state, the state variables, update rules, revalidation triggers, and routing reasons are visible and testable.

The point is not to claim that explicit memory is universally better. The point is to make repeated-decision memory inspectable enough to debug, evaluate, and deliberately improve.

## 6. Current prototype status

The repo already contains:

- an MVP implementation for event extraction, profile updates, decay, revalidation, explanation, and routing
- unit tests covering the core update, decay, revalidation, and decision logic
- a synthetic evaluation runner over five hand-authored scenario families
- baseline comparison code for a naive summary scorer and a full-history scorer
- supporting docs for architecture, evaluation notes, and roadmap

This is an early research prototype, not a production system and not evidence of real-world superiority.

## 7. Why it matters

If the goal is repeated decisions by assistants or agents, explicit memory has practical advantages:

- inspectability: you can see the state that drove the decision
- controllability: thresholds and update semantics can be changed deliberately
- decision consistency: the system does not need to reconstruct its stance from scratch every time
- recoverability: wrong early impressions can be revised instead of fossilized in a summary
- suitability for agent routing: the profile can decide when to trust a cheap path and when to escalate

Even when the current behavior is conservative, that conservatism is legible: disagreements with baselines and threshold failures are exposed rather than hidden.

## 8. Immediate next step

The immediate next step is not to make the system more complex. It is to validate the explicit MVP more rigorously: strengthen baselines, add richer recovery and trajectory metrics, expand synthetic scenario coverage, and improve evaluation quality. Learned variants may be worth exploring later, but only after the explicit profile-and-routing design demonstrates value on a stronger evaluation harness.
