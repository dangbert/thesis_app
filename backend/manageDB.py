#!/usr/bin/env python3

import subprocess
import argparse
import app.database as database
from app.settings import Settings
from sqlalchemy.orm import close_all_sessions
from typing import Tuple

from config import get_logger

settings = Settings()  # type: ignore [call-arg]
logger = get_logger(__name__)


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
        logger.info("DB already exists!")
    else:
        database.create_db()

    if not createTables:
        return

    logger.info("creating tables...")
    database.create_all_tables
    logger.info("Done initializing database!")


def maybe_migrate():
    """
    Ensure database exists and is migrated to latest version.
    noop if settings.auto_migrate is False.
    """
    if not database.db_exists():
        init_db()

    if not settings.auto_migrate:
        logger.info("skipping DB migration check (auto_migrate disabled).")
        return

    exit_code, output = run_cmd("alembic upgrade head", exit_on_fail=False)
    if exit_code != 0:
        logger.error("DB upgrade failed!")
        exit(exit_code)
    logger.info(output)
    logger.info("***Database is at the latest version!***")


def destroy():
    if (
        input("Are you sure you want to delete the database? (yes/no) > ").lower()
        != "yes"
    ):
        logger.info("aborting...")
        return

    if not database.db_exists():
        logger.info("database already non-existent!")
        return

    close_all_sessions()
    database.delete_db()  # fails if any sessions are connected


def run_cmd(
    cmd: str, exit_on_fail: bool = True, verbose: bool = False, dry_run: bool = False
) -> Tuple[int, str]:
    """Runs a shell command, returns the exitcode and output."""
    if verbose or dry_run:
        logger.debug(f"{'running' if not dry_run else 'would run'} command: {cmd}")
    if dry_run:
        return -1, ""

    exitCode, output = subprocess.getstatusoutput(cmd)
    if exitCode != 0:
        logger.error(f"*** command failed with code {exitCode} ***")
        logger.error("cmd:")
        logger.error(cmd)
        logger.error("output:")
        logger.error(output)
        logger.error("*******************************************\n")
        if exit_on_fail:
            exit(exitCode)
    return exitCode, output


if __name__ == "__main__":
    main()
