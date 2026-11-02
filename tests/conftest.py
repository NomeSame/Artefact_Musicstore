from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from emporio.web.app import create_app, ROOT

@pytest.fixture
def app(tmp_path):
    return create_app(ROOT, tmp_path / "test.sqlite3")

@pytest.fixture
def client(app):
    with TestClient(app) as client:
        client.get("/api/bootstrap")
        yield client
