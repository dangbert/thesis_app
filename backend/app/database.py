from sqlalchemy.orm import registry, sessionmaker
from sqlalchemy import create_engine, Column, Integer, DateTime, func
from sqlalchemy.exc import ProgrammingError, OperationalError
from app.settings import Settings
import psycopg2
from psycopg2 import sql
import time
import app.models as models
from app.models.Base import Base

settings = Settings()

engine = create_engine(settings.db_uri, echo=False)
mapper_registry = Base.registry
meta = Base.metadata

# database Session factory
# TODO: look into these params:
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def dbExists(awaitConnection: bool = True):
    """
    return true if DB exists (for environment's config).
    If DB connection isn't available, waits up to 8-10 seconds before raising an error.
    """
    tmpEngine = create_engine(settings.db_uri)
    maxTries = 5 if awaitConnection else 1
    for n in range(maxTries):
        try:
            with tmpEngine.connect() as conn:
                conn.execute("commit")
            return True
        except OperationalError as err:
            msg = f'database "{settings.db_name}" does not exist'
            if msg in str(err):
                print(f"{msg} (determined after {n+1} tries)")
                return False
            # an OperationalError with any other message is a real problem (e.g. db is not online yet)
            if n >= maxTries - 1:
                print(
                    f"\nERROR: giving up after {n+1} tries to connect to DB {settings.db_uri_print_safe}"
                )
                raise err
            time.sleep(2)


def createDb():
    """create initial database (supresses error if already exists)."""
    print(f"creating database '{settings.db_name}'...", end=" ")

    # https://stackoverflow.com/a/66361547/5500073
    # have to use form of URI that doesn't contain DB name (when it doesn't exist)
    tmpEngine = create_engine(settings._db_uri(omit_pass=False, include_db_name=False))

    db_params = {
        "host": settings.db_host,
        "port": settings.db_port,
        "user": settings.db_user,
        "password": settings.db_pass,
    }

    print(f"\nAttempting creation of database '{settings.db_name}'...")

    # Connect to the PostgreSQL server using the existing 'master' user
    conn = psycopg2.connect(**db_params, database="postgres")
    conn.autocommit = True
    cursor = conn.cursor()

    # Create the database
    create_cmd = sql.SQL("CREATE DATABASE {};").format(sql.Identifier(settings.db_name))
    try:
        cursor.execute(create_cmd)
        # TODO: run  CREATE EXTENSION "uuid-ossp";
    except psycopg2.errors.DuplicateDatabase:
        print("(database already exists)", end=" ")
    finally:
        cursor.close()
        conn.close()


def deleteDb():
    """delete entire database (destructive)."""
    print(f"deleting database '{settings.db_name}'...", end=" ")
    tmpEngine = create_engine(settings.db_uri)
    with tmpEngine.connect() as conn:
        conn.execute("commit")
        conn.execute(f"DROP DATABASE {settings.db_name}")
    print("DONE!")


def createAllTables():
    """create all tables in database (for defined models)"""
    print(f"creating all tables in database '{settings.db_name}'...", end=" ")
    meta.create_all(engine)
    print("table list: {}", meta.sorted_tables)
    print("DONE!")


def deleteAllTables():
    """delete all tables in database"""
    print(
        f"deleting all tables in database '{settings.db_name}'...",
        end=" ",
        flush=True,
    )

    # delete tables
    meta.drop_all(engine)
    print("DONE!")
