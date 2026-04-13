# Support V1 Client-Facing Naming Guide

This guide is for buyer-facing, commercial, and pilot-deliverable documents in `use_cases/support_v1`.

Use the preferred client-facing term in customer-facing prose. Keep the internal technical term in scripts, evaluation outputs, artifact names, and engineering documentation where exact implementation labels matter.

## Core term map

| Internal technical term | Preferred client-facing term | When to use each |
| --- | --- | --- |
| `default iml` | standard routing | Use the client-facing term in buyer and pilot materials when describing the uncalibrated Support V1 routing result. Keep `default iml` in evaluation tables, run outputs, and technical notes. |
| `calibrated iml` | calibrated routing | Use the client-facing term in commercial and pilot comparison language. Keep `calibrated iml` in evaluation outputs, script results, and technical references. |
| `baseline` | comparison method | Use the client-facing term when the audience only needs to know there are alternate methods used for comparison. Keep `baseline` in evaluation and technical analysis documents. |
| `routing intelligence layer` | routing layer | Use the client-facing term in buyer and commercial prose. Keep the internal term in architecture and system-level engineering documents. |
| `fast_path` | fast path | Use the client-facing term in prose with normal spacing and no code formatting. Keep `fast_path` in schemas, labels, prompts, and evaluation artifacts. |
| `deep_path` | deeper review path | Use the client-facing term when describing escalation or deeper handling in customer-facing materials. Keep `deep_path` in schemas, labels, prompts, and evaluation artifacts. |
| `ingest modality` | export format | Use the client-facing term in pilot scoping, onboarding, pricing, and buyer materials. Keep `ingest modality` in runbooks, evaluation comparisons, and engineering docs that compare modalities directly. |
| `pilot package` | pilot deliverables pack | Use the client-facing term when describing what the client receives. Keep `pilot package` in internal workflow references, artifact names, and scripts. |
| `handoff bundle` | handoff materials | Use the client-facing term in summaries, pricing, and deliverable descriptions. Keep `handoff bundle` in script names, exported artifact names, and internal ops references. |

## Related format terms

| Internal technical term | Preferred client-facing term | When to use each |
| --- | --- | --- |
| `raw_ingest` | raw JSON export path | Use the client-facing term in buyer and pilot documents. Keep `raw_ingest` when referring to runner names, evaluation outputs, or exact internal workflow labels. |
| `mapped_ingest` | mapped CSV export path | Use the client-facing term in client-facing scoping language. Keep `mapped_ingest` in engineering and evaluation references. |

## Usage rules

- Prefer readable prose over backticked internal labels in client-facing documents.
- If the internal label adds needed precision, introduce it once in parentheses after the preferred client-facing term.
- Avoid underscore-style labels in buyer-facing prose unless they are being cited exactly.
- Keep technical specificity where it affects scope, evidence, or constraints; do not replace precise claims with vague marketing language.
