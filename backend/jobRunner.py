#!/usr/bin/env python3
"""Executes pending jobs from the database in an infinite lop."""

import signal
import sys
import time
import app.database as database
import app.models as models
from app.models.job import Job, JobType, JobStatus
from app.settings import get_settings
import config
from sqlalchemy.orm import Session

settings = get_settings()
logger = config.get_logger(__name__)


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)  # Also handle Ctrl-C gracefully

    with database.get_session() as session:
        while True:
            if not _loop_once(session):
                logger.debug("No jobs to run, sleeping...")
                time.sleep(15)


def _loop_once(session: Session) -> Job | None:
    job = get_next_pending_job(session)
    if job is None:
        return None

    logger.info(f"Running job: {job}")
    job.run(session)
    return job


def get_next_pending_job(session: Session) -> Job | None:
    job = session.query(models.Job).filter(Job.status == JobStatus.PENDING).first()
    if job:
        job.status = JobStatus.IN_PROGRESS
        session.commit()
    return job


def signal_handler(signum):
    print(f"Received signal: {signum}, cleaning up...")
    # NOTE: could do any cleanup here
    sys.exit(0)


if __name__ == "__main__":
    main()
