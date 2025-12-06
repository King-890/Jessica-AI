import os

# Disable local-only enforcement for tests using TestClient
os.environ["ENFORCE_LOCAL_ONLY"] = "false"

from fastapi.testclient import TestClient
from api.internal_api import app


def test_health():
    client = TestClient(app)
    r = client.get("/internal/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"