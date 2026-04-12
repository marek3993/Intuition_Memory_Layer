# Intuition Memory Layer (IML)
## Invention Memo v0.2

## 1. Working Framing

`Intuition Memory Layer` (`IML`) is the current working title for an explicit decision-memory layer that maintains a compact, interpretable profile for an entity and uses that profile to route downstream decisions.

In this memo, "intuition" is used as a computational metaphor for a fast, profile-based decision surface. It does not imply anthropomorphic feeling, consciousness, or opaque instinct. If needed for external filings or technical standardization, the project could later adopt a more literal naming convention while preserving the same underlying design.

## 2. Problem Statement

Many systems need to make repeated decisions about the same entity under partial, changing, and sometimes contradictory evidence. Examples include repeated interactions with a user, collaborator, external service, tool, or agent. The practical problem is not just storing history. The harder problem is maintaining a compact decision state that can answer questions such as:

- What does the system currently believe about this entity?
- How confident is that belief?
- How much of the profile is now unknown because evidence is sparse or stale?
- Has contradictory evidence accumulated to the point that shortcut decisions are unsafe?
- When is it acceptable to take a fast path, and when should the system escalate to deeper review?

Common memory patterns do not address this cleanly:

- Naive summary memory compresses history into text, but the update semantics, decay behavior, contradiction handling, and audit trail are weak or implicit.
- Opaque latent memory may retain useful signal, but the represented state and the reason for downstream routing are not directly inspectable.
- Retrieval-only approaches can surface past observations, but they do not by themselves maintain a persistent decision state with explicit confidence, unknownness, decay, and routing logic.

The proposed invention addresses this gap by introducing an explicit, interpretable decision-memory layer rather than a free-form summary or a hidden latent state.

## 3. Proposed Solution

The core proposal is a per-entity `IntuitionProfile` that stores a small number of interpretable attributes together with profile-wide control signals. Incoming events are converted into explicit evidence updates. The profile evolves over time, decays when evidence becomes stale, can be revalidated when its state becomes unreliable, and is then used to route low-stakes decisions to either a `fast_path` or a `deep_path`.

The central concept is unchanged across the broader invention direction and the current MVP:

- explicit decision-memory layer
- interpretable profile
- confidence
- unknownness
- decay
- contradiction handling
- revalidation
- fast-path vs deep-path routing

## 4. State Model And Lifecycle

### 4.1 Profile Structure

In the current implementation, each profile maintains five attribute dimensions:

- `trust`
- `stability`
- `predictability`
- `cooperativeness`
- `risk`

Each attribute has an explicit value and its own confidence, rather than a single undifferentiated score.

The profile also maintains profile-wide control signals:

- `overall_confidence`: aggregate confidence across attributes
- `unknownness`: how much of the effective decision state should be treated as insufficiently known
- `freshness`: how recently the state has been supported by new evidence
- `contradiction_load`: how much conflicting evidence has accumulated

This separation matters. Attribute values represent directional belief about the entity, while the control signals represent whether that belief is current and decision-usable.

### 4.2 Update Path

Incoming observations are represented as timestamped events. Each event is deterministically mapped into one or more `EvidenceUnit` updates. Those updates apply bounded changes to specific profile attributes and to attribute confidence.

In the current MVP, this event-to-evidence mapping is hand-authored and intentionally narrow. Implemented event types include:

- `fulfilled_commitment`
- `cooperative_response`
- `ignored_request`
- `contradiction_detected`
- `long_inactivity`

Contradiction is handled as an explicit first-class signal rather than being left implicit inside a summary. In the current implementation, contradiction events directly increase `contradiction_load`, while non-contradiction events allow that load to relax gradually.

### 4.3 Time Awareness

The profile is not static after an update. Over elapsed time, the system applies decay. In the current MVP, decay reduces freshness and attribute confidence, which in turn increases unknownness. Importantly, the current decay logic does not directly rewrite attribute values. It weakens the system's confidence in those values and makes routing more conservative as evidence ages.

This yields a cleaner distinction between:

- what the profile last leaned toward
- how strongly that state is still supported
- whether the profile remains safe to use for shortcut decisions

### 4.4 Revalidation

The broader invention direction includes revalidation as a mechanism for recovering from stale, weak, or contradictory state before reuse.

In the current MVP, revalidation is implemented as a bounded heuristic adjustment step triggered by threshold conditions such as low freshness, low confidence, high contradiction load, high unknownness, or excessive time since last update. It is not yet a full evidence re-read or a retrieval-backed reconciliation pass. That broader version remains part of the research direction, not the implemented claim of the repository.

### 4.5 Routing

The profile is operationalized through routing. The system uses explicit thresholds over `overall_confidence`, `freshness`, `contradiction_load`, `unknownness`, and task stakes to choose between:

- `fast_path`: use the current profile directly for a lower-cost decision
- `deep_path`: escalate to a slower, more careful path

In the current MVP, high-stakes decisions always go to `deep_path`. Low-stakes decisions can use `fast_path` only when the profile is sufficiently confident, fresh, low-contradiction, and low-unknown. Routing reasons are explicit and inspectable.

## 5. Differentiation From Other Memory Approaches

### 5.1 Versus Naive Summary Memory

Naive summary memory usually produces a textual or loosely structured synopsis of history. That can be useful for recall, but it does not naturally provide first-class mechanics for confidence, unknownness, contradiction accumulation, temporal decay, or deterministic routing.

IML differs in that the memory state is not a summary string. It is an explicit profile with defined update semantics and explicit control signals that can be tested and audited.

### 5.2 Versus Opaque Latent Memory

Opaque latent memory can encode history in a compact internal state, but the representation is not directly inspectable and its routing consequences are difficult to audit. When a downstream system acts on that memory, it is harder to explain what changed, why confidence moved, or why the system escalated or did not escalate.

IML is designed so that profile state, update causes, decay behavior, contradiction state, and routing reasons remain visible.

### 5.3 Versus Retrieval-Only Approaches

Retrieval-only approaches return past observations on demand, but they do not by themselves maintain a persistent decision surface that has already integrated recency, contradiction, and uncertainty into a compact state.

IML is intended to sit between raw history and downstream action. It preserves an explicit, continuously updated decision profile rather than forcing each downstream decision to reconstruct that state from scratch.

## 6. Novelty Surface

The novelty is not any single scoring heuristic in isolation. The novelty surface is the explicit combination of:

- a persistent, interpretable per-entity decision profile rather than a free-form summary
- simultaneous representation of attribute values and profile-level usability signals
- first-class treatment of confidence, unknownness, freshness, and contradiction as distinct operational variables
- a lifecycle that includes explicit update, passive decay, contradiction handling, and revalidation
- direct use of that profile for auditable `fast_path` versus `deep_path` routing

Expressed differently, the proposal is a decision-memory layer whose purpose is not merely to remember history, but to maintain an inspectable, time-aware, uncertainty-aware decision surface.

## 7. Current MVP Status

The current repository already implements a concrete explicit MVP with:

- an explicit `IntuitionProfile` model
- deterministic event-to-evidence extraction
- profile update logic
- passive decay over elapsed time
- heuristic revalidation
- explicit `fast_path` versus `deep_path` routing
- unit tests for update, decay, revalidation, and routing
- synthetic evaluation over hand-authored scenario traces
- baseline comparison against naive-summary and full-history scorers

The repository also includes supporting architecture and evaluation notes. The current implementation is still intentionally narrow: single-entity replay, hand-authored event semantics, heuristic thresholds, and synthetic rather than benchmark-grade evaluation.

## 8. Implemented Scope Versus Broader Invention Direction

### 8.1 Implemented In This Repository

The current codebase demonstrates the following implemented behavior:

- an explicit profile with five attribute dimensions and profile-wide control signals
- deterministic profile updates from timestamped events
- contradiction accumulation and gradual contradiction relaxation
- time-based decay that lowers freshness and confidence and increases unknownness
- threshold-based revalidation triggers with a bounded heuristic recovery step
- threshold-based routing with explicit reasons
- a synthetic evaluation harness that compares IML against two simpler baselines

### 8.2 Not Yet Implemented, But Part Of The Broader Direction

The broader invention direction may include, but the current repository does not yet implement:

- richer event vocabularies and source-specific evidence semantics
- retrieval-backed or history-backed revalidation rather than the current heuristic state adjustment
- calibration methods that tie confidence and unknownness to stronger correctness targets
- broader scenario coverage and machine-readable evaluation artifacts
- multi-entity persistence, service integration, or production controls
- learned tuning or learned variants built on top of the explicit state model

This memo should therefore be read as an invention/research description anchored by a working explicit MVP, not as a claim that the full research direction has already been implemented.

## 9. Risks And Technical Challenges

Several technical risks are already visible:

- Hand-authored event semantics may be brittle across domains.
- Confidence and unknownness may be operationally useful without yet being well calibrated.
- Heuristic revalidation can improve state usability without introducing genuinely new evidence.
- Conservative thresholds may over-route to `deep_path`.
- A compact fixed attribute set may miss context-specific factors needed in some domains.

These risks are not disqualifying, but they matter because the invention depends on the quality of the explicit state semantics, not just on the existence of a profile object.

## 10. Mitigations And Research Discipline

The current repository takes several credible steps toward disciplined evaluation:

- core state transitions are unit tested
- the evaluation path is synthetic and deterministic, which makes behavior inspectable
- baseline comparisons are included so the explicit layer can be compared against simpler alternatives
- routing reasons are surfaced directly instead of hidden in aggregate scores

The present repo does not establish benchmarked superiority, production readiness, or real-world generalization. It is better understood as a concrete testbed for validating whether an explicit decision-memory layer is useful enough to justify further development.

## 11. Candidate Claim-Area Themes

The following themes may be useful for later legal or invention analysis. They are not assertions of patentability.

- Maintaining a persistent, interpretable decision-memory profile for an entity using explicit attribute state plus profile-level confidence, unknownness, freshness, and contradiction signals.
- Updating that profile through explicit evidence units derived from incoming events rather than through free-form summarization alone.
- Applying passive temporal decay to reduce decision usability without necessarily rewriting attribute values.
- Treating contradiction as a first-class operational state that directly affects routing.
- Triggering revalidation based on profile degradation conditions before reusing the profile for decisions.
- Routing between `fast_path` and `deep_path` as a direct function of the profile's state and uncertainty signals.
- Producing auditable reasons for both profile change and routing outcome.

## 12. Development Path

The current development path should remain disciplined and explicit:

- strengthen the synthetic evaluation with better recovery, calibration, and trajectory metrics
- expand scenario coverage before claiming broad usefulness
- refine revalidation so it is more strongly tied to evidence and less purely heuristic
- continue comparing against simpler baselines as the design evolves
- only consider learned tuning after the explicit state model has been validated on stronger evaluation surfaces

## 13. Closing Position

The core proposal is an explicit decision-memory layer that maintains an interpretable profile with confidence, unknownness, decay, contradiction handling, revalidation, and route selection between `fast_path` and `deep_path`.

What is strongest about the current repository is not scale or benchmark performance. It is that the central loop now exists in executable form: events become explicit evidence, evidence updates an interpretable profile, time degrades that profile, revalidation can be triggered, and routing decisions are made from inspectable state. That makes the project a credible research and invention artifact while still leaving substantial room for further validation and refinement.
