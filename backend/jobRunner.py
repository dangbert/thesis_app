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

    with database.SessionFactory() as session:
        logger.info("Job runner started")
        while True:
            if not _loop_once(session):
                logger.debug("No jobs to run, sleeping...")
                time.sleep(10)


def _loop_once(session: Session) -> Job | None:
    job = pop_next_pending_job(session)
    if job is None:
        return None

    pending_job_count = (
        session.query(models.Job).filter(Job.status == JobStatus.PENDING).count()
    )
    logger.info(f"Running job: {job} (other pending jobs: {pending_job_count-1})")
    start_time = time.perf_counter()
    job.run(session)
    logger.info(f"job complete in {(time.perf_counter() - start_time):.3f} secs: {job}")
    return job


def pop_next_pending_job(session: Session) -> Job | None:
    """Get the next pending job to run."""
    job = session.query(models.Job).filter(Job.status == JobStatus.PENDING).first()
    return job


def signal_handler(signum):
    print(f"Received signal: {signum}, cleaning up...")
    # NOTE: could do any cleanup here
    sys.exit(0)


if __name__ == "__main__":
    main()
