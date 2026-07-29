import pytest
from sqlalchemy import select

from app.analytics import (
    _drawdown,
    attribution_analytics,
    exposure_analytics,
    holdings_snapshot,
    performance_analytics,
)
from app.database import SessionLocal
from app.models import Portfolio


def test_drawdown_tracks_running_peak():
    values, minimum = _drawdown([100, 110, 99, 105, 88, 120])
    assert values[0] == 0
    assert values[-1] == 0
    assert minimum == pytest.approx(-0.2)


def test_seeded_performance_is_reproducible(database):
    with SessionLocal() as db:
        portfolio = db.scalar(select(Portfolio).where(Portfolio.id == "demo-canadian-growth"))
        result = performance_analytics(db, portfolio.id, portfolio.owner_id)
    assert len(result["series"]) == 260
    assert result["as_of"] == "2026-07-23"
    assert result["metrics"]["maximum_drawdown"] <= 0
    assert result["metrics"]["annualized_volatility"] > 0
    assert "formula" in result["methodology"]["sharpe_ratio"]


def test_exposure_weights_sum_to_one(database):
    with SessionLocal() as db:
        result = exposure_analytics(
            db, "demo-canadian-growth", "demo-user"
        )
    assert sum(item["weight"] for item in result["allocation"]["sector"]) == pytest.approx(1, abs=1e-5)


@pytest.mark.parametrize(
    "operation",
    [
        holdings_snapshot,
        performance_analytics,
        exposure_analytics,
        attribution_analytics,
    ],
)
def test_analytics_reject_another_owner(database, operation):
    with SessionLocal() as db:
        with pytest.raises(LookupError, match="Portfolio not found"):
            operation(db, "demo-canadian-growth", "another-user")
