#!/usr/bin/env python3

import subprocess
import argparse
import app.database as database
from app.settings import Settings
from sqlalchemy.orm import close_all_sessions
from typing import Tuple

settings = Settings()


def main():
    parser = argparse.ArgumentParser(
        description="helper script to perform maintenance on the DB",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--init-db-empty",
        "-i",
        action="store_true",
        help="create initial DB without tables (useful for alembic)",
    )

    parser.add_argument(
        "-mm",
        "--maybe-migrate",
        action="store_true",
        help="ensure database is created and migrated to latest version (if ENV var AUTO_MIGRATE=1)",
    )
    parser.add_argument("--delete-db", action="store_true", help="delete DB and tables")
    args = parser.parse_args()

    if args.init_db_empty:
        init_db(createTables=False)
        exit(0)

    if args.maybe_migrate:
        maybe_migrate()
        exit(0)

    if args.delete_db:
        destroy()
        exit(0)

    parser.print_help()
    exit(1)


def init_db(createTables: bool = False):
    if database.db_exists():
        print("DB already exists!")
    else:
        database.create_db()

    if not createTables:
        return

    print("creating tables...")
    database.create_all_tables
    print("\nDone initializing database!")


def maybe_migrate():
    """
    Ensure database exists and is migrated to latest version.
    noop if settings.auto_migrate is False.
    """
    db_exists = database.db_exists()

    if not settings.auto_migrate:
        print(f"skipping DB migration check (auto_migrate disabled). {db_exists=}")
        return

    exitCode, output = run_cmd("alembic upgrade head", exitOnFail=False)
    if exitCode != 0:
        print("\nERROR: DB upgrade failed!")
        exit(exitCode)
    print(output)
    print("\n***Database is at the latest version!***\n")


def destroy():
    # prompt yes/no
    if (
        input("Are you sure you want to delete the database? (yes/no) > ").lower()
        != "yes"
    ):
        print("aborting...")
        return

    if not database.db_exists():
        print("database already non-existent!")
        return

    close_all_sessions()
    database.delete_db()  # fails if any sessions are connected


def run_cmd(
    cmd: str, exitOnFail: bool = True, verbose: bool = False, dryRun: bool = False
) -> Tuple[int, str]:
    """Runs a shell command, returns the exitcode and output."""
    if verbose or dryRun:
        print(f"\n{'running' if not dryRun else 'would run'} command:")
        print(cmd)
    if dryRun:
        return -1, ""

    exitCode, output = subprocess.getstatusoutput(cmd)
    if exitCode != 0:
        print(f"\n*** command failed with code {exitCode} ***")
        print("cmd:")
        print(cmd)
        print("output:")
        print(output)
        print(f"\n*******************************************")
        if exitOnFail:
            exit(exitCode)
    return exitCode, output


if __name__ == "__main__":
    main()
