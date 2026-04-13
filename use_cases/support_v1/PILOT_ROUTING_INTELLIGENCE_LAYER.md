# Support V1 Pilot Routing Intelligence Layer

## What this artifact adds

This artifact defines `support_v1` as a pilot-ready routing intelligence layer for support workflows: a bounded layer that sits between raw support exports and final queue-routing review, and that can be described clearly to internal operators, technical founders, and pilot buyers.

## What the layer is

`support_v1` is a support-specific routing intelligence layer for first pilots. It takes a bounded helpdesk export, reconstructs visible case history, applies the current calibrated routing logic, and produces a reviewable routing comparison without requiring core-engine changes.

It is designed for one pilot workflow at a time: one partner, one queue, one export modality, one redacted slice, and human review throughout.

## What it takes in

- One bounded support export slice in a currently supported format: `raw_ingest`, `csv_ingest`, `mapped_ingest`, or `zendesk_like`
- The ids, joins, timestamps, and ordering fields needed to validate the export contract
- Enough case detail to reconstruct visible history safely
- Redaction/privacy constraints for the pilot slice
- A small labeled review set, or reviewer time to create one

## What it produces

- A contract-validation readout on whether the export is usable for the current flow
- A normalized, auditable support slice in the current `support_v1` schema
- A reviewable routing comparison across `iml`, calibrated `iml`, `naive_summary`, and `full_history`
- Pilot handoff materials that make the result usable for operator review and a stop / repeat / expand decision

## Where it sits in the support workflow

The layer sits after export intake and before any broader workflow decision about routing, escalation, or expansion.

In practical terms, the current flow is:

1. Intake one bounded export slice.
2. Validate the export contract.
3. Normalize the data and reconstruct visible support history.
4. Run the routing comparison layer.
5. Review outputs with a human owner before any pilot decision.

## What it already does today

- Supports five current evaluation modes: `labeled_support`, `raw_ingest`, `csv_ingest`, `mapped_ingest`, and `zendesk_like`
- Validates export readiness before normalization
- Reconstructs support history into the current evaluation flow
- Compares calibrated `iml` against default `iml` and simpler baselines on the same labeled slices
- Produces pilot packages, handoff bundles, and a validated real pilot workspace for `raw_ingest`

Current evidence is strong enough for a first bounded pilot, but still small-sample and pilot-stage rather than production-proven.

## What it does not do yet

- Unattended production routing
- Deep live integration into a customer's ticketing platform
- Broad multi-queue rollout
- SLA-backed operational use without manual review
- A proven real-customer evidence base across multiple external pilots

## Why the calibrated layer matters

Default routing and simple baselines are easier to deploy, but they do not use the current support-specific calibration layer that is helping `support_v1` make better use of reconstructed case history.

In the current repo evidence, calibrated `iml` clears the best baseline on the largest evaluated slice in 5 of 5 supported modalities. The practical value is not that it guarantees perfect routing; it is that it appears to reduce over-conservative routing on clean support histories while preserving the contradiction and staleness protections already built into the flow.

That makes the layer more useful than a default-route or summary-only baseline when the goal is to decide which cases can stay on a faster path and which need deeper review.

## What a first pilot use looks like

The first pilot use is narrow by design:

- One partner
- One support queue or workflow
- One supported export modality, preferably `raw_ingest`
- One small redacted and auditable slice
- One labeled review pass on the real slice
- Human review and manual override kept in place for the full pilot

The output of that first pilot is not a production rollout. It is a decision-ready package showing whether this routing intelligence layer is useful enough on a real support slice to justify repeating, expanding, or stopping the pilot.
