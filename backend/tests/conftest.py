import json
import os

import pytest
from fastapi.testclient import TestClient

from agent import db
from agent.orchestrator import CRM_LOG_PATH
from backend.app import app


@pytest.fixture(autouse=True)
def fresh_state():
    """
    Resets the SQLite DB (re-seeding inventory) and clears the mock CRM log
    before every test, so tests don't leak leads/bookings/handoffs into
    each other. This talks only to agent.db.reset_db()/init_db(), the same
    functions the app itself calls - no test-only backdoor into the schema.
    """
    db.reset_db()
    db.init_db()
    if os.path.exists(CRM_LOG_PATH):
        os.remove(CRM_LOG_PATH)
    yield
    if os.path.exists(CRM_LOG_PATH):
        os.remove(CRM_LOG_PATH)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def a_workspace_id(client):
    """First seeded meeting_room workspace id, for instant-book tests."""
    resp = client.get("/api/workspaces", params={"workspace_type": "meeting_room"})
    assert resp.status_code == 200
    workspaces = resp.json()
    assert workspaces, "expected at least one seeded meeting_room workspace"
    return workspaces[0]
