# Intuition Memory Layer

An explicit, interpretable MVP for a decision-memory layer that compresses historical evidence about an entity into a dynamic profile used for routing downstream decisions.

This repository is an early-stage research prototype. It is not a production memory system, not a learned model, and not a benchmark-backed claim that this approach outperforms simpler baselines. The value of the current repo is that the memory state, update logic, decay behavior, revalidation triggers, and routing reasons are all inspectable.

## Why This Project Exists

Many AI systems need some form of memory when making repeated decisions about an entity such as a user, collaborator, vendor, or agent. Two common failure modes show up quickly:

- naive summary memory collapses history into a static text summary that is hard to update, hard to decay, and hard to audit
- opaque latent memory can be effective in practice, but it makes it difficult to inspect what changed, why confidence moved, or why a system routed a decision one way versus another

This project explores a third option: a compact but explicit decision-memory layer that preserves a visible state surface and a visible update loop.

## Core Idea

The system maintains an `IntuitionProfile` per entity. Instead of storing a free-form summary, it stores a small set of interpretable attributes and profile-wide control signals:

- attributes: `trust`, `stability`, `predictability`, `cooperativeness`, `risk`
- profile signals: `overall_confidence`, `unknownness`, `freshness`, `contradiction_load`

Incoming events are mapped into explicit evidence units. Those evidence units update the profile over time. The profile then serves as a routing layer:

- if the profile is confident, fresh, low-contradiction, and low-unknownness, low-stakes decisions may use a `fast_path`
- otherwise the system routes to `deep_path`

What makes this different from naive summary memory is that the state is structured, decays over time, and produces explicit decision reasons. What makes it different from opaque latent memory is that the full update path is inspectable and testable.

## Current MVP Architecture

The current MVP is deliberately small and explicit:

1. `Event` objects capture timestamped observations with reliability, polarity, intensity, source, and metadata.
2. `iml.extractor` maps each event type into one or more `EvidenceUnit` updates.
3. `iml.update_engine` applies those evidence units to the profile and recomputes aggregate state.
4. `iml.decay` lowers freshness and attribute confidence as time passes, which increases unknownness.
5. `iml.revalidate` applies a simple heuristic recovery step when the profile becomes stale, low-confidence, highly contradictory, or too unknown.
6. `iml.decision` routes the next action to `fast_path` or `deep_path` based on explicit thresholds and stakes.
7. `iml.explain` formats evidence, profile snapshots, and routing results for auditability.

The current event vocabulary is intentionally narrow and hand-authored:

- `fulfilled_commitment`
- `cooperative_response`
- `ignored_request`
- `contradiction_detected`
- `long_inactivity`

This is enough to exercise the end-to-end memory loop without hiding behavior behind learned weights or large prompt logic.

## Repository Structure

```text
.
|-- datasets/
|   `-- synthetic_entities.json
|-- iml/
|   |-- models.py
|   |-- extractor.py
|   |-- update_engine.py
|   |-- decay.py
|   |-- revalidate.py
|   |-- decision.py
|   |-- explain.py
|   `-- metrics.py
|-- tests/
|   |-- test_update_engine.py
|   |-- test_decay.py
|   |-- test_revalidate.py
|   `-- test_decision.py
|-- main.py
|-- run_evaluation.py
|-- EVALUATION_NOTES.md
|-- ROADMAP.md
`-- INVENTION_MEMO.md
```

Notes:

- `main.py` is the simplest end-to-end demo of event replay, decay, revalidation, and routing
- `run_evaluation.py` is the current synthetic evaluation runner
- `tests/` covers the core update, decay, revalidation, and routing logic
- `datasets/synthetic_entities.json` is a compact hand-authored scenario dataset for deterministic inspection

## Running The Project

### Install

```powershell
py -m pip install -r requirements.txt
```

### Run Demo

```powershell
py main.py
```

This prints:

- the initial profile
- extracted evidence for each demo event
- profile snapshots after updates
- a decay step
- revalidation output
- final low-stakes and high-stakes routing decisions

### Run Tests

```powershell
py -m unittest discover -s tests -v
```

### Run Evaluation

```powershell
py run_evaluation.py
```

The evaluation runner replays the synthetic dataset, applies decay across long gaps, triggers revalidation heuristics at the final decision point when needed, and reports both per-entity and aggregate metrics. Evaluation output includes a console summary and a machine-readable JSON artifact; the current artifact structure is documented in `docs/evaluation_artifact_format.md`.

## Current Evaluation Scenarios

The synthetic dataset currently contains five scenario families:

- `stable_good_actor`: repeated aligned positive evidence
- `false_positive_first_impression`: strong start followed by contradiction and ignored requests
- `false_negative_first_impression`: weak start followed by a long run of reliable follow-through
- `high_contradiction_actor`: alternating useful behavior and repeated contradictions
- `sparse_data_actor`: long gaps, weak recency, and limited evidence density

The current runner reports:

- final routing choice
- routing reason
- event count and decay checkpoints
- whether revalidation triggered and why
- first-impression trust and final trust
- final confidence, unknownness, freshness, and contradiction load
- aggregate counts for `fast_path` and `deep_path`
- a simple false-first-impression recovery proxy

This evaluation is a sanity-check harness, not a benchmark. It is synthetic, tiny, deterministic, and designed for inspectability rather than coverage.

## Current Status

What this repo is:

- an explicit research MVP for interpretable decision memory
- a concrete profile/update/decay/revalidation/routing loop
- a small deterministic evaluation harness with unit tests
- a useful surface for discussing semantics, thresholds, and failure modes

What this repo is not:

- not a production-ready memory subsystem
- not a learned or latent memory architecture
- not a large-scale evaluation suite
- not a benchmarked comparison against naive summary memory or other baselines
- not evidence of real-world generalization

One practical implication of the current thresholds is that the synthetic evaluation is conservative: the present runner routes all current scenarios to `deep_path`, including the stable-good case. That is a useful research signal, not a polished final behavior.

## Next Steps

The current roadmap focuses on making the prototype more decision-useful before making it more complex:

- deepen baseline evaluation beyond the current naive-summary and full-history scorers
- strengthen recovery metrics beyond the current midpoint-crossing proxy
- expand synthetic scenarios to cover ambiguity, mixed reliability, and concept drift
- refine profile semantics where evaluation interpretation is currently awkward
- improve evaluation outputs with machine-readable artifacts and better run-to-run comparison
- only consider learned tuning after the explicit system is better validated

## Related Project Docs

- `EVALUATION_NOTES.md`: scenario semantics, metric definitions, and limits of the current synthetic runner
- `ROADMAP.md`: staged plan for baselines, metrics, scenario coverage, and evaluation improvements
- `INVENTION_MEMO.md`: invention memo describing the current framing, scope, and implementation boundaries
