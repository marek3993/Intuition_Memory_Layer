# Roadmap

## Stage 1: Establish Baselines

Add two simple comparison baselines against the same synthetic dataset and the same final reporting surface:

1. A naive summary baseline that collapses the event stream into a small hand-written aggregate state.
2. A simple full-history scorer that uses all events directly without decay or revalidation semantics.

Goal: determine whether the explicit IML update loop is actually adding value over simpler alternatives before expanding the design.

## Stage 2: Strengthen Recovery Metrics

Keep the current trust-midpoint recovery proxy, but add more informative recovery measurements:

1. first-impression trust after a defined window, not just after the first event
2. time or event-count until recovery
3. maximum wrong-direction magnitude after the initial impression
4. whether routing also recovers, not just trust

Goal: distinguish "eventually crossed 0.50" from "recovered quickly and stayed recovered."

## Stage 3: Expand Synthetic Scenario Coverage

Add a small number of new hand-authored scenarios before moving to larger generation:

1. mixed-reliability evidence
2. gradual concept drift rather than abrupt flips
3. benign contradiction that later resolves
4. bursty positive behavior followed by long silence
5. sparse but consistently good actor versus sparse and inconsistent actor

Goal: cover failure modes that the current five scenarios only partially represent, especially around ambiguity and source quality.

## Stage 4: Refine Profile Semantics Where Needed

Review profile-field semantics that affect evaluation interpretation, especially:

1. whether `last_revalidated_at` should start as profile creation time, first event time, or `None` until the first real revalidation
2. whether initial trust should be measured after one event or after a fixed first-impression window
3. whether revalidation should be modeled as a state change with its own explicit evidence trail

Goal: make the profile easier to reason about and make evaluation outputs less sensitive to implementation convenience.

## Stage 5: Improve Evaluation Output

Make the evaluation easier to compare across runs without changing the core model:

1. emit machine-readable JSON or CSV alongside console output
2. report per-scenario aggregates, not only global aggregates
3. include decision-threshold reasons in a compact tabular form
4. separate final-state metrics from trajectory metrics
5. make it easy to diff one run against another

Goal: turn the current sanity-check script into a usable internal evaluation artifact.

## Stage 6: Validate The Explicit MVP Before Any Learned Variant

Only after the explicit system is stable on the stronger synthetic evaluation:

1. consider learned tuning of event weights or thresholds
2. compare learned variants against the explicit baseline, not in isolation
3. keep the explicit interpretation surface and use learning only where it demonstrably improves recovery or routing quality

Goal: treat a learned variant as a later optimization step, not as a substitute for validating the explicit MVP.
