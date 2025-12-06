import os

# Disable local-only enforcement for tests using TestClient
os.environ["ENFORCE_LOCAL_ONLY"] = "false"

from fastapi.testclient import TestClient
from api.internal_api import app


def test_process():
    client = TestClient(app)
    r = client.post("/internal/process", json={"text": "hello"})
    assert r.status_code == 200
    body = r.json()
    assert "output" in body
    assert "hello" in body["output"].lower()