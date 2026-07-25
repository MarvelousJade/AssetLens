# AssetLens

AssetLens is a portfolio research and analytics workbench built as an independent
demonstration project. It is not affiliated with TD and does not reproduce any
private TD system.

The app ships with a seeded Canadian multi-asset portfolio so the complete
experience works immediately: benchmark comparison, risk metrics, exposure,
performance attribution, deterministic stress scenarios, a grounded research
copilot, CSV import, and timestamped PDF reports.

![AssetLens portfolio overview](docs/screenshots/dashboard.png)

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
ruff check .

cd ..\web
npm test
npm run build

cd ..\..
npm run test:e2e
```

## Disclaimer

AssetLens is for software demonstration and educational research only. Scenario
results are simplified estimates, not forecasts. Nothing in the application is
investment advice or a recommendation to buy, sell, or hold a security.
