# tests/conftest.py
import os
import sys
import json
import time
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Asegurar que `app` sea importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite:///./test_guitar.db"
test_engine = create_engine(
    TEST_DB_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

RESULTS = []
RESULTS_FILE = os.path.join(os.path.dirname(__file__), "..", "test_results.json")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        duration_ms = round(report.duration * 1000, 2)
        status = (
            "passed" if report.passed else ("failed" if report.failed else "skipped")
        )
        RESULTS.append(
            {
                "event": "test_result",
                "suite": item.module.__name__.replace("tests.", "").replace("test_", ""),
                "test_name": item.name,
                "description": getattr(item, "_test_description", item.name),
                "status": status,
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "commit_sha": os.environ.get("GITHUB_SHA", "local"),
                "branch": os.environ.get("GITHUB_REF_NAME", "local"),
                "actor": os.environ.get("GITHUB_ACTOR", "local"),
                "input": getattr(item, "_test_input", None),
                "expected": getattr(item, "_test_expected", None),
                "method": getattr(item, "_test_method", None),
                "endpoint": getattr(item, "_test_endpoint", None),
                "status_code": getattr(item, "_test_status_code", None),
                "response_time_ms": getattr(item, "_test_response_time_ms", None),
                "error_message": str(report.longrepr) if report.failed else None,
            }
        )


def pytest_sessionfinish(session, exitstatus):
    summary = {
        "total": len(RESULTS),
        "passed": sum(1 for r in RESULTS if r["status"] == "passed"),
        "failed": sum(1 for r in RESULTS if r["status"] == "failed"),
        "skipped": sum(1 for r in RESULTS if r["status"] == "skipped"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": RESULTS,
    }
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Resultados escritos en {RESULTS_FILE} ({len(RESULTS)} pruebas)")


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_headers(client):
    client.post(
        "/register",
        json={"username": "admin", "password": "admin12345", "is_admin": False},
    )
    res = client.post("/token", data={"username": "admin", "password": "admin12345"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def vendor_headers(client, admin_headers):
    client.post(
        "/register",
        json={"username": "vendor", "password": "vendor12345", "is_admin": False},
    )
    res = client.post("/token", data={"username": "vendor", "password": "vendor12345"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def mark_test(request):
    def _mark(
        description,
        test_input=None,
        expected=None,
        method=None,
        endpoint=None,
        status_code=None,
        response_time_ms=None,
    ):
        request.node._test_description = description
        request.node._test_input = test_input
        request.node._test_expected = expected
        request.node._test_method = method
        request.node._test_endpoint = endpoint
        request.node._test_status_code = status_code
        request.node._test_response_time_ms = response_time_ms

    return _mark


def timed_request(client, method, endpoint, **kwargs):
    start = time.perf_counter()
    res = getattr(client, method.lower())(endpoint, **kwargs)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return res, elapsed_ms