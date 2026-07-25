import pytest
from sqlalchemy import select

from app.analytics import _drawdown, exposure_analytics, performance_analytics
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
        result = performance_analytics(db, portfolio.id)
    assert len(result["series"]) == 260
    assert result["as_of"] == "2026-07-23"
    assert result["metrics"]["maximum_drawdown"] <= 0
    assert result["metrics"]["annualized_volatility"] > 0
    assert "formula" in result["methodology"]["sharpe_ratio"]


def test_exposure_weights_sum_to_one(database):
    with SessionLocal() as db:
        result = exposure_analytics(db, "demo-canadian-growth")
    assert sum(item["weight"] for item in result["allocation"]["sector"]) == pytest.approx(1, abs=1e-5)
