import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./.tmp/assetlens-test.db"
os.environ["COPILOT_PROVIDER"] = "deterministic"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_demo  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database():
    Path(".tmp").mkdir(exist_ok=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo(db)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(database):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers():
    return {"Authorization": "Bearer assetlens-demo-token"}
