import pytest

from app.database import init_db


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database() -> None:
    init_db()
