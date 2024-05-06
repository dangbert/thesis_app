import os
import shutil
import pytest
from sqlalchemy.orm import close_all_sessions, Session
from dotenv import load_dotenv
from app.settings import Settings, get_settings
import config
from fastapi.testclient import TestClient

TEST_DIR = os.path.abspath(os.path.dirname(__file__))

logger = config.get_logger(__name__)


@pytest.fixture
def client():
    from app.main import app

    # TODO: change how this is instantiated after next Starlette release https://github.com/encode/starlette/issues/2524
    return TestClient(app)


@pytest.fixture
def session() -> Session:
    from app.database import SessionFactory

    return SessionFactory()


@pytest.fixture
def settings() -> Settings:
    return get_settings()


def pytest_sessionstart():
    """Runs before all tests start https://stackoverflow.com/a/35394239"""
    if not load_dotenv(override=True, dotenv_path=os.path.join(TEST_DIR, "test.env")):
        raise Exception("failed to load dotenv")
    settings = get_settings()
    import app.database as database

    assert (
        settings.env == "TEST"
    ), f"double check dotenv loaded correctly (settings.env='{settings.env}')"
    assert (
        database.settings.env == "TEST"
    ), f"double check dotenv loaded correctly (settings.env='{settings.env}')"


@pytest.fixture(autouse=True)
def run_around_tests():
    """code to run before and afer each test https://stackoverflow.com/a/62784688/5500073"""
    # code that will run before a given test:

    print("\n\nBEFORE TEST")
    # do imports now that env args are set
    from app.database import (
        create_db,
        create_all_tables,
        delete_all_tables,
    )
    from app.database import settings, engine, SessionFactory

    assert settings.env == "TEST"  # seat belt
    create_db()  # ensure test database exists
    delete_all_tables()
    create_all_tables()

    logger.debug(f"recreating files dir '{settings.file_dir}'")
    if os.path.exists(settings.file_dir):
        shutil.rmtree(settings.file_dir)
    os.makedirs(settings.file_dir)

    yield

    # code that will run after a given test:
    close_all_sessions()  # prevents pytest from hanging
    # deleteAllTables() # leave around for debugging schema
