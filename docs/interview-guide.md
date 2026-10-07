# AssetLens interview guide

## Project introduction

**One sentence:** AssetLens turns a seeded portfolio into explainable performance,
risk, exposure, and simplified stress results through a reproducible web workspace.

**60-second outline:** The problem is understanding the calculations behind a
portfolio summary rather than merely showing a balance. AssetLens uses a React/
Next.js interface, a FastAPI service, and SQLAlchemy storage. A local SQLite
seed makes the demo independent of accounts and paid data feeds. The core journey
is holdings → benchmark analytics → scenario → research report. The strongest
freshly verified correctness example is atomic CSV rejection: malformed rows and
non-finite numbers return validation errors without changing five affected tables.
At commit `cef57d0`, all 43 API tests passed with 84% statement coverage. These
are local test results, not production impact or performance improvements.

**Three-minute walkthrough:**

1. Explain the eight-holding seeded dataset and educational scope (30 seconds).
2. Trace a holdings request through authentication, ownership filtering, prices,
   quantity-times-price calculation, and the rendered dashboard (60 seconds).
3. Run Technology drawdown and explain explicit shocks and exclusions (45 seconds).
4. Explain CSV parse-before-write validation and the regression evidence (45 seconds).

## Purpose and motivation

The project helps a reviewer or learner explore how inputs become financial
metrics with formulas, dates, and assumptions. It is useful because the same
small workflow crosses UI state, validation, authorization, storage, calculation,
and asynchronous execution boundaries.

Personalize only if true:

> I wanted a reproducible way to understand the engineering behind portfolio
> analytics. I focused on transparent calculations and boundary correctness rather
> than live trading or adding features I could not explain.

Personal investigation and learning claims must come from completed learner notes
in [engineering-journal.md](engineering-journal.md), not from this outline.

## Architecture and stack

```text
Browser / React
    │ same-origin /api requests through Next.js
    ▼
FastAPI: authentication → owned resource lookup → service function
    │                         │
    ▼                         ├─ deterministic analytics / scenarios
SQLAlchemy + SQLite           └─ ReportLab report
(local demo)
```

Optional paths: PostgreSQL for deployment, Celery/Redis for workers,
OpenTelemetry for tracing, and an external research model. None is needed to
understand the local seeded workflow. Do not claim those paths were freshly
verified by the SQLite tests.

### Trace one operation

`GET /api/portfolios/{id}/holdings` → Next.js rewrite → FastAPI `get_holdings`
→ `require_demo_user` + `get_db` dependencies → `holdings_snapshot`
→ owner-filtered portfolio and holding queries → latest available prices
→ quantity × price, cost basis, weights → JSON → Dashboard holdings table.

Failure cases include missing authentication, wrong owner/resource, unavailable
storage, invalid imported values, and UI requests resolving out of order.

### Component contracts and decisions

| Component | Inputs → outputs | Dependencies / likely failures | Why / alternative |
| --- | --- | --- | --- |
| Next.js/React | API data and user actions → workspace | API availability and asynchronous state | Preserve existing working UI; a simpler static UI would offer less workflow coverage. |
| FastAPI | requests + authenticated owner → JSON/PDF | validation, authorization, database errors | Typed request models and useful API docs; another small HTTP framework could work. |
| SQLAlchemy | owned queries and validated writes → persisted records | transaction or constraint failures | One persistence boundary across SQLite/PostgreSQL; direct SQL is simpler for a very small schema. |
| Analytics | holdings and dated observations → metrics | sparse history, unsupported currency assumptions | Deterministic service functions are testable; live feeds would add data-quality complexity. |
| Scenario runner | stored run + shocks → result/status | cancellation, repeated delivery, calculation failure | Local runner keeps demo setup small; worker path exists but needs its own lifecycle verification. |
| ReportLab | calculated report payload → PDF bytes | missing analytics or download failure | Existing server-side reporting; HTML export would be a simpler alternative if PDF were unnecessary. |
| Research explainer | question + authorized read-only tools → explanation | advice requests or provider failures | Deterministic fallback keeps demo reproducible; external model is optional and separately bounded. |

### Read these files in order

1. `apps/api/app/main.py`: route/dependency boundary.
2. `apps/api/app/auth.py`, `models.py`, `database.py`: identity and persistence.
3. `apps/api/app/imports.py`: validation before writes and exact-byte replay.
4. `apps/api/app/analytics.py`: `holdings_snapshot`, `performance_analytics`, `_drawdown`.
5. `apps/api/app/scenarios.py`: calculation and execution lifecycle.
6. `apps/web/app/api.ts`, `components/Dashboard.tsx`: client requests and UI state.
7. `apps/api/tests/test_imports.py`, `test_authorization.py`, and dashboard tests:
   examples of boundary evidence.

Understand percentages as decimal returns, static-quantity assumptions,
transactions versus pre-write validation, owner-scoped queries, and asynchronous
UI state. Prefer explaining an actual request to memorizing stack names.

## Problem-solving stories

Use the journal for full reproductions and exact evidence. These outlines describe
project evidence, not claims about what the learner personally did.

1. **CSV numeric boundaries:** Invalid inputs should be rejected → suspected
   positivity was insufficient → 11 new cases failed before the fix → require
   finite positive numbers and correct row width → small pre-write checks →
   stricter row shape requires explicit blanks → 43 API tests passed after the
   fix → parseability is not domain validity.
2. **Preserve rather than rewrite:** Existing features were costly to study →
   suspected a smaller local path was sufficient → source/tests showed a seeded
   Next.js/FastAPI/SQLite journey → keep that architecture and repair boundaries →
   define a focused scope → optional integrations remain but are not prerequisites
   → existing baseline lint/tests/type/build passed → require evidence for rewrites.
3. **Empty-portfolio loading:** Creation showed old holdings and a missing-market-
   prices error → suspected aggregate request failure → browser reproduced eight
   old rows and both new component tests failed → separate holdings from optional
   analytics and guard superseded loads → two-stage loading without fabricated
   metrics → four frontend tests, types, build, and isolated browser import passed
   → expected API errors need deliberate UI states (commit `549fffa`).

4. **Scenario lifecycle:** Cancelled jobs became completed/failed and repeated
   delivery reran terminal jobs → suspected stale status checks → seven controlled
   pre-fix failures → conditional database transitions and winner-only audit →
   cancellation discards outcomes but cannot interrupt computation or recover a
   crashed worker → 54 API tests and lint passed → lifecycle invariants belong
   in database predicates, not cached ORM state.

## Learning and reflection

Be able to explain why validation precedes writes; why replay hashing is not proof
of concurrent idempotency; why ownership belongs in resource queries; how drawdown
tracks the running peak; and why a slow old request must not replace a newer
portfolio's display.

Improve next: verify PDF download and frontend scenario terminal/polling states,
sparse-history policies, and imported-price
ownership. Decide whether to restrict inputs to CAD or implement actual FX
conversion; summing arbitrary currencies is not a production accounting model.

For production: real authentication, tenant/data boundaries, numerical/market-data
policies, concurrency constraints, durable job recovery, monitoring, retention,
security review, and deployed-system tests. Do not confuse a demo token with
real customer authentication or an instantaneous shock with a forecast.

Next time, cover empty/error states alongside the first happy path and write
boundary tests before describing the workflow as complete.

## Likely questions and follow-ups

| Question | Concise answer outline | Follow-up to practice |
| --- | --- | --- |
| Who uses this and why? | Reviewer/learner exploring explainable portfolio analytics. | What is deliberately outside scope? |
| Why this stack? | Preserve a tested UI/API boundary with a small local database path. | What would justify a worker or a different database? |
| What bug is supported by evidence? | CSV finite-value/row-shape failures; pre-fix failures and post-fix checks recorded. | Why does `NaN <= 0` not catch the problem? |
| How is import atomic? | Validate all rows before writes; commit once; rollback on write exceptions. | What does this not prove about concurrent requests? |
| How is authorization enforced? | Auth dependency plus owner-filtered service/resource queries. | Why return 404 for a different owner's resource? |
| What makes a test meaningful? | Observable behavior, realistic boundary input, and unchanged-table assertions. | Can a high coverage percentage hide missing error cases? |
| How are scenarios interpreted? | Deterministic shocks to current values with explicit omissions. | What does cancellation require under concurrent execution? |
| What measurement can you claim? | Local test outcomes; historical in-process benchmark with limits. | Why is reciprocal latency not concurrent throughput? |
| What would you improve first? | Complete failure/empty-state workflows and resolve data semantics. | Which requirement changes the architecture? |

## Quick preparation plan and demonstration script

1. Understand the purpose and architecture.
2. Run the main demonstration.
3. Read the key implementation files.
4. Reproduce and understand the strongest debugging examples.
5. Review decisions, evidence, and limitations.
6. Practice explaining the project without notes.

**Demo:** Follow README local setup using the API virtualenv; run the web app.
Enter the workspace, show benchmark comparison, open Holdings, then run Technology
drawdown. Explain the assumptions before interpreting the result. Show the CSV
regression tests and journal. Try PDF export only after checking its browser path;
the initial native browser download was canceled and is not yet verified. Avoid
using personal financial data or claiming the shared demo workspace is read-only.

**One-page talking points:**

- Purpose: explain the path from portfolio inputs to transparent metrics.
- Audience: reviewer or learner; not a trading or advice service.
- Architecture: Next.js → FastAPI → SQLAlchemy/SQLite → deterministic services.
- Strong evidence: CSV and lifecycle failures reproduced; latest API run has 54
  passing tests and 85% statement coverage.
- Decision: preserve useful behavior; optional infrastructure is not required locally.
- Tradeoff: reproducible static data and simplified shocks, not live financial accuracy.
- Limits: browser export and scenario lifecycle need further verification; no
  production impact or performance improvement claim.
- Personal learning: fill in only after reproducing and recording your own study.
