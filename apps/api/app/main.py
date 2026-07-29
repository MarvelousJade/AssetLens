from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .analytics import (
    attribution_analytics,
    exposure_analytics,
    get_portfolio,
    holdings_snapshot,
    performance_analytics,
)
from .auth import require_demo_user
from .config import settings
from .copilot import answer_question
from .database import Base, SessionLocal, engine, get_db
from .imports import import_holdings_csv
from .models import (
    AuditEvent,
    BenchmarkPrice,
    MarketPrice,
    Portfolio,
    PriceAlert,
    Report,
    ScenarioRun,
    Security,
    WatchlistItem,
)
from .reports import build_pdf, report_payload
from .scenarios import execute_scenario, scenario_catalog
from .schemas import AlertCreate, CopilotQuestion, PortfolioCreate, PortfolioUpdate, ScenarioCreate
from .seed import seed_demo
from .telemetry import configure_telemetry


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo(db)
    yield


app = FastAPI(
    title="AssetLens API",
    version="0.1.0",
    description="Authenticated portfolio analytics, deterministic scenarios, and grounded research.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
configure_telemetry(app)

Db = Annotated[Session, Depends(get_db)]
User = Annotated[str, Depends(require_demo_user)]


def not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


@app.get("/api/health")
def health(db: Db) -> dict[str, Any]:
    db.execute(text("SELECT 1"))
    latest = db.scalar(select(func.max(BenchmarkPrice.price_date)))
    return {
        "status": "ok",
        "service": "assetlens-api",
        "version": "0.1.0",
        "database": "connected",
        "market_data_as_of": latest.isoformat() if latest else None,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/portfolios")
def list_portfolios(db: Db, user: User) -> list[dict[str, Any]]:
    rows = list(
        db.scalars(select(Portfolio).where(Portfolio.owner_id == user).order_by(Portfolio.created_at))
    )
    return [
        {
            "id": row.id,
            "name": row.name,
            "benchmark": row.benchmark,
            "benchmark_name": row.benchmark_name,
            "archived": row.archived,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@app.post("/api/portfolios", status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, db: Db, user: User) -> dict[str, Any]:
    portfolio = Portfolio(
        name=payload.name,
        benchmark=payload.benchmark,
        benchmark_name=payload.benchmark_name,
        owner_id=user,
    )
    db.add(portfolio)
    db.flush()
    db.add(
        AuditEvent(
            actor_id=user,
            action="portfolio.created",
            resource_type="portfolio",
            resource_id=portfolio.id,
        )
    )
    db.commit()
    return {"id": portfolio.id, "name": portfolio.name, "benchmark": portfolio.benchmark}


@app.patch("/api/portfolios/{portfolio_id}")
def update_portfolio(portfolio_id: str, payload: PortfolioUpdate, db: Db, user: User) -> dict[str, Any]:
    try:
        portfolio = get_portfolio(db, portfolio_id, user)
    except LookupError as exc:
        raise not_found(exc) from exc
    if payload.name is not None:
        portfolio.name = payload.name
    if payload.archived is not None:
        portfolio.archived = payload.archived
    db.commit()
    return {"id": portfolio.id, "name": portfolio.name, "archived": portfolio.archived}


@app.get("/api/portfolios/{portfolio_id}/holdings")
def get_holdings(portfolio_id: str, db: Db, user: User) -> dict[str, Any]:
    try:
        return holdings_snapshot(db, portfolio_id, user)
    except (LookupError, ValueError) as exc:
        raise not_found(exc) from exc


@app.post("/api/portfolios/{portfolio_id}/imports")
async def import_portfolio(
    portfolio_id: str,
    db: Db,
    user: User,
    file: Annotated[UploadFile, File()],
) -> dict[str, Any]:
    try:
        result = import_holdings_csv(db, portfolio_id, user, await file.read())
    except LookupError as exc:
        raise not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result.get("errors"):
        raise HTTPException(status_code=422, detail=result)
    return result


@app.get("/api/portfolios/{portfolio_id}/performance")
def get_performance(portfolio_id: str, db: Db, user: User) -> dict[str, Any]:
    try:
        return performance_analytics(db, portfolio_id, user)
    except LookupError as exc:
        raise not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/portfolios/{portfolio_id}/risk")
def get_risk(portfolio_id: str, db: Db, user: User) -> dict[str, Any]:
    try:
        performance = performance_analytics(db, portfolio_id, user)
    except (LookupError, ValueError) as exc:
        raise not_found(exc) from exc
    risk_keys = {"annualized_volatility", "sharpe_ratio", "maximum_drawdown"}
    return {
        "metrics": {key: value for key, value in performance["metrics"].items() if key in risk_keys},
        "methodology": {key: value for key, value in performance["methodology"].items() if key in risk_keys},
        "as_of": performance["as_of"],
        "calculated_at": performance["calculated_at"],
    }


@app.get("/api/portfolios/{portfolio_id}/exposure")
def get_exposure(portfolio_id: str, db: Db, user: User) -> dict[str, Any]:
    try:
        return exposure_analytics(db, portfolio_id, user)
    except LookupError as exc:
        raise not_found(exc) from exc


@app.get("/api/portfolios/{portfolio_id}/attribution")
def get_attribution(portfolio_id: str, db: Db, user: User) -> dict[str, Any]:
    try:
        return attribution_analytics(db, portfolio_id, user)
    except LookupError as exc:
        raise not_found(exc) from exc


@app.get("/api/scenarios/catalog")
def get_scenario_catalog(_: User) -> list[dict[str, Any]]:
    return scenario_catalog()


@app.post(
    "/api/portfolios/{portfolio_id}/scenarios",
    status_code=status.HTTP_202_ACCEPTED,
)
def create_scenario(
    portfolio_id: str,
    payload: ScenarioCreate,
    background_tasks: BackgroundTasks,
    db: Db,
    user: User,
) -> dict[str, Any]:
    try:
        get_portfolio(db, portfolio_id, user)
    except LookupError as exc:
        raise not_found(exc) from exc
    if payload.scenario_type == "custom" and not payload.shocks:
        raise HTTPException(status_code=422, detail="Custom scenarios require at least one shock.")
    if any(value < -1 or value > 1 for value in payload.shocks.values()):
        raise HTTPException(status_code=422, detail="Scenario shocks must be between -1 and 1.")
    run = ScenarioRun(
        portfolio_id=portfolio_id,
        name=payload.name,
        scenario_type=payload.scenario_type,
        shocks=payload.shocks,
    )
    db.add(run)
    db.commit()
    if settings.task_mode == "celery":
        from .tasks import run_scenario_task

        run_scenario_task.delay(run.id)
    else:
        background_tasks.add_task(_run_scenario_local, run.id)
    return {"id": run.id, "status": run.status, "poll_url": f"/api/scenario-runs/{run.id}"}


def _run_scenario_local(run_id: str) -> None:
    with SessionLocal() as db:
        execute_scenario(run_id, db)


def _get_scenario_run(db: Session, run_id: str, owner_id: str) -> ScenarioRun:
    run = db.scalar(
        select(ScenarioRun)
        .join(Portfolio, ScenarioRun.portfolio_id == Portfolio.id)
        .where(ScenarioRun.id == run_id, Portfolio.owner_id == owner_id)
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Scenario run not found")
    return run


@app.get("/api/scenario-runs/{run_id}")
def get_scenario_run(run_id: str, db: Db, user: User) -> dict[str, Any]:
    run = _get_scenario_run(db, run_id, user)
    return {
        "id": run.id,
        "portfolio_id": run.portfolio_id,
        "name": run.name,
        "scenario_type": run.scenario_type,
        "shocks": run.shocks,
        "status": run.status,
        "result": run.result,
        "error": run.error,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


@app.post("/api/scenario-runs/{run_id}/cancel")
def cancel_scenario_run(run_id: str, db: Db, user: User) -> dict[str, str]:
    run = _get_scenario_run(db, run_id, user)
    if run.status not in {"pending", "running"}:
        raise HTTPException(status_code=409, detail="Only pending or running scenarios can be cancelled.")
    run.status = "cancelled"
    db.commit()
    return {"id": run.id, "status": run.status}


@app.post("/api/copilot/questions")
def ask_copilot(payload: CopilotQuestion, db: Db, user: User) -> dict[str, Any]:
    try:
        get_portfolio(db, payload.portfolio_id, user)
    except LookupError as exc:
        raise not_found(exc) from exc
    return answer_question(db, payload.portfolio_id, user, payload.question)


@app.post("/api/portfolios/{portfolio_id}/reports", status_code=201)
def create_report(portfolio_id: str, db: Db, user: User) -> dict[str, Any]:
    try:
        payload = report_payload(db, portfolio_id, user)
        pdf = build_pdf(payload)
    except LookupError as exc:
        raise not_found(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    report = Report(portfolio_id=portfolio_id, payload=payload, pdf_bytes=pdf)
    db.add(report)
    db.flush()
    db.add(
        AuditEvent(
            actor_id=user,
            action="report.created",
            resource_type="report",
            resource_id=report.id,
            detail={"data_as_of": payload["holdings"]["as_of"]},
        )
    )
    db.commit()
    return {
        "id": report.id,
        "status": report.status,
        "download_url": f"/api/reports/{report.id}",
        "created_at": report.created_at,
    }


@app.get("/api/reports/{report_id}")
def download_report(report_id: str, db: Db, user: User) -> Response:
    report = db.scalar(
        select(Report)
        .join(Portfolio, Report.portfolio_id == Portfolio.id)
        .where(Report.id == report_id, Portfolio.owner_id == user)
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    pdf = report.pdf_bytes or build_pdf(report.payload)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="assetlens-{report_id[:8]}.pdf"'},
    )


@app.get("/api/securities")
def screen_securities(
    db: Db,
    _: User,
    sector: str | None = Query(default=None),
    asset_class: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=80),
) -> list[dict[str, Any]]:
    query = select(Security).order_by(Security.symbol)
    if sector:
        query = query.where(Security.sector == sector)
    if asset_class:
        query = query.where(Security.asset_class == asset_class)
    if search:
        query = query.where(Security.symbol.ilike(f"%{search}%") | Security.name.ilike(f"%{search}%"))
    rows = list(db.scalars(query.limit(100)))
    result = []
    for security in rows:
        price = db.scalar(
            select(MarketPrice.close)
            .where(MarketPrice.security_id == security.id)
            .order_by(MarketPrice.price_date.desc())
            .limit(1)
        )
        result.append(
            {
                "id": security.id,
                "symbol": security.symbol,
                "name": security.name,
                "sector": security.sector,
                "asset_class": security.asset_class,
                "geography": security.geography,
                "latest_price": price,
            }
        )
    return result


@app.get("/api/watchlist")
def get_watchlist(db: Db, user: User) -> list[dict[str, Any]]:
    rows = db.execute(
        select(WatchlistItem, Security)
        .join(Security, WatchlistItem.security_id == Security.id)
        .where(WatchlistItem.owner_id == user)
        .order_by(WatchlistItem.created_at.desc())
    ).all()
    return [
        {
            "id": item.id,
            "security_id": security.id,
            "symbol": security.symbol,
            "name": security.name,
        }
        for item, security in rows
    ]


@app.post("/api/watchlist/{security_id}", status_code=201)
def add_watchlist(security_id: str, db: Db, user: User) -> dict[str, Any]:
    security = db.get(Security, security_id)
    if security is None:
        raise HTTPException(status_code=404, detail="Security not found")
    existing = db.scalar(
        select(WatchlistItem).where(WatchlistItem.owner_id == user, WatchlistItem.security_id == security_id)
    )
    if existing:
        return {"id": existing.id, "symbol": security.symbol, "idempotent_replay": True}
    item = WatchlistItem(owner_id=user, security_id=security_id)
    db.add(item)
    db.commit()
    return {"id": item.id, "symbol": security.symbol, "idempotent_replay": False}


@app.delete("/api/watchlist/{item_id}", status_code=204)
def remove_watchlist(item_id: str, db: Db, user: User) -> Response:
    item = db.scalar(select(WatchlistItem).where(WatchlistItem.id == item_id, WatchlistItem.owner_id == user))
    if item is None:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@app.get("/api/alerts")
def get_alerts(db: Db, user: User) -> list[dict[str, Any]]:
    rows = db.execute(
        select(PriceAlert, Security)
        .join(Security, PriceAlert.security_id == Security.id)
        .where(PriceAlert.owner_id == user)
        .order_by(PriceAlert.created_at.desc())
    ).all()
    return [
        {
            "id": alert.id,
            "symbol": security.symbol,
            "direction": alert.direction,
            "threshold": alert.threshold,
            "enabled": alert.enabled,
        }
        for alert, security in rows
    ]


@app.post("/api/alerts", status_code=201)
def create_alert(payload: AlertCreate, db: Db, user: User) -> dict[str, Any]:
    security = db.scalar(select(Security).where(Security.symbol == payload.symbol.upper()))
    if security is None:
        raise HTTPException(status_code=404, detail="Security not found")
    alert = PriceAlert(
        owner_id=user,
        security_id=security.id,
        direction=payload.direction,
        threshold=payload.threshold,
    )
    db.add(alert)
    db.commit()
    return {
        "id": alert.id,
        "symbol": security.symbol,
        "direction": alert.direction,
        "threshold": alert.threshold,
    }
