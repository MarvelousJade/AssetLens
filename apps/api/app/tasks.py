from .celery_app import celery
from .database import SessionLocal
from .scenarios import execute_scenario


@celery.task(name="assetlens.run_scenario", bind=True, max_retries=2)
def run_scenario_task(self, run_id: str) -> None:
    db = SessionLocal()
    try:
        execute_scenario(run_id, db)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2) from exc
    finally:
        db.close()
