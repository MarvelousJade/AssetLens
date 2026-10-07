# Debugging exercises: learner instructions

The working project at rework baseline `b990b6b` is verified before these exercises.
Two defects are intentionally introduced only on `shaoyu/learning`; they are not production
incidents. The final learning branch will be corrected and merged into
`shaoyu/rework` independently of your study progress, preserving faulty and fix
commits. No intentional defect may remain in the merged working state.

Do not read the separate solutions document or fix diffs until you are ready.
Ask for progressive hints if you get stuck. Describe personal investigation only
after recording your own observations in the journal's learner-notes section.

## Safe setup

Use a separate worktree at the desired faulty commit rather than resetting your
working implementation branch. Commit IDs will be recorded below after the
checkpoints are verified. Replace `<checkpoint>` with the exercise's faulty ID:

```text
git worktree add --detach ../AssetLens-debug <checkpoint>
```

From that worktree's `apps/api`, create/activate a Python 3.12+ virtualenv and
install `pip install -e ".[dev]"`. Do not copy runtime `.env` or personal databases.
Tests use their own ignored database. Run `python -m pytest` and
`python -m ruff check app tests scripts` there. Remove the worktree only after
preserving your notes/changes; do not force-remove uncommitted work.

## Exercise 1: inconsistent drawdown path

**Faulty checkpoint:** `4d8e3e2` (verified intentional failure).

**Simulated report:** “The portfolio dips below an earlier high, but some risk
values look smaller than the expected decline. A later recovery is shown as if
that decline has already disappeared.” This is an educational report, not a real
customer incident.

**Reproduce:** Run:

```text
python -m pytest tests/test_debugging_regressions.py -k drawdown --no-cov
```

Compare each returned value to a hand calculation for the test's input series.
Use the documented maximum-drawdown definition, not a memorized expected minimum.

**Investigation goals:** Record expected/actual values, form hypotheses, identify
where divergence first appears, test at least one counterexample, and propose a
minimal correction with a regression test. Explain what information must persist
between observations. Do not change expected results to fit the implementation.

## Exercise 2: cancellation followed by a late result

**Faulty checkpoint:** To be recorded after failure verification.

**Simulated report:** “Cancelling a scenario appeared to work, but a later status
read showed a result and a different terminal timestamp.” The report is simulated;
its consequences are hypothetical, not a claim of production impact.

**Reproduce:** Run:

```text
python -m pytest tests/test_debugging_regressions.py -k cancelled --no-cov
python -m pytest tests/test_scenarios.py --no-cov
```

These checks deliberately control interleaving through independent sessions.
You do not need to create a race with sleeps or a live worker.

**Investigation goals:** Trace when state becomes visible to each session,
compare the returned object to persisted state, establish which transitions are
allowed, and explain what must be true at the moment of a terminal write. Preserve
the cancellation timestamp and demonstrate that late outcomes cannot publish a
result or completion audit for a cancelled run.

## Notes template

For each exercise, record separately from implementation notes:

- Expected/actual behavior and reproducible command.
- Your hypotheses, inspected evidence, and unsuccessful attempts.
- Your narrowed cause and proposed correction.
- Alternatives, tradeoffs, and remaining limits.
- Actual regression and broader verification results.
- What you learned and how to explain the investigation without jargon.

Solutions and final verification will be maintained separately. Avoid presenting
these intentional defects as naturally discovered problems in the working branch.
