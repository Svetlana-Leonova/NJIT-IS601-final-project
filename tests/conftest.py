import os
import tempfile

import pytest
from fastapi.testclient import TestClient

import init_db
from main import app


@pytest.fixture
def client():
    """Provide a TestClient wired to an isolated temporary SQLite database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.sqlite")
        os.environ["DB_PATH"] = db_path

        # Initialize schema + seed data into the test database
        init_db.init_db()

        with TestClient(app) as test_client:
            yield test_client

        # Temporary directory (and DB file) are cleaned up automatically

