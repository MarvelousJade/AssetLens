# Debugging solutions — spoilers

Read `debugging-exercises.md` first. This file is separate implementation-side
diagnosis material; it is not a record of the learner's personal investigation.
Do not use these intentional defects as stories about real users or production.

## Exercise 1: drawdown path

**Problem/reproduction:** Run the drawdown regression listed in learner instructions.
The correct baseline passed the full-path assertion before the defect was added.
On the faulty code, lint passed but the focused run produced two failures and
six passes in 1.11 seconds. Four of seven path points diverged; the existing
minimum test returned -0.12 instead of -0.2.

**Investigation:** Compare every output to the metric definition, especially the
first decline after a new high. The intentional change was selected to model a
plausible mistaken reference during an iteration refactor, not an arbitrary crash.
No unsuccessful learner investigation is invented.

**Root cause:** Comparing each value to the first observation loses highs reached
in preceding iterations. Maximum drawdown requires the maximum observed so far,
not the maximum of only the first and current observation.

**Correction:** Carry the running maximum forward, then divide by that maximum.
The original implementation was already correct; the exercise fix restores it.
Regression coverage includes declines, partial recoveries, and later new highs.

**Tradeoff:** No meaningful new architecture tradeoff exists. The streaming
accumulator is linear time/constant extra state; repeatedly scanning each prefix
would be simpler to express mathematically but unnecessarily quadratic.

**Checkpoint:** `4d8e3e2` on `shaoyu/learning` preserves the faulty code. The
correction restores the previously correct accumulator. Lint and all 55 API tests
passed in 4.57 seconds, with 85% statement coverage.

**Verification:** Baseline full-path test passed; the faulty focused run produced
two failures as recorded above. The corrected full API suite passed as recorded
above. Existing seeded metrics are not claimed to have been defective on main.

**Lesson/interview outline:** A correct aggregate minimum can hide incorrect
intermediate points; test the complete path and preserve required state across
iterations. Say this was intentionally introduced if discussing this exercise.

**Progressive hints, only when ready:**

1. Calculate the documented denominator independently for each observation.
2. List information from earlier observations that the current iteration needs.
3. Compare the denominator after the first high to what the next iteration retains.

## Exercise 2: late scenario outcome

Details will be recorded after the first exercise is corrected. It will be an
intentional regression of an already-correct rework lifecycle, not a new claim
about a production cancellation incident.
