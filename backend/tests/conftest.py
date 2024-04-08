import os
import pytest
from sqlalchemy.orm import close_all_sessions, Session
from dotenv import load_dotenv
from app.settings import Settings

TEST_DIR = os.path.abspath(os.path.dirname(__file__))

# @pytest.fixture
# def client():
#     """will be invoked for every test function"""
#     from app import create_app
#     from app.settings import settings
#     from app.models.User import User

#     app = create_app(TestingConfig)
#     with app.test_client() as client:
#         with app.app_context():
#             yield client

@pytest.fixture
def session() -> Session:
    from app.database import SessionFactory

    return SessionFactory()

def pytest_sessionstart():
    """Runs before all tests start https://stackoverflow.com/a/35394239"""
    if not load_dotenv(override=True, dotenv_path=os.path.join(TEST_DIR, "test.env")):
        raise Exception("failed to load dotenv")
    settings = Settings()
    import app.database as database
    assert settings.env == "TEST", f"double check dotenv loaded correctly (settings.ENV='{settings.ENV}')"
    assert database.settings.env == "TEST", f"double check dotenv loaded correctly (settings.ENV='{settings.ENV}')"

@pytest.fixture(autouse=True)
def run_around_tests():
    """code to run before and afer each test https://stackoverflow.com/a/62784688/5500073"""
    # code that will run before a given test:

    print("\n\nBEFORE TEST")
    # do imports now that env args are set
    from app.database import (
        createDb,
        createAllTables,
        deleteAllTables,
        deleteAllTables,
    )
    from app.database import settings, engine, SessionFactory

    # deleteDb(TestingConfig)
    assert settings.env == "TEST" # seat belt
    createDb()  # ensure test database exists
    deleteAllTables()
    createAllTables()

    yield

    # code that will run after a given test:
    print("AFTER TEST", flush=True)
    close_all_sessions()  # prevents pytest from hanging
    deleteAllTables()
    print("finished test cleanup", flush=True)