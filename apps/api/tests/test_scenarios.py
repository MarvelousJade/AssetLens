import pytest
from sqlalchemy import func, select

from app import main, scenarios
from app.database import SessionLocal
from app.models import AuditEvent, ScenarioRun


def _create_run(status="pending"):
    with SessionLocal() as db:
        run = ScenarioRun(
            portfolio_id="demo-canadian-growth", name="Lifecycle regression",
            scenario_type="technology_decline", status=status,
        )
        db.add(run)
        db.commit()
        return run.id


def _completion_count(db, run_id):
    return db.scalar(
        select(func.count()).select_from(AuditEvent).where(
            AuditEvent.resource_id == run_id, AuditEvent.action == "scenario.completed"
        )
    )


@pytest.mark.parametrize("status", ["running", "completed", "failed", "cancelled"])
def test_only_pending_scenarios_can_be_claimed(database, monkeypatch, status):
    run_id = _create_run(status)
    calls = []

    def calculate(*args):
        calls.append(True)
        return {"test_result": True}

    monkeypatch.setattr(scenarios, "calculate_scenario", calculate)
    with SessionLocal() as db:
        scenarios.execute_scenario(run_id, db)
    with SessionLocal() as db:
        run = db.get(ScenarioRun, run_id)
        assert run.status == status
        assert run.result is None
        assert _completion_count(db, run_id) == 0
    assert calls == []


@pytest.mark.parametrize("calculation_fails", [False, True])
def test_cancellation_during_calculation_is_not_overwritten(database, monkeypatch, calculation_fails):
    run_id = _create_run()

    def cancel_during_calculation(db, run, owner_id):
        with SessionLocal() as cancelling_db:
            cancelling = cancelling_db.get(ScenarioRun, run.id)
            assert cancelling.status == "running"
            cancelling.status = "cancelled"
            cancelling_db.commit()
        if calculation_fails:
            raise RuntimeError("Calculation failed after cancellation")
        return {"test_result": True}

    monkeypatch.setattr(scenarios, "calculate_scenario", cancel_during_calculation)
    with SessionLocal() as db:
        scenarios.execute_scenario(run_id, db)
    with SessionLocal() as db:
        run = db.get(ScenarioRun, run_id)
        assert run.status == "cancelled"
        assert run.result is None
        assert run.error is None
        assert _completion_count(db, run_id) == 0


def test_completed_scenario_delivery_does_not_recalculate_or_duplicate_audit(database):
    run_id = _create_run()
    with SessionLocal() as db:
        scenarios.execute_scenario(run_id, db)
    with SessionLocal() as db:
        first = db.get(ScenarioRun, run_id)
        assert first.status == "completed"
        expected = (first.result, first.completed_at)
        assert _completion_count(db, run_id) == 1
        scenarios.execute_scenario(run_id, db)
    with SessionLocal() as db:
        replay = db.get(ScenarioRun, run_id)
        assert (replay.result, replay.completed_at) == expected
        assert _completion_count(db, run_id) == 1


def test_duplicate_delivery_during_calculation_does_not_claim_running_run(database, monkeypatch):
    run_id = _create_run()
    original_calculation = scenarios.calculate_scenario
    calls = []

    def calculate_with_duplicate_delivery(db, run, owner_id):
        calls.append(True)
        if len(calls) == 1:
            with SessionLocal() as duplicate_db:
                scenarios.execute_scenario(run_id, duplicate_db)
        return original_calculation(db, run, owner_id)

    monkeypatch.setattr(scenarios, "calculate_scenario", calculate_with_duplicate_delivery)
    with SessionLocal() as db:
        scenarios.execute_scenario(run_id, db)
    assert len(calls) == 1
    with SessionLocal() as db:
        assert db.get(ScenarioRun, run_id).status == "completed"
        assert _completion_count(db, run_id) == 1


def test_pending_run_can_be_cancelled(client, auth_headers):
    run_id = _create_run()
    response = client.post(f"/api/scenario-runs/{run_id}/cancel", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"id": run_id, "status": "cancelled"}
    with SessionLocal() as db:
        scenarios.execute_scenario(run_id, db)
    with SessionLocal() as db:
        run = db.get(ScenarioRun, run_id)
        assert run.status == "cancelled"
        assert run.completed_at is not None
        assert run.result is None
        assert _completion_count(db, run_id) == 0


def test_calculation_error_records_failed_state(database, monkeypatch):
    run_id = _create_run()

    def fail(*args):
        raise RuntimeError("Reproducible calculation failure")

    monkeypatch.setattr(scenarios, "calculate_scenario", fail)
    with SessionLocal() as db:
        scenarios.execute_scenario(run_id, db)
    with SessionLocal() as db:
        run = db.get(ScenarioRun, run_id)
        assert run.status == "failed"
        assert run.error == "Reproducible calculation failure"
        assert run.completed_at is not None
        assert _completion_count(db, run_id) == 0


def test_cancel_does_not_overwrite_a_concurrently_completed_run(client, auth_headers, monkeypatch):
    run_id = _create_run("running")
    original_lookup = main._get_scenario_run

    def complete_after_lookup(db, requested_id, owner_id):
        run = original_lookup(db, requested_id, owner_id)
        with SessionLocal() as completing_db:
            completing = completing_db.get(ScenarioRun, requested_id)
            completing.status = "completed"
            completing_db.commit()
        return run

    monkeypatch.setattr(main, "_get_scenario_run", complete_after_lookup)
    response = client.post(f"/api/scenario-runs/{run_id}/cancel", headers=auth_headers)
    assert response.status_code == 409
    with SessionLocal() as db:
        assert db.get(ScenarioRun, run_id).status == "completed"
