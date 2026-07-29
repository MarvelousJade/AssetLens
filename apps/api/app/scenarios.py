from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .analytics import holdings_snapshot
from .models import AuditEvent, Portfolio, ScenarioRun

PRESETS: dict[str, dict[str, Any]] = {
    "equity_decline": {
        "label": "Broad equity decline",
        "description": "Applies -15% to equity holdings and -2% to fixed income.",
        "asset_class": {"Equity": -0.15, "Fixed Income": -0.02},
    },
    "technology_decline": {
        "label": "Technology drawdown",
        "description": "Applies -25% to technology and -7% to broad-market equity exposure.",
        "sector": {"Technology": -0.25, "Broad Market": -0.07},
    },
    "interest_rate_increase": {
        "label": "Interest rates +100 bps",
        "description": "Uses a simplified -6% shock for fixed income and -4% for rate-sensitive equities.",
        "asset_class": {"Fixed Income": -0.06},
        "sector": {"Financials": -0.04, "Real Estate": -0.08},
    },
    "currency_movement": {
        "label": "CAD appreciates 10%",
        "description": "Applies -9.1% to holdings with United States geographic exposure.",
        "geography": {"United States": -0.091},
    },
}


def scenario_catalog() -> list[dict[str, Any]]:
    return [
        {"type": key, "label": value["label"], "description": value["description"]}
        for key, value in PRESETS.items()
    ]


def calculate_scenario(
    db: Session, run: ScenarioRun, owner_id: str
) -> dict[str, Any]:
    snapshot = holdings_snapshot(db, run.portfolio_id, owner_id)
    definition = PRESETS.get(run.scenario_type, {})
    custom = run.shocks or {}
    impacts: list[dict[str, Any]] = []
    total_impact = 0.0
    for holding in snapshot["holdings"]:
        shock = 0.0
        if run.scenario_type == "custom":
            shock = float(custom.get(holding["symbol"], custom.get(holding["sector"], custom.get("*", 0.0))))
        else:
            for dimension in ("asset_class", "sector", "geography"):
                shock += float(definition.get(dimension, {}).get(holding[dimension], 0.0))
        shock = max(-1.0, min(1.0, shock))
        estimated_impact = holding["market_value"] * shock
        total_impact += estimated_impact
        impacts.append(
            {
                "symbol": holding["symbol"],
                "market_value": holding["market_value"],
                "shock": round(shock, 6),
                "estimated_impact": round(estimated_impact, 2),
                "estimated_value": round(holding["market_value"] + estimated_impact, 2),
            }
        )
    impacts.sort(key=lambda item: item["estimated_impact"])
    current_value = snapshot["summary"]["market_value"]
    return {
        "portfolio_value": current_value,
        "estimated_impact": round(total_impact, 2),
        "estimated_impact_percent": round(total_impact / current_value, 6) if current_value else 0.0,
        "estimated_post_scenario_value": round(current_value + total_impact, 2),
        "affected_holdings": impacts,
        "assumptions": [
            "Shocks are instantaneous and applied independently to current market values.",
            "No trading, liquidity, tax, correlation, convexity, or second-order effects are modelled.",
            "Results are deterministic estimates, not forecasts or investment advice.",
        ],
        "as_of": snapshot["as_of"],
        "calculated_at": datetime.now(UTC).isoformat(),
    }


def execute_scenario(run_id: str, db: Session) -> None:
    row = db.execute(
        select(ScenarioRun, Portfolio.owner_id)
        .join(Portfolio, ScenarioRun.portfolio_id == Portfolio.id)
        .where(ScenarioRun.id == run_id)
    ).one_or_none()
    if row is None:
        return
    run, owner_id = row
    if run.status == "cancelled":
        return
    try:
        run.status = "running"
        db.commit()
        run.result = calculate_scenario(db, run, owner_id)
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        db.add(
            AuditEvent(
                actor_id=owner_id,
                action="scenario.completed",
                resource_type="scenario_run",
                resource_id=run.id,
                detail={"type": run.scenario_type},
            )
        )
        db.commit()
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)
        run.completed_at = datetime.now(UTC)
        db.commit()
