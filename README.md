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
