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

**Checkpoints:** `4d8e3e2` preserves the faulty code; `2778165` is its separate fix.
Both are preserved through merge `b23ab90`. The correction restores the previously correct accumulator. Lint and all 55 API tests
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

**Problem/reproduction:** A cancellation committed during calculation must remain
terminal, with the cancellation timestamp and no published result/completion
audit. The new timestamp regression passed before the intentional mistake.
On the intentional faulty code, lint passed while three focused cases failed
and ten passed in 1.64 seconds: committed cancellation became completed or failed.

**Investigation:** Use the controlled separate-session test to compare stored
state before cancellation, after cancellation, and after late worker persistence.
The simulated report is educational; no real user incident or unsuccessful
personal debugging attempt is invented.

**Root cause:** Removing terminal-state eligibility from the final UPDATE makes
a late worker overwrite any existing state for that ID. Prior object reads are
not an atomic eligibility check at write time.

**Correction:** Restore the `running` predicate and inspect the affected row count
before auditing completion. Cancellation that wins the database transition then
discards late results/errors. This restores the already-correct rework baseline;
it is not a new repair of a naturally discovered main-branch defect. Earlier
ordinary lifecycle defects and their real rework fix are documented separately.

**Tradeoffs:** Conditional writes need no new schema or lock service. A repeated
read/check followed by an unconditional write still races; a lock/lease design
would add complexity and is unnecessary for this tested invariant. Calculation
is not interrupted, and crashed-worker recovery remains outside this change.

**Verification:** New cancelled-timestamp baseline case passed in 0.33 seconds;
the intentional faulty run had three failures and ten passes as recorded above.
**Checkpoints:** `8255540` preserves the faulty state; `cacadc4` is its separate
fix. Both are preserved through merge `b23ab90`. Restored the guarded terminal write. Lint and all 56 API tests passed in
5.09 seconds with 85% coverage; SQLite migration upgrade/drift checks passed.
All eight frontend tests (5.03 seconds), standalone TypeScript checking, and
production build passed; both isolated Chromium journeys passed in 18.7 seconds.
The reviewed corrected state was integrated through `b23ab90`; post-merge API,
frontend/type/build, migration, and both Chromium checks passed. Exact commands
and results are recorded in the journal.

**Lesson/interview outline:** Persist lifecycle invariants as write predicates.
Explain the controlled interleaving, cancellation's preserved state/timestamp,
and winner-only audit, while accurately identifying the intentional provenance.

**Progressive hints, only when ready:**

1. Draw the allowed state transitions and mark terminal states.
2. Distinguish an ORM object's status from current persisted eligibility.
3. Inspect what conditions are enforced at the final write, not only earlier reads.
