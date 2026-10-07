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
intentional defect was introduced. A UI fix and regression checks are pending;
no fix or completed verification is claimed in this entry.

**Tradeoffs and next step:** Handle empty holdings explicitly and keep them
usable for import rather than fabricate performance metrics. Test creation,
portfolio switching, and analytics failures. Do not replace every dashboard
component to repair this data-loading boundary.

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
`docs/api.md`. Planned commit: `fix: reject non-finite and malformed CSV input`;
its hash will be recorded in the next journal update.

**Provenance:** Existing implementation defects reproduced during ordinary rework,
not intentionally introduced debugging exercises. Fixed within an uncommitted
increment; the regression tests and correction will be committed together.

**Interview explanation:** The normal import test passed, but boundary cases
revealed non-finite values and malformed rows bypassing validation. Reproductions
isolated Python float semantics and DictReader's sentinel values. A small
pre-write validation change rejects these inputs with useful errors, while table
count assertions test atomicity and a positive case preserves optional defaults.

## Learner investigation notes

Not completed yet. Record personal reproductions, hypotheses, evidence, changes,
verification, and lessons here after carrying out the exercises. Interview
statements about personal investigation must use these completed notes.
