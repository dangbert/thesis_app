import jobRunner
from app.models.job import Job, JobStatus, JobType
import tests.dummy as dummy


# # Create a job


def test_get_next_pending_job(session):
    """
    Test that the loop_once function correctly runs a job.
    """
    course, assignment, student, teacher = dummy.init_simple_course(session)

    job = jobRunner.get_next_pending_job(session)
    assert job is None

    # job = Job(
    #     job_type=JobType.AI_FEEDBACK,
    #     status=JobStatus.PENDING,
    #     data={"attempt_id": dummy.DUMMY_ID},
    # )
    # session.add(job)
    # session.commit(

    # # Run the job
    # job.run()

    # session.refresh(job)
    # assert job.status == JobStatus.COMPLETED

    # # Check that the job is no longer pending
    # job = jobRunner.get_next_pending_job()
    # assert job is None
