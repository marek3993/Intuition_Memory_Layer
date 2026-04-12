# Support V1 Calibration Integration Notes

`support_v1` now has an optional calibration module that applies only after support history replay and before final routing. The rule stays domain-specific because the evidence behind it is still support-shaped: it was validated on the labeled support slice, depends on support event semantics such as `cooperative_response` and `fulfilled_commitment`, and explicitly guards against support inactivity and contradiction patterns.

It is not promoted into generic `iml/` behavior yet because the current win is calibration, not a proven cross-domain engine rule. Moving it into the core now would blur the line between generic routing logic and support-specific interpretation, and it would risk encoding support assumptions into unrelated domains before broader validation exists.
