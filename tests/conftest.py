import os
from pathlib import Path

TEST_DB = Path("/tmp/civitas-test.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

import pytest
from backend.database import Base, engine
import backend.db_models  # noqa: F401

Base.metadata.create_all(engine)

@pytest.fixture(scope="session", autouse=True)
def clean_database():
    yield
