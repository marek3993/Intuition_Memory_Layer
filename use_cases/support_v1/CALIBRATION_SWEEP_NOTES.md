# Support V1 Calibration Sweep Notes

The next step is robustness testing, not immediate integration, because the current win is still narrow evidence. The combined calibration rule moves `support_v1` from `5/8` to `8/8` on the labeled slice, but that slice is tiny, hand-authored, and the rule was shaped after inspecting the exact three clean `fast_path` misses it now fixes. The ablation result is useful but also cautionary: `confidence_only` stays `5/8`, `unknownness_only` stays `5/8`, and only the combined adjustment flips the three misses. That is enough to justify a parameter sweep, not enough to claim the rule generalizes.

A reassuring sweep result would show the same qualitative behavior across a reasonable neighborhood of settings: the clean recent cooperative cases still flip to `fast_path`, the stale and contradiction-bearing cases stay on `deep_path`, and accuracy does not depend on one razor-thin threshold combination. In practice, the support-specific eligibility filter should remain selective, and nearby changes to the confidence boost or unknownness reduction should not suddenly create guardrail misses.

A brittle or overfit result would show that the current success collapses under small parameter movement. Examples include only one narrow setting recovering the three clean misses, nearby settings reintroducing the original false negatives, or any setting starting to promote sparse, stale, inactivity-heavy, or contradiction-present histories that currently route correctly to `deep_path`.

Decision after the sweep:

- If the result is robust, keep this calibration as the leading `support_v1` candidate and move to limited integration in the support adapter path, followed by a broader labeled validation set.
- If the result is brittle, do not integrate it. Keep the current conservative routing, treat the experiment as diagnostic only, and revisit support event mapping or a less example-shaped calibration rule.
