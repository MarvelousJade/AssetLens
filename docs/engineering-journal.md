# Engineering journal

This journal records observed implementation behavior and verification evidence.
It does not assert that the learner personally performed these investigations.
Learner notes belong in a separate section and should be filled in after study.
Intentional exercise defects must be identified as such and never attributed to
main unless independently reproduced there.

## Rework start: preserve the existing workflow

**Context:** Rework starts from `e13a1d8`, with portfolio-development instructions
committed as `d1b73ef` on `shaoyu/rework`. The initial working tree contained only
the previously staged `AGENTS.md` change. Recent commits cover ownership checks,
benchmark evidence, deployment configuration, and repository maintenance.

**Difficulty and constraints:** There is already a working-looking seeded
portfolio workflow, but historical verification is not proof that the current
local environment still works. Optional worker, deployment, and model-provider
paths add study overhead. The runtime `.env` and database must remain untouched.

**Alternatives:** A full rewrite would make the stack smaller only by discarding
existing behavior and tests. Keep the current local Next.js/FastAPI/SQLite path
and repair demonstrated issues instead. Do not add infrastructure for hypothetical
requirements.

**Evidence inspected:** `README.md`, `docs/architecture.md`,
`docs/methodology.md`, `docs/performance.md`, `docs/security.md`, API routes,
imports, scenarios, analytics, models, configuration, existing API tests,
frontend entry/dashboard, frontend test, browser test/configuration, and CI.
README contains both historical and newer test counts. Scenario and ingestion
claims need stronger boundary checks; these are investigation candidates, not
confirmed incidents.

**Decision:** Define the focused scope and acceptance checklist in
`docs/rework-plan.md`. Verify the baseline before choosing a behavioral increment.

**Tradeoffs:** Retaining optional deployment integrations leaves some complexity,
but avoids a speculative rewrite. Explain which paths are required locally and
which are extensions. Local checks do not establish production readiness.

**Baseline verification:** From Windows cmd.exe, run:

```text
cd /d "G:\C++ PROJECTS\AssetLens\apps\api" && python --version && python -m ruff check app tests scripts && python -m pytest
cd /d "G:\C++ PROJECTS\AssetLens\apps\web" && node --version && call npm test && call npx tsc --noEmit && call npm run build
```

The first API command stopped after reporting Python 3.12.10: system Python
could not import `ruff`, so neither lint nor tests ran. Inspection of
`apps/api/.venv/pyvenv.cfg` confirmed an existing Python 3.12.10 project virtual
environment. Retry using `.venv\Scripts\python.exe` for the same lint/test
commands. The retry passed lint and all 28 API tests in 7.86 seconds, with 83%
statement coverage over 932 statements. One dependency warning reports deprecated
Starlette/httpx TestClient integration; it did not fail verification. The first
attempt was an environment failure, not an application regression.

Frontend baseline also passed on Node v24.19.0: 1 Vitest test, `npx tsc --noEmit`,
and the Next.js 16.2.11 production build (compilation reported 9.8 seconds).
These results verify the existing automated baseline, not untested edge cases.
API tests select an isolated `.tmp/assetlens-test.db` in their fixture. The
existing Playwright suite was not run: its setup reuses servers and writes tracked
screenshots. Isolated native browser checks are recorded separately below.

**Migration verification:** With `DATABASE_URL=sqlite:///./.tmp/rework-migrations.db`,
run `.venv\Scripts\python.exe -m alembic upgrade head` and
`.venv\Scripts\python.exe -m alembic check` from `apps/api`. Both passed: initial
revision `20260724_0001` applied and no new upgrade operations were detected.
The temporary database is ignored; PostgreSQL migration execution was not tested.

**Environment hurdle:** Initial repository inspection ran through a Linux bash
mount of the Windows working directory. `rg` was unavailable; tracked file
listing and direct reads provided the inventory. A later bash invocation could
not locate a bash executable. Continue verification through the supported
Windows background shell instead of assuming a portable shell. No application
bug is inferred from this tool/environment failure.

**Commit hurdle:** The documentation commit initially failed because Git had no
author identity. After the user authorized using the existing identity, set
repository-local name/email to the values in recent commits; commit `d1b73ef`
succeeded. Do not fabricate attribution or modify global Git settings.

**Lesson:** Re-establish evidence at the actual revision and environment. Keep
hypotheses, historical observations, and fresh results distinct.

**Interview explanation:** An existing project can be improved without rewriting
it: first identify its useful workflow, constrain the scope, and verify behavior.
Architecture changes need evidence, not just a preference for a different stack.

## Browser baseline and empty-portfolio investigation

**Environment:** Next.js development server at `http://127.0.0.1:3100`, API at
`http://127.0.0.1:8875`, isolated API `.tmp/rework-smoke.db`, local task runner,
and deterministic copilot. The user's runtime database was not used.

**Observed baseline:** Demo entry displayed the seeded dashboard and benchmark
chart. The Technology drawdown scenario reached `ESTIMATED IMPACT`. Native
browser report download returned `Download was canceled`; no saved PDF is
claimed. Existing API report tests passed, but browser export needs separate
investigation. An initial browser navigation timeout recovered after inspection
and server-readiness confirmation; stale refs were replaced with stable visible
locators. One batch incorrectly placed session flags on individual rows; moving
them to the enclosing command corrected that automation error.

**Problem and reproduction:** From Holdings, enter `Rework empty portfolio` and
click Create. The browser displays `Portfolio has no market prices`. Inspection
then showed eight seeded holding rows and the old `Canadian Growth & Income`
selection still displayed, while import controls remained visible. This confirms
stale displayed data after creation, not the stronger hypothesis that import
controls necessarily disappear.

**Investigation:** `createPortfolio` updates the selected ID, but `loadPortfolio`
only updates all displayed data after a six-request `Promise.all` succeeds.
The empty portfolio's performance endpoint rejects missing market prices, so
that aggregate update never occurs. The earlier snapshot and portfolio list are
retained. The API's missing-history response is expected; the UI has coupled
holdings display to availability of historical analytics.

**Provenance:** Naturally encountered on the pre-fix rework baseline. No
intentional defect was introduced. The correction and regression tests were
verified together before committing this increment.

**Tradeoffs and next step:** Handle empty holdings explicitly and keep them
usable for import rather than fabricate performance metrics. Test creation,
portfolio switching, and analytics failures. Do not replace every dashboard
component to repair this data-loading boundary.

**Increment acceptance criteria:** Creating an empty portfolio displays the new
selection and no seeded holdings, retains import controls, and avoids requesting
performance for empty holdings. A valid import enables analytics and report export.
If a nonempty portfolio's analytics fail, show only that selected portfolio's
holdings and disable export, never retain another portfolio's snapshot. Added
component regressions for these journeys before changing the implementation.

**Pre-fix verification:** `npm test -- app/components/Dashboard.test.tsx` failed
both tests in 22.37 seconds. Creation did not update the displayed selection;
switching to a portfolio with failed analytics retained the `SEEDED` holding.

**Fix:** Load the portfolio list and holdings before requesting historical
analytics; skip those analytics for empty holdings. Clear the previous snapshot
on selection changes, retain the selected holdings on analytics failure, and
render explicit empty/unavailable overview states. Disable report export without
analytics and scenario execution without holdings. A monotonically increasing
request ID prevents an older refresh from replacing a newer selection, including
late errors/finalizers. A third component test covers controlled out-of-order
completion without timing-dependent sleeps. Corrected demo wording to describe
an editable shared demonstration rather than a read-only workspace.

**Manual verification:** In the isolated browser, the previously created empty
portfolio displayed its own selection and empty overview, with export disabled.
Opened Holdings and uploaded `.tmp/rework-browser-holdings.csv` containing one
fictional CAD holding. The UI reported one atomic import, showed only `REWORK`
(quantity 2, price $12, value $24), enabled export, and displayed no global error.
The user's runtime database and tracked screenshots remained untouched. Stopped
both owned demo servers before running the production build to avoid concurrent
writes to `.next`.

**Verification attempt:** All four frontend tests passed (three dashboard
regressions and existing entry test), but standalone TypeScript checking rejected
an unsupported `exact` option in `getByRole`. String `name` matching already
provides the intended exact match. Removed the extra option before committing;
this was a test-authoring mistake within the increment, not an application bug.
Rerun frontend tests and type checking. The Next.js 16.2.11 production build
passed with compilation in 4.8 seconds and built-in TypeScript checking in
4.2 seconds. The final `npm test && npx tsc --noEmit` rerun passed all four
frontend tests in 3.68 seconds and standalone type checking. Browser report download
remains a separate open investigation; enabled export alone does not prove a
saved PDF.

**Lesson and interview explanation:** An expected missing-history API response
must not make a new portfolio unusable or relabel stale data as current. Separate
required holdings from optional analytics, expose deliberate empty states, and
protect UI state from superseded responses. The tradeoff is two-stage loading
rather than one all-or-nothing request group; do not invent zero performance.

**References:** `apps/web/app/components/Dashboard.tsx`, `Dashboard.test.tsx`,
`apps/web/app/page.tsx`, `docs/security.md`. Commit: `549fffa`
(`fix: keep empty portfolios usable for CSV import`). `docs/interview-guide.md` provides concise study outlines and marks open
investigations without inventing personal learning or production evidence.

## CSV validation: reject non-finite values and malformed rows

**Problem:** Imports promise atomic validation errors. Numeric spellings accepted
by Python's `float` parser are not necessarily usable finite values, and malformed
row lengths were not checked before normalization.

**Reproduction:** `tests/test_imports.py` submits a valid first row and an invalid
second row in a new portfolio. Across each numeric field, try `NaN`, `inf`,
`-inf`, and `1e309`. Also try a second row with one extra field or a truncated
optional field. The expected result is HTTP 422, row/field diagnostics, and
unchanged counts of holdings, securities, prices, import records, and audit events.

**Investigation and evidence:** Before changing `imports.py`, run:

```text
cd /d "G:\C++ PROJECTS\AssetLens\apps\api"
.venv\Scripts\python.exe -m pytest tests/test_imports.py --no-cov --tb=short
```

Result: 11 failures, 3 passes in 7.27 seconds. Negative infinity was already
rejected. Positive infinity and overflow returned HTTP 200; NaN reached SQLite
and triggered NOT NULL integrity errors. An extra field raised
`AttributeError: 'list' object has no attribute 'strip'`; a truncated optional
price row was accepted with HTTP 200. These observations establish distinct
validation gaps, not a concurrency or production incident.

**Root cause:** `value <= 0` does not reject NaN and accepts positive infinity;
`float('1e309')` overflows to infinity. `csv.DictReader` stores excess fields under
a `None` key as a list, and missing fields as `None` values. The normalization
code assumed every value was a string and treated missing optional fields as
intentional blanks.

**Fix:** Require `math.isfinite(value)` as well as positivity. Check row shape
before normalization, accumulate a row-level `file` error, and continue validating
the remainder of the file. The existing parse-before-write boundary rejects the
entire import if any row has errors. Keep explicitly blank optional prices valid;
a positive-control test checks their average-cost fallback.

**Tradeoffs:** Strict row width rejects truncated optional fields even when a
default could be inferred. This makes accidental column loss visible; users can
express a default with an explicit blank field. No new parser, dependency, or
schema migration is required. Existing float-based monetary arithmetic remains
unchanged; arbitrary large finite values and concurrent-import guarantees are
outside this increment and are not claimed solved.

**Verification:** With Python 3.12.10 in the project virtualenv,
`python -m ruff check app tests scripts` passed and `python -m pytest` passed
all 43 tests in 5.01 seconds, including the 15 new regression/compatibility
cases. Statement coverage was 84% over 936 statements. The dependency deprecation
warning remains. The pre-fix regression run is intentionally unsuccessful evidence.
Frontend baseline checks passed earlier; no frontend code changed in this increment.
PostgreSQL, containers, external providers, and production deployment were not
verified by this local SQLite test run.

**Diff review:** Reviewed the source, tests, and documentation changes; whitespace
checks passed. Generated local execution/delegate artifacts appeared as untracked
files. Added targeted `.pi/tasks/` and `.pi/delegate/` ignore rules; these artifacts,
runtime databases, and credentials are excluded from staging.

**Lesson:** Validate domain requirements, not just parseability. Boundary tests
should include special numeric values and parser output shapes, and assert that
all affected tables remain unchanged on rejection.

**References:** `apps/api/app/imports.py`, `apps/api/tests/test_imports.py`,
`docs/api.md`. Commit: `cef57d0` (`fix: reject non-finite and malformed CSV input`).

**Provenance:** Existing implementation defects reproduced during ordinary rework,
not intentionally introduced debugging exercises. Fixed within an uncommitted
increment; the regression tests and correction will be committed together.

**Interview explanation:** The normal import test passed, but boundary cases
revealed non-finite values and malformed rows bypassing validation. Reproductions
isolated Python float semantics and DictReader's sentinel values. A small
pre-write validation change rejects these inputs with useful errors, while table
count assertions test atomicity and a positive case preserves optional defaults.

## Scenario lifecycle: controlled interleaving investigation

**Expected behavior and acceptance:** Only a pending run may be claimed by an
executor. Repeated delivery must not recalculate completed/failed/cancelled or
already-running runs. Cancellation committed during calculation must survive
both successful and failing calculation. Cancellation must not overwrite a run
that completed after the cancellation handler's initial lookup. A successful run
must have one completion audit event; ordinary calculation errors remain failed
with a diagnostic and completion timestamp.

**Investigation plan:** `apps/api/tests/test_scenarios.py` uses separate database
sessions and monkeypatched calculation/lookup boundaries to establish specific
interleavings, not elapsed-time sleeps. These are local controlled tests, not
production incident reports or proof of all multi-worker behavior. Run the nine
cases against the unchanged executor before changing its state transitions.

```text
cd /d "G:\C++ PROJECTS\AssetLens\apps\api"
.venv\Scripts\python.exe -m pytest tests/test_scenarios.py --no-cov --tb=short
```

**Source hypothesis:** `execute_scenario` checks only pre-execution cancellation,
then unconditionally writes running and terminal states through a cached ORM
object. The cancellation route also checks status before a separate write. A
read/check/write sequence can accept a stale state even with a transaction.
**Reproduction results:** The nine unchanged-code cases produced seven failures
and two passes in 1.19 seconds. Running/failed runs became completed; completed
runs were recalculated; cancellation during calculation became completed or
failed; repeated delivery changed result/timestamp; stale cancellation returned
HTTP 200 after another session completed the run. Cancellation before execution
and ordinary calculation failure already worked.

**Root cause:** Status was checked separately from mutation, and the worker
retained an ORM object across another session's cancellation. A local object is
not evidence that the corresponding database status is still eligible.

**Fix:** Claim pending runs with a conditional SQL update and inspect affected
row count. Finalize only still-running runs; write completion audit in the same
transaction only when completion wins. Roll back a failed calculation session
before recording failed state. Cancel only an eligible database state, returning
409 when a concurrent terminal transition won. Cancellation records a timestamp.
Added two further cases for duplicate delivery during calculation and successful
pending cancellation, for eleven lifecycle cases total.

**Verification:** API lint passed and all 54 tests passed in 5.32 seconds,
including eleven lifecycle cases. Statement coverage was 85% over 940 statements;
the existing TestClient dependency warning remains. Commands used the project
Python 3.12.10 virtualenv. No schema change was required; isolated SQLite migration
checks also passed. PostgreSQL/Celery multi-worker execution was not verified.
Existing frontend state wording still needs its own follow-up checks, especially
terminal states, polling exhaustion, and late scenario results after portfolio
switching.

**Tradeoffs:** Conditional database transitions guard the lifecycle without a
new queue, schema, or lock service. Cancellation discards a calculated result;
it does not interrupt computation. A worker that dies after claiming a run may
remain running without a lease/recovery policy. Automatic safe retry is not
claimed. Cancellation versus completion is decided by the winning database
transition, not wall-clock assumptions.

**Lesson:** Lifecycle invariants need to live in database predicates, not just
prior status reads. Controlled interleavings expose races without flaky sleeps.

**References:** `apps/api/app/scenarios.py`, `main.py`,
`apps/api/tests/test_scenarios.py`, `docs/api.md`, `docs/architecture.md`.
Commit: `75f1890` (`fix: preserve terminal scenario state during concurrent execution`).

**Interview explanation:** Tests demonstrated that stale worker/handler objects
could overwrite terminal state. Conditional updates made claim, completion, and
cancellation eligibility atomic; completion auditing follows the same winning
transaction. This improves the tested ordering guarantees but is not durable
worker recovery or a production load-test claim.

**Provenance:** Investigating existing implementation behavior during ordinary
rework. Test synchronization simulates relevant ordering; no intentional learning
branch defect has been introduced.

## Scenario display: terminal states and bounded polling

**Problem hypothesis:** The current UI displays a spinner and “The job is running”
for any run that is not completed, including failed/cancelled runs. It stops
polling after fifteen attempts without exposing that polling stopped.

**Acceptance criteria:** Failed/cancelled runs must show a terminal heading with
no running spinner; a failure includes its error. A still-pending/running run
after the polling budget must offer an explicit paused state and a status-refresh
action that does not create another run. Superseded scenario responses must not
appear after portfolio selection changes. Remove claims of automatic safe retry.

**Reproduction:** Added component tests before editing the UI. They return
controlled failed/cancelled job responses and use fake timers for a job that
remains pending beyond the polling budget. Run
`npm test -- app/components/Dashboard.test.tsx`. Before the UI change, three
new scenario cases failed and the three loading cases passed in 6.11 seconds:
terminal headings were missing and a permanently pending run kept displaying
“safe retry semantics” instead of announcing polling exhaustion.

**Root cause:** Rendering treated every non-completed status as active, while
polling returned silently after its finite loop. There was no distinction between
the server run's status and whether the browser was still observing it.

**Fix:** Separate polling activity/paused state from the persisted job status.
Share a bounded polling helper between new-run and status-refresh actions.
Render failed/cancelled states without spinners; expose `Polling paused` and
`Refresh status` without another POST. Disable duplicate submission while
observing a run. Invalidate scenario request IDs on selection change/unmount and
ignore late responses. A fourth new test uses a deferred response to verify
portfolio-scoped results; this is additional coverage, not a pre-fix run claim.

**Verification:** `npm test` passed all eight frontend tests in 3.49 seconds;
`npx tsc --noEmit` passed; the Next.js production build passed (3.0-second
compilation, 4.3-second built-in type check). Tests cover four scenario cases and
three portfolio-loading cases plus the existing entry test. The failed baseline
remains recorded evidence.

**Tradeoffs:** Polling remains a small fifteen-attempt, 300 ms local-demo budget;
pausing observation does not cancel the server job or declare it failed. Manual
refresh starts another bounded observation period for the same run. This avoids
unbounded background polling without adding WebSockets or durable scheduling.

**Lesson:** Job lifecycle and client observation lifecycle are different states.
Use explicit terminal/error/paused presentation, and guard late work independently
of the user's current selection.

**References:** `apps/web/app/components/Dashboard.tsx` and `Dashboard.test.tsx`.
Commit: `b6fe87b` (`fix: distinguish scenario terminal state from polling activity`).

**Interview explanation:** The backend could report a terminal job while the UI
still showed a running spinner. Reproductions separated server state from polling
activity; a reusable observer and explicit state rendering corrected that mismatch.
A request identity prevents an old portfolio's scenario from appearing in the
new workspace. Eight frontend tests, types, and production build passed.

**Provenance:** Investigation of existing UI behavior during ordinary development,
not an intentionally introduced learning-branch defect. Controlled API responses
are test fixtures, not reports of real users or production events.

## Browser workflow isolation and report verification

**Hurdle:** The existing Playwright configuration could attach to already-running
servers, use the user's default runtime database, and overwrite tracked screenshots.
Its Python command also did not prefer the installed project virtualenv. Earlier
native PDF download was cancelled, so an independent saved-file check is needed;
do not assume immediate object-URL revocation is the root cause without evidence.

**Acceptance:** Browser tests own dedicated API/web ports and a temporary SQLite
database, use deterministic/local services, save artifacts in ignored test output,
and fail rather than reuse an unrelated server. Exercise seeded analytics/scenario
and creation → empty holdings → CSV import → real saved PDF with signature/size
checks. Preserve existing tracked screenshots and the runtime database.

**Approach:** Detect the platform's project virtualenv interpreter (or use
`API_PYTHON`/system Python for CI), create the ignored `.tmp` directory, and assign
a per-process test database. Replace screenshot destinations with test output
paths. Add the creation/import/download browser journey. Run `npm run test:e2e`
from the repository root. Both Chromium journeys passed in 25.8 seconds. The
new journey downloaded and saved a PDF, checked `%PDF` bytes and size >2 KB,
and exercised creation, empty holdings, import, and export. No application PDF
fix was necessary: the earlier native capture cancellation alone did not prove
a defect. Its cause was not established, so do not invent a root cause.

**Tradeoffs:** Dedicated ports fail if occupied rather than borrowing a server
with unknown configuration. Each run leaves an ignored test database that can be
removed when no tests are active. Native browser capture and Playwright download
results may differ; report the actual saved-file result rather than infer a
production defect from a tool failure.

**References:** `playwright.config.ts`, `tests/e2e/demo.spec.ts`.

**Provenance:** Existing test-isolation shortcomings and an observed local download
capture failure, not intentionally introduced application defects. Successful
saved-file verification is from the independent isolated Chromium test.

**Lesson and interview explanation:** Test tooling is part of reproducibility.
Owning the server/database/artifact lifecycle prevents a successful run from
silently depending on someone else's local state or modifying repository images.
An unsuccessful capture is evidence to investigate, not permission to invent a
bug or performance claim.

## Intentional debugging exercises: verified baseline and provenance

**Baseline:** `b990b6b` on `shaoyu/rework`, with 54 API tests, eight frontend tests,
TypeScript/build checks, isolated SQLite migration checks, and two Chromium
journeys passing. Learner-facing instructions were written in
`docs/debugging-exercises.md` before introducing defects or publishing solutions.

**Exercise preparation:** Added a full drawdown-path regression. Against the
correct baseline, `pytest tests/test_debugging_regressions.py --no-cov --tb=short`
passed (one test, 0.50 seconds). Existing drawdown behavior on main and rework is
already correct; a later exercise correction must not be described as fixing a
naturally discovered baseline defect.

**Policy:** Introduce two plausible mistakes only on `shaoyu/learning`, reproduce
failures, preserve each faulty commit, then correct each in a separate normal fix
commit. Keep symptoms/reproduction apart from diagnoses. Continue correction and
integration independently of learner progress unless a pause is requested. Merge
only the corrected state with a merge commit; main remains untouched.

**Investigation limitation:** Implementation-side diagnostic notes are not
learner personal investigation. Hypothetical reports/consequences are educational,
not production usage or incidents. Fault/fix IDs and actual results will be added
after each checkpoint.

### Exercise 1 checkpoint — implementation-side spoilers

**Problem/reproduction:** Full drawdown-path values diverged after an earlier high.
Focused command: `pytest tests/test_debugging_regressions.py tests/test_analytics.py
--no-cov --tb=short`; run on `shaoyu/learning` with the project virtualenv.

**Investigation/evidence:** Correct baseline passed the new test. After the
intentional one-line iteration change, lint passed but tests had two failures and
six passes in 1.11 seconds. Four of seven path points differed; the existing
minimum test returned -0.12 rather than -0.2. Full-path assertions identify the
first divergence instead of testing only an aggregate. No fictional unsuccessful
investigation is attributed to the learner.

**Root cause:** The intentional change compares each observation to the first
value rather than preserving the maximum from previous iterations. Partial
recoveries erase relevant peak history.

**Fix:** Restored the running maximum for a separate fix commit after preserving
the verified faulty checkpoint. This restores baseline behavior already correct
on main and rework; it does not repair a defect previously affecting those branches.

**Tradeoffs/lesson:** No meaningful architecture tradeoff; a streaming accumulator
is linear time with constant extra state, while rescanning prefixes is quadratic.
Test complete intermediate output, not just final aggregates.

**Verification/provenance:** Expected failures are verified intentional exercise
evidence, not a naturally discovered bug or production incident. Faulty checkpoint
`4d8e3e2` is preserved. Restored the correct accumulator in the working tree;
API lint passed and all 55 tests passed in 4.57 seconds with 85% statement
coverage before the separate fix commit. See `docs/debugging-solutions.md` for separate
progressive hints and explanation, and `docs/debugging-exercises.md` for symptoms.
Separate correction commit: `2778165` (`fix: preserve running peaks when calculating drawdown`).

**Interview explanation:** State that the defect was intentionally introduced;
explain how hand-calculated points reveal lost iteration state and how the
restored accumulator plus full-path regression prevents it.

### Exercise 2 preparation

Added `test_cancelled_run_keeps_timestamp_and_discards_late_result`, asserting
that cancellation committed during calculation retains its timestamp, status,
empty result/error, and absence of completion audit. With the guarded executor
still correct, `pytest tests/test_debugging_regressions.py -k cancelled --no-cov
--tb=short` passed (one test, one deselected, 0.33 seconds). This baseline result
precedes the intentional lifecycle mistake. It restores/tests existing correct
rework behavior, not a newly discovered main-branch defect.

### Exercise 2 checkpoint — implementation-side spoilers

**Problem/reproduction:** After cancellation, a late worker outcome can change
terminal status/timestamp and publish a result. Run
`pytest tests/test_debugging_regressions.py tests/test_scenarios.py --no-cov --tb=short`
on `shaoyu/learning`. Lint passed; tests produced three expected failures and ten
passes in 1.64 seconds. Committed cancellation became completed on late success
or failed on late error. The new timestamp test fails first at terminal status,
so do not claim it reached and observed later assertions on the faulty code.

**Intentional root cause:** Removed final-write status eligibility from the
already-correct rework helper. An unconditional ID-based update can overwrite
committed cancellation despite earlier reads. This is a plausible persistence
refactor mistake, not an arbitrary crash or unrelated broken code.

**Investigation plan:** Inspect separate-session stored state at the controlled
calculation boundary and assert status, timestamp, result/error, and completion
audit. The new timestamp regression passed before the fault was introduced.

**Fix/tradeoffs:** Preserved faulty checkpoint `8255540`, then restored the terminal
predicate for a separate fix commit. API lint and all 56 tests passed in 5.09
seconds with 85% statement coverage; SQLite migration upgrade/drift checks passed.
All eight frontend tests passed in 5.03 seconds; standalone types and production
build passed (2.7-second compilation, 4.6-second built-in type check); both isolated
Chromium journeys passed in 18.7 seconds, including the saved PDF. No intentional
failure remains in these checks before integration. Fresh reads without guarded writes still
race; no new lock, queue, schema, or lease is needed for this invariant. Cancellation
cannot interrupt calculation, and worker-crash recovery remains unimplemented.

**Provenance:** Intentionally introduced only on the learning branch after a
verified working rework baseline. The eventual fix restores that baseline. It
must not be represented as a new naturally discovered main incident; ordinary
preexisting lifecycle findings are documented separately.

**References/lesson:** `scenarios._finish_scenario`,
`tests/test_debugging_regressions.py`, `tests/test_scenarios.py`, separate learner
instructions and spoiler material. Enforce state eligibility at write time and
inspect the winning transition before publishing an audit.

**Interview explanation:** Describe this as an intentional exercise showing a
late result after a terminal transition. Explain how a controlled interleaving
and persisted-state assertions distinguish object state from write eligibility.
No personal study, production consequence, or unperformed verification is claimed.

## Corrected learning integration and final verification

**Review:** Complete `shaoyu/rework..shaoyu/learning` diff was inspected before
merging: only two regression cases and their documentation/journal remained.
`git diff --exit-code shaoyu/rework..shaoyu/learning -- apps/api/app apps/web`
passed, proving no intentional runtime changes remained relative to the verified
rework baseline. Working tree was clean.

**Integration:** Merge `b23ab90` uses `--no-ff`, preserving first fault/fix
`4d8e3e2` / `2778165` and second fault/fix `8255540` / `cacadc4`. The exercise
corrections restore existing correct rework behavior; net contributions are
regression tests, learner instructions, separate spoilers, and accurate evidence.
No squashing, history rewrite, push, or merge into main occurred.

**Post-merge verification:** On `shaoyu/rework` at `b23ab90`, API lint passed
and all 56 API tests passed in 4.68 seconds with 85% statement coverage over 940
statements. Isolated Alembic upgrade/check passed with no schema drift. All eight
frontend tests passed in 4.40 seconds, standalone TypeScript checking passed,
and production build passed (2.4-second compilation, 4.0-second built-in type
check). Both isolated Chromium workflows passed in 27.5 seconds, including the
saved-PDF check. These are actual post-merge results, not inferred pre-merge passes.

**Final source review:** Inspected the complete source/configuration delta and
changed-path list against main; `git diff --check main..HEAD` passed. No runtime
environment, database, generated build output, or tracked screenshot changes are
included. Relevant new helpers/imports/state have runtime or test references;
source lint and frontend types passed. No commented-out implementation was added.
The common terminal-write and polling behavior is owned by named helpers.
Main remains `e13a1d83d8080e6b70395850f7bb7ed7d10ce469`; no push occurred.
Ignored test databases/artifacts remain local evidence, not commit contents.
A temporary Python 3.12 standard-library checker resolved local Markdown links
from tracked `.md` files, checked changed paths for environment/generated artifacts,
and looked for private-key blocks or long `sk-` token patterns. All checks passed.
This is targeted hygiene, not a comprehensive security scan; the temporary checker
is removed after use. Final documentation whitespace/staged-diff checks are run
before its commit.

**Remaining scope limits:** Local SQLite/Chromium checks do not verify PostgreSQL,
Celery/Redis workers, containers, external providers, deployed security, or
production behavior. Concurrent import guarantees, shared imported-price ownership,
FX conversion/sparse-history policy, and crashed-worker recovery remain documented
limitations/future decisions, not claims of production readiness. The original
TestClient dependency warning was still present at this checkpoint; the follow-up
below records its maintenance fix. Learner personal investigation is intentionally
unfilled until study is actually performed.

## TestClient dependency maintenance

**Problem/provenance:** A real dependency-maintenance warning remained in the
verified API tests; this is not an intentional exercise defect. FastAPI 0.140.0 /
Starlette 1.3.1 reported that its TestClient's `httpx` fallback was deprecated.
All 56 tests previously passed, but the development dependency declaration had
not adopted the preferred client.

**Investigation:** `python -m pip show fastapi starlette httpx httpx2` showed
`httpx` 0.28.1 and no `httpx2`. Reading installed `starlette/testclient.py` showed
that it first imports `httpx2` and warns when falling back to `httpx`. The custom
warning inherits `UserWarning`, so a generic `DeprecationWarning`-only policy
would not catch this case. Package-index inspection found stable `httpx2` 2.x
releases, including 2.13.1.

**Reproduction/regression:** Added a message-specific error filter in
`apps/api/pyproject.toml`, then ran `.venv\Scripts\python.exe -m pytest` before
installing the new client. Pytest exited 4 while importing `tests/conftest.py`,
with the exact Starlette fallback warning as its error. This is an observed
failure, not a simulation, and the persistent filter prevents its silent return.

**Fix/decision:** Declare `httpx2>=2,<3` under the API development extras, where
TestClient belongs. Keep runtime `httpx>=0.28,<1`, which the OpenAI SDK also uses;
do not replace production transport or unnecessarily pin/downgrade the framework.
Do not ignore warnings. The narrow error filter avoids making unrelated third-party
warnings a permanent project policy; an additional strict verification run checks
all warnings for this change.

**Verification:** From `apps/api` on Windows/Python 3.12.10:

```text
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -W error -c "from fastapi.testclient import TestClient; import starlette.testclient as tc; assert tc.httpx.__name__ == 'httpx2'"
.venv\Scripts\python.exe -m ruff check app tests scripts
.venv\Scripts\python.exe -m pytest -W error
```

Installed `httpx2` 2.13.1, `httpcore2` 2.13.1, and `truststore` 0.10.4; existing
runtime packages were already satisfied. `pip check` found no broken requirements.
The strict import check confirmed Starlette selects `httpx2` without a warning.
Ruff passed. All 56 API tests passed with `-W error` in 5.81 seconds and 85%
statement coverage (940 statements), with no warning summary. From the repository
root, `npm run test:e2e` passed both isolated Chromium journeys in 38.9 seconds,
including saved PDF verification. Frontend source and dependency manifests are
unchanged; their tests, type checking, and production build passed in the preceding
verification of `3f62ffb`. The final working diff contains only the API manifest
and this journal; whitespace checks passed and no environment/generated artifacts
are included. Runtime environment files are not edited.

**Tradeoff/lesson:** Both client distributions exist in development because
TestClient and the runtime SDK use different packages. Keep their ownership clear
and bound the added major version. A warning can identify incomplete dependency
metadata even when functional tests pass; reproduce it as a failure before fixing
the dependency, rather than hiding the signal. This does not verify live OpenAI,
PostgreSQL, Celery, containers, or production behavior.

## Authorized main integration

**Decision/scope:** The user requested the verified rework on `main`, with both
branches and their commits retained. Merge `a7e9898` integrates `shaoyu/rework`
using `--no-ff`; its parents are original main `e13a1d8` and rework `079f6bc`.
No branch was deleted, no history rewritten, and nothing pushed. After the verified
finalization commit, fast-forward `shaoyu/rework` to main so both expose the same
finished state; keep `shaoyu/learning` and all historical checkpoints.

**Corrected-state evidence:** `git diff --exit-code shaoyu/rework HEAD` passed
immediately after the merge, so the merged tree exactly matches the verified
rework state. Both exercise fault/fix pairs remain ancestors through `b23ab90`.
The faults are preserved only as historical checkpoints, not in the final source.
Their fixes restore already-correct baseline behavior; the regression tests and
learning documentation are the genuine net additions.

**Documentation review:** Inspected tracked Markdown matches and searched tracked
files for development-attribution labels. No such labels were found; grep's exit
1 with no output means no matches, not an application failure. Kept functional
Copilot/provider descriptions and repository wording instructions. No false
statements about authorship were added, and no wording changes were necessary.

**Post-merge verification:** On `main` at `a7e9898`, dependency consistency and
API lint passed. All 56 API tests passed with warnings as errors in 7.18 seconds,
with 85% coverage over 940 statements and no warnings. Fresh isolated SQLite
migration upgrade and schema-drift checks passed. Eight frontend tests passed in
10.83 seconds; standalone types and production build passed (4.8-second
compilation and 6.3-second built-in type check). Commands use the API virtualenv
and frontend workflow documented above; migration verification sets
`DATABASE_URL=sqlite:///./.tmp/main-verification-%RANDOM%.db` from `apps/api`.

**Browser failure/investigation:** The first post-merge browser run failed both
journeys at the 30-second overall test deadline while clicking the entry button.
The import journey's call log resolved the correct visible, enabled, stable
button and reached dispatch; failure snapshots still showed the login screen.
At that point, there was no basis to claim an application root cause or successful
browser verification. The merged tree matched the previously passing rework tree.
Reviewed the entry state/effect and local stylesheet; no external font import
explains the observed stall. The rendered login follows the initial client effect,
so the snapshot alone does not support a missing-hydration diagnosis.

**Diagnostic outcomes:** From the root, `npx playwright test --workers=1 --trace on --output=.tmp/main-serial-browser`
with `DEBUG=pw:webserver` passed both
journeys in 1.0 minute (20.4 and 12.4 seconds per test). Then
`npx playwright test --trace on --output=.tmp/main-parallel-browser` passed both using the default two
workers in 1.5 minutes (14.0 and 20.2 seconds per test). Application code, retries,
and the 30-second test deadline were unchanged. The initial stall did not
reproduce; resource contention remains a hypothesis, not an established cause.
No permanent application or timing fix is claimed. Kept original failure contexts
and diagnostic traces in separate ignored directories.

**Diagnostics improvement:** Original `trace: "on-first-retry"` provided no trace
for an initial failure because retries are disabled. Change it to
`"retain-on-failure"`, preserving the first failure's trace without hiding failures,
adding retries, or widening timeouts. A temporary, explicitly synthetic failing
test inherits this policy with application servers disabled to check readable
first-failure trace retention. Its output showed the intended assertion mismatch
and one first-failure trace attachment, not an application failure. Separately
validated ZIP integrity and trace entries with Python; confirmed the original
failure directory had two error contexts and no trace. Removed the temporary
probe source/config, retaining ignored evidence only. Finally,
`npm run test:e2e -- --output=.tmp/main-final-browser` passed both real journeys
using two workers and the new default policy in 20.1 seconds (6.3 and 6.4 seconds
per test), including saved PDF verification. This is actual post-change verification,
not an inference from an attachment message or serial-only success. Final changed
files are this journal and one trace-policy setting; no runtime source, environment,
database, or tracked screenshot changes belong to this follow-up. Existing
production-scope limitations and unfilled personal study notes remain unchanged.

## CI production dependency audit

**Problem/provenance:** Actual GitHub run `37699322107` for `effb8ab` failed its
web job at `npm audit --omit=dev`. API installation/lint/tests/migrations passed;
web tests/build and the dependent container/browser jobs were skipped, not failed
application tests. This is a real dependency-maintenance issue, not an exercise.
Previous main also had a failed run; its exact cause was not inferred without logs.

**Reproduction/evidence:** From `apps/web` on the local Node 24.19.0 environment,
`npm audit --omit=dev` exited 1 with the same five vulnerable production package
entries: Next.js (critical), Nano ID, PostCSS, sharp, and source-map-js (high).
The Next.js advisories include Windows-hosted, AVIF optimization, and ImageResponse
remote-code-execution risks. No exploitation or production exposure is claimed.

**Root cause/decision:** The pinned Next.js 16.2.11 and locked transitive versions
were outdated relative to current advisories. Passing functional tests did not
cover CI's separate dependency audit; earlier local verification omitted that gate.
Do not disable the audit, reduce its severity threshold, or claim that unused image
features make these advisories irrelevant. Inspect the patched release's engine,
peer, and transitive requirements before a same-major upgrade; explicitly update
the pin/lockfile instead of using a blanket `npm audit fix --force`.

**Compatibility/fix:** Registry metadata for Next.js 16.4.0 requires
Node >=20.9.0 and accepts React/React DOM ^19.0.0, so the existing Node 24 and React
19.2.0 meet its declared requirements. Current tree had Next.js 16.2.11,
PostCSS 8.4.31 under Next, sharp 0.34.5, Nano ID 3.3.16, and source-map-js 1.2.1.
`npm install --save-exact next@16.4.0` followed by `npm update nanoid source-map-js`
resolved Next.js 16.4.0, PostCSS 8.5.23, sharp 0.35.5, Nano ID 3.3.20, and
source-map-js 1.2.2. Production audit now reports zero vulnerabilities. Kept React
versions and CI audit enforcement; no blanket force-fix was used. Installation
also reported three development-only advisories (one moderate, two critical).
Full `npm audit` reproduced those with exit 1: vulnerable Vitest/@vitest/mocker
and Tinypool. These concern mock path traversal/file reads and worker-option
prototype-pollution RCE. Inspect supported patched test-tool releases rather than
claiming the entire tree is clean or blindly applying a major-version force fix.

**Test-tool follow-up:** Inspected available releases and selected the earliest
published unaffected 4.x release, Vitest 4.1.11, rather than npm's suggested 5.0.3
jump. Its declared Node and Vite ranges accept the existing Node 24/Vite 7.3.6
setup. `npm install --save-dev --save-exact vitest@4.1.11` resolved the patched
mocker and removed Tinypool; Vite 7.3.6 and React plugin 5.2.0 remain unchanged.
Both full `npm audit` and `npm audit --omit=dev` report zero vulnerabilities.

**Prevention/tradeoff:** Strengthen the existing CI gate from production-only
`npm audit --omit=dev` to full `npm audit`, matching the added README local check.
This catches development-tool advisories as well, at the cost of broader dependency
maintenance. No checks were disabled, severity thresholds reduced, or tests skipped.
A same-major Next.js minor update and a controlled test-tool major update require
actual compatibility checks, not just clean audit output. npm reports an existing
pending esbuild install-script approval; no global script-approval policy is changed.

**Local verification:** `npm ci` installed 166 packages from the new lockfile;
full and production audits both found zero vulnerabilities. Eight frontend tests
passed under Vitest 4.1.11 in 18.03 seconds with unchanged test source; standalone
TypeScript checking passed. Next.js 16.4.0 build passed (8.6-second compilation,
4.3-second built-in type check). `npm run test:e2e -- --output=.tmp/security-update-browser`
passed both Chromium journeys in 44.8 seconds, including saved PDF verification.
The clean install still reports the existing whatwg-encoding deprecation and
pending esbuild script-approval notices; these are not audit findings and no
warnings or install-script policies were suppressed.

**Framework-generated follow-up:** Next.js added a root-parameter type reference
to the existing tracked type bootstrap; retain that framework-owned declaration.
It also generated an untracked nested instruction file containing only its managed
block during startup. Verified the generator, configuration type/schema, and bundled
configuration guide. The generated block recommends committing itself, which
conflicts with the user's preference for curated repository documentation; it is
not a user-authored change and does not override the root workflow. Set the supported
top-level `agentRules: false` option, which removes only the managed nested block
and stops recreating it. Root repository instructions remain authoritative.

**Final configuration verification:** Full audit still found zero vulnerabilities;
standalone types and production build passed. Both real Chromium journeys passed
in 17.6 seconds (4.2 and 5.1 seconds per test), including the saved PDF check.
An explicit filesystem assertion confirmed the generated nested file was removed
and not recreated; `git diff --exit-code -- AGENTS.md` proved root instructions
unchanged. These are post-configuration results. The lockfile review confirmed
expected pins, unchanged Vite/plugin versions, no Tinypool, required Linux/glibc
and Alpine/musl binary entries, and only public npm registry resolution URLs.
Changed files are dependency/configuration/type bootstrap, CI gate, README, and
this journal; no runtime environment, database, screenshots, or unrelated source
changes are included. Staged diff/whitespace checks precede the focused commit.

**Remote verification pending:** All four GitHub jobs must complete successfully
after publication. Do not report CI green based solely on the local checks.

## Learner investigation notes

Not completed yet. Record personal reproductions, hypotheses, evidence, changes,
verification, and lessons here after carrying out the exercises. Interview
statements about personal investigation must use these completed notes.
