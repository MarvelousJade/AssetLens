# AssetLens portfolio rework

## Purpose and audience

AssetLens helps a reviewer or someone learning portfolio analytics understand
how a set of holdings contributes to performance, risk, and simplified stress
outcomes. Its seeded dataset makes an end-to-end demonstration possible without
an account, paid market data, or an external model service.

It is worth building as a concrete example of validated ingestion, database
transactions, ownership checks, deterministic calculations, asynchronous work,
and a browser interface. This is a software demonstration, not a trading system
or financial advice service. No production usage or customer impact is claimed.

Suggested motivation to personalize, only if accurate:

> I wanted a small, reproducible application for exploring how portfolio inputs
> become explainable analytics. I chose to focus on data validation, transparent
> calculations, and evidence-based debugging rather than live trading.

## First rework scope

Preserve the seeded reviewer journey: demo entry → holdings and benchmark
analytics → deterministic scenario → downloadable report. Preserve existing
CSV import and deterministic research explanations. Inspect and improve
correctness at these boundaries rather than replace the stack.

Include:

- A freshly verified baseline and explicit records of verification limitations.
- Focused fixes for reproduced workflow defects, with regression tests.
- Accurate claims about demo permissions, analytics assumptions, and job behavior.
- A concise interview guide and comprehensive engineering journal.
- Two or three reproducible debugging exercises after a working baseline, with
  separate learner instructions and solutions, preserved checkpoints, and
  corrected-state integration into `shaoyu/rework`.

Exclude new infrastructure, live market feeds, trading, production authentication,
new research features, and claims of production readiness or measured improvement
without evidence. Do not delete working features or deployment files merely
because they are outside the main demonstration. Changes to optional runtime
paths require reference checks and a concrete reason.

## Architecture decision

Keep Next.js/React → FastAPI → SQLAlchemy/SQLite as the smallest existing local
workflow. Analytics remain service functions, reports use ReportLab, and scenario
execution uses the existing local background runner. PostgreSQL, Celery/Redis,
OpenTelemetry, Kubernetes, and the external model provider are optional paths,
not prerequisites for studying the project.

A rewrite would discard tested behavior without a demonstrated benefit. The
tradeoff is retaining some optional deployment complexity; documentation should
separate the required local path from those extensions.

## Checklist and acceptance criteria

- [x] Read root instructions and inspect Git status and recent history.
- [x] Create `shaoyu/rework` without rewriting existing history.
- [x] Commit the previously staged workflow instructions using the authorized
  existing Git identity (`d1b73ef`).
- [x] Inspect source, current documentation, test contracts, and CI commands.
- [x] Record API lint/tests, frontend tests/type checks/build baseline results.
- [ ] Verify the browser workflow without overwriting tracked screenshots or
  touching the user's runtime database.
- [x] Define and reproduce the first validation increment: 11 failures and 3
  passes before the fix; 43 total API tests pass after the fix.
- [ ] Deliver each behavior with tests, journal evidence, diff review, and a
  focused commit.
- [ ] Prepare the interview guide and isolated debugging exercises.
- [ ] Integrate only corrected learning-branch state using a merge commit;
  rerun checks on the resulting rework branch.

Baseline acceptance: API lint and existing tests pass; frontend tests, TypeScript
checking, and production build pass; the reviewer browser journey works against
an isolated local database. Record each command, environment, and actual result.
Container, PostgreSQL, worker, external provider, or deployment checks that were
not run must be stated explicitly rather than inferred from local success.

Behavioral increment acceptance: reproduce a meaningful defect, observe the new
regression test fail for the expected reason, apply the smallest clear fix,
verify it and affected existing tests, then inspect and commit specific files.

## Initial inspection questions

These are source-inspection concerns, not yet confirmed runtime failures.
A read-only second review also identified a likely broken creation/import
journey: selecting an empty portfolio requires performance analytics to load
successfully, but that API intentionally rejects portfolios with no market
prices. Reproduce it before choosing a UI fix.

Prioritize one small validation increment first: finite positive CSV values and
well-formed rows must be validated before writes. Then repair the empty-portfolio
workflow and scenario lifecycle in separate increments, using reproduced failures
and focused tests. Shared imported prices and unsupported currencies need explicit
scope decisions rather than speculative concurrency/schema changes.

- CSV finiteness and row-shape gaps were reproduced and fixed in the first
  increment, with 15 new regression/compatibility cases.
- Scenario execution writes terminal state after calculation without an apparent
  conditional cancellation check; verify cancellation and repeated delivery.
- The browser describes the demo as read-only despite exposing creation/import
  controls; documentation and permissions must accurately reflect behavior.
- README test counts differ between its historical summary and current-result
  section. Fresh results must be revision-specific, not silently assumed current.

## Branch and delivery policy

Work on `shaoyu/rework`. Keep intentional defects on a separate learning branch
only after baseline verification. Do not reveal solutions in learner instructions.
Continue implementation independently of study progress unless a pause is
requested. Do not push, rewrite history, or merge into `main` without authorization.
