# Support V1 Pilot Pricing Framework

## What this adds

This note adds a practical way to package and price a first paid Support V1 pilot after initial free or discounted validation work. It keeps the commercial ask aligned with the current pilot boundary: one partner, one queue, one export format, one bounded slice, and no core-engine changes.

## What the pilot includes

- One scoped pilot for one support queue or workflow.
- One supported export format and one redacted, auditable export slice.
- Contract validation for the supplied export.
- Normalization into the current Support V1 workflow.
- One labeled review pass on the real slice.
- One comparison readout across the current routing methods, including calibrated routing.
- One operator-facing handoff summary with recommendation, risks, and next-step decision.

## Explicitly out of scope

- Production deployment or broad rollout.
- Multi-queue or multi-region expansion in the first pilot.
- Net-new core-engine work or custom model development.
- Deep integration into the customer's ticketing platform.
- SLA-backed operational use without manual review.
- Large historical backfills or open-ended data cleanup work.

## Customer inputs required

- One bounded export sample in a supported format.
- Field and join context needed to validate ids, timestamps, and ordering.
- Redaction and privacy requirements for the pilot slice.
- One operational owner who can review outputs and answer workflow questions.
- A small labeled review set, or reviewer time to create one on the pilot slice.

## Deliverables

- Export contract-validation readout.
- Normalized and auditable pilot slice.
- Reviewable routing comparison artifact for the scoped slice.
- Pilot handoff summary with key findings, limits, and stop conditions.
- A recommendation to stop, repeat, expand, or move to a broader paid phase.

## Pilot package shapes

### 1. Lightweight validation pilot

Best when the buyer wants to confirm export fit and see whether a real slice is worth deeper work.

- Scope: one queue, one export slice, minimal label set.
- Focus: contract validation, normalization, first comparison readout.
- Good fit when: export quality and data readiness are still the main unknowns.

### 2. Standard pilot

Best default shape for a first paid pilot.

- Scope: one queue, one supported export format, one real redacted slice, one defined label review pass.
- Focus: validate export quality, produce a credible comparison, and tie the results to an ROI discussion.
- Good fit when: the team wants a decision-ready result for whether to repeat or expand.

### 3. Extended pilot

Best when the first buyer already accepts the core shape and wants more operational confidence before a larger commitment.

- Scope: larger slice, more reviewer coverage, or a second pass on the same queue.
- Focus: tighten confidence in data quality, routing behavior, and measured operational value.
- Good fit when: the standard pilot is not enough to support an internal budget or rollout decision.

## Pricing logic in principle

Pricing should be tied to delivery effort and decision value, not to broad market claims.

- Base pilot fee should cover setup, export validation, normalization, evaluation, and handoff.
- Price should increase with complexity drivers such as export messiness, mapping effort, label-review effort, and iteration count.
- The raw JSON export path should usually be the simplest commercial entry point because it is the strongest current starting path.
- CSV or mapped CSV pilots may justify higher pricing when field mapping, joins, or cleanup work is heavier.
- Extended pilots should be priced above the standard shape because they consume more review time and create more customer-specific handling.
- ROI upside can support the commercial case, but pilot pricing should not depend on promising a fixed savings outcome from today's evidence base.

## What justifies moving from free or discounted to paid

- The team can already validate exports, normalize data, run comparisons, and produce handoff materials with the current workflow.
- The buyer wants work on a real redacted export rather than a synthetic or internal sample.
- The pilot requires dedicated analyst or operator time, not just a quick qualification pass.
- The work will produce a decision artifact the customer can use for budget, workflow, or expansion choices.
- The customer asks for iteration beyond a simple readiness check, especially around labeling, review, or ROI framing.

## Practical commercial stance

Use free or discounted work to qualify fit quickly. Move to a paid pilot when the work shifts from "is this export even viable?" to "produce a credible decision package on our real queue." That keeps the first commercial step modest, aligns with the current readiness evidence, and avoids overstating production certainty.
