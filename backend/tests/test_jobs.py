import jobRunner
from app.models.job import Job, JobStatus, JobType, AI_FEEDBACK_JOB_DATA
import tests.dummy as dummy


# # Create a job


def test_pop_next_pending_job(session):
    """
    Test that the loop_once function correctly runs a job.
    """
    course, assignment, student, teacher = dummy.init_simple_course(session)

    pending = jobRunner.pop_next_pending_job(session)
    assert pending is None
    pending = jobRunner.pop_next_pending_job(session)
    assert pending is None

    job1 = Job(
        job_type=JobType.AI_FEEDBACK,
        status=JobStatus.PENDING,
        data=dummy.EXAMPLE_AI_FEEDBACK_DATA.dict(),
    )
    session.add(job1)
    session.commit()

    pending = jobRunner.pop_next_pending_job(session)
    assert job1.status == JobStatus.IN_PROGRESS, "should been marked as in progress"
    assert (
        jobRunner.pop_next_pending_job(session) is None
    ), "should be no pending jobs now"

    # # Run the job
    # TODO: mock GPT API etc...
    job1.run(session)

    session.refresh(job1)
    assert job1.status == JobStatus.COMPLETED

    pending = jobRunner.pop_next_pending_job(session)
    assert pending is None, "should be no pending jobs"


# TODO: also test in test_attempts.py that creating an attempt also creates an associated job!
