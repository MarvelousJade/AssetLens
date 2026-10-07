from datetime import datetime

import pytest
from sqlalchemy import func, select

from app import scenarios
from app.analytics import _drawdown
from app.database import SessionLocal
from app.models import AuditEvent, ScenarioRun


def test_drawdown_path_matches_expected_values():
    values, minimum = _drawdown([100, 140, 125, 130, 90, 150, 120])
    expected = [0, 0, 125 / 140 - 1, 130 / 140 - 1, 90 / 140 - 1, 0, 120 / 150 - 1]
    assert values == pytest.approx(expected)
    assert minimum == pytest.approx(90 / 140 - 1)


def test_cancelled_run_keeps_timestamp_and_discards_late_result(database, monkeypatch):
    cancelled_at = datetime(2026, 1, 2, 12)
    with SessionLocal() as db:
        run = ScenarioRun(
            portfolio_id="demo-canadian-growth", name="Late outcome regression",
            scenario_type="technology_decline",
        )
        db.add(run)
        db.commit()
        run_id = run.id

    def calculate_after_cancellation(db, run, owner_id):
        with SessionLocal() as cancelling_db:
            cancelled = cancelling_db.get(ScenarioRun, run.id)
            cancelled.status = "cancelled"
            cancelled.completed_at = cancelled_at
            cancelling_db.commit()
        return {"late_result": True}

    monkeypatch.setattr(scenarios, "calculate_scenario", calculate_after_cancellation)
    with SessionLocal() as db:
        scenarios.execute_scenario(run_id, db)
    with SessionLocal() as db:
        persisted = db.get(ScenarioRun, run_id)
        assert persisted.status == "cancelled"
        assert persisted.completed_at == cancelled_at
        assert persisted.result is None
        assert persisted.error is None
        assert db.scalar(
            select(func.count()).select_from(AuditEvent).where(
                AuditEvent.resource_id == run_id, AuditEvent.action == "scenario.completed"
            )
        ) == 0
