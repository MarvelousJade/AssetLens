# AssetLens

AssetLens is a portfolio research and analytics workbench built as an independent
demonstration project. It is not affiliated with TD and does not reproduce any
private TD system.

The app ships with a seeded Canadian multi-asset portfolio so the complete
experience works immediately: benchmark comparison, risk metrics, exposure,
performance attribution, deterministic stress scenarios, a grounded research
copilot, CSV import, and timestamped PDF reports.

![AssetLens portfolio overview](docs/screenshots/dashboard.png)

## Live demo

Open [assetlens-web.onrender.com](https://assetlens-web.onrender.com) and choose
**Enter demo workspace**. The deployment uses free Render web services and a
free Neon PostgreSQL database, so the first request after inactivity can take a
moment to wake up.

## Verified outcomes

- Prevented partial portfolio updates during CSV ingestion: a file containing
  an invalid row left holdings unchanged, while an identical valid-file replay
  was recognized without processing the import twice.
- Validated portfolio analytics across 260 deterministic business-day
  observations, with sector exposure weights reconciling to 100% and drawdown
  calculations tracking the running peak.
- Grounded all 3 tested research questions in the correct read-only analytics
  tools with citations, and refused all 3 tested buy/sell/price-target prompts
  before making any tool call.
- Re-verified 18 automated tests locally on July 29, 2026: 16 API tests with
  80% statement coverage across 933 Python statements, 1 React test, and
  1 Chromium reviewer workflow covering entry, analytics, and scenario execution.

No throughput, latency, or deployment-time improvement is claimed because the
repository does not contain a recorded load test or manual deployment baseline.

## Quick start

### Local development

Prerequisites: Node.js 20+, Python 3.12+, and npm.

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd apps/web
npm install
npm run dev
```

Open <http://localhost:3000> and choose **Enter demo workspace**. The frontend
proxies `/api` requests to FastAPI at `http://localhost:8000`.

### Docker Compose

```powershell
docker compose up --build
```

This starts the web app, API, PostgreSQL, Redis, and a Celery worker.

## Demo flow

1. Enter the demo workspace.
2. Review the seeded Canadian Growth & Income portfolio.
3. Compare its return and drawdown with the S&P/TSX Composite proxy.
4. Inspect sector allocation and holding-level contributors.
5. Run the **Technology drawdown** scenario.
6. Ask, “Why did this portfolio underperform its benchmark?”
7. Export the timestamped research report.

## CSV format

Imports are atomic: a file with any invalid row changes nothing. Required
columns are `ticker`, `quantity`, and `average_cost`.

```csv
ticker,name,quantity,average_cost,current_price,sector,asset_class,geography,currency
RY,Royal Bank of Canada,25,128.40,151.20,Financials,Equity,Canada,CAD
XBB,iShares Core Canadian Universe Bond ETF,40,29.10,28.65,Fixed Income,Fixed Income,Canada,CAD
```

## Copilot safety model

- All model-accessible tools are authenticated and read-only.
- Financial metrics are calculated by the analytics engine, never by the LLM.
- Answers include tool-call records, source identifiers, and data timestamps.
- Personalized buy/sell/hold questions are refused.
- Retrieved or tool-provided text is treated as data, not as instructions.
- The live OpenAI path is optional. With `OPENAI_API_KEY` configured,
  `COPILOT_PROVIDER=auto` uses the Responses API and `gpt-5.6-sol`; otherwise a
  deterministic grounded explanation keeps the demonstration fully usable.

## Repository map

```text
apps/api/     FastAPI, SQLAlchemy, analytics, scenarios, copilot, reports
apps/web/     Next.js, React, TypeScript dashboard
tests/e2e/    Playwright smoke journey
infra/        Kubernetes and Kustomize manifests
docs/         Architecture, security, and metric methodology
```

## Verification matrix

The outcomes below are tied to automated checks or a recorded benchmark on the
current revision. They are not production measurements, and no percentage
improvement is claimed without a before-and-after baseline.

| Verified outcome | Automated evidence | Current result |
| --- | --- | --- |
| Prevented partial portfolio writes from invalid CSV imports and duplicate effects from exact import replays. | `test_csv_import_is_atomic_and_idempotent` | Invalid input left the portfolio unchanged; replaying identical valid bytes returned an idempotent result. |
| Prevented cross-user access to portfolio analytics, mutations, scenario results, and reports. | `test_authorization.py` plus service-layer owner checks | 11 protected cross-owner read/workflow attempts returned `404`; portfolio lists remained owner-scoped. |
| Grounded copilot answers in read-only analytics tools and refused personalized trading advice. | Six parameterized cases in `test_copilot.py` | Three research prompts produced tool records and citations; three buy/sell/price-target prompts were refused before tool use. |
| Produced deterministic scenario results and downloadable research reports. | `test_scenario_job_returns_grounded_impact` and `test_report_is_a_real_pdf` | Scenario completed with three explicit assumptions; report output was a valid PDF larger than 2 KB. |
| Exercised the reviewer journey from demo entry through dashboard analytics and scenario impact. | React Testing Library and `tests/e2e/demo.spec.ts` | 1 frontend test and 1 Chromium Playwright journey passed locally. |
| Replaced ad hoc repository checks with a repeatable CI workflow. | Four GitHub Actions jobs in `.github/workflows/ci.yml` | Automates API lint/tests/migrations, frontend audit/tests/build, two container builds, and the browser journey. |
| Established an absolute performance baseline without inventing an improvement percentage. | `scripts/benchmark_api.py` and `docs/performance.md` | 410 measured sequential local requests completed without HTTP errors; recorded p95 latency ranged from 70.527 ms to 158.745 ms by operation. |

Current local verification: **28 API tests passed with 83% statement coverage**,
the frontend test passed, the optimized Next.js build completed, and the
Playwright journey passed.

## Quality commands

```powershell
cd apps/api
pytest
ruff check app tests scripts

cd ..\web
npm test
npm run build

cd ..\..
npm run test:e2e
```

## Performance baseline

Run the local API benchmark from `apps/api`:

```powershell
python scripts/benchmark_api.py --iterations 100 --report-iterations 10
```

The benchmark uses a temporary SQLite database, FastAPI's in-process test
client, and the deterministic copilot. See [docs/performance.md](docs/performance.md)
for the recorded baseline, methodology, and limits. These measurements are not
production results or verified performance improvements.

## Disclaimer

AssetLens is for software demonstration and educational research only. Scenario
results are simplified estimates, not forecasts. Nothing in the application is
investment advice or a recommendation to buy, sell, or hold a security.
