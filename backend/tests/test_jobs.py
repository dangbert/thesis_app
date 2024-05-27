import jobRunner
from app.models.job import Job, JobStatus, JobType, AI_FEEDBACK_JOB_DATA
import tests.dummy as dummy
from app.routes.attempts import build_feedback_job_for_attempt
from app.hardcoded import SMARTData, FeedbackData


def test_pop_next_pending_job(session):
    """
    Test that the loop_once function correctly runs a job.
    """
    course, assignment, teacher, student = dummy.init_simple_course(session)

    pending = jobRunner.pop_next_pending_job(session)
    assert pending is None
    pending = jobRunner.pop_next_pending_job(session)
    assert pending is None

    attempt = dummy.make_attempt(session, assignment.id, student.id)
    job1 = Job(
        job_type=JobType.AI_FEEDBACK,
        status=JobStatus.PENDING,
        data=AI_FEEDBACK_JOB_DATA(attempt_id=attempt.id).custom_dump_dict(),
    )
    session.add(job1)
    session.commit()

    pending = jobRunner.pop_next_pending_job(session)

    # # Run the job
    # TODO: mock GPT API etc...
    job1.run(session)

    assert (
        jobRunner.pop_next_pending_job(session) is None
    ), "should be no pending jobs now"

    session.refresh(job1)
    assert job1.status == JobStatus.COMPLETED

    pending = jobRunner.pop_next_pending_job(session)
    assert pending is None, "should be no pending jobs"


# TODO: also test in test_attempts.py that creating an attempt also creates an associated job!


def test_ai_feedback_job(session):
    course, assignment, teacher, student = dummy.init_simple_course(session)

    attempt = dummy.make_attempt(session, assignment.id, student.id)
    job = build_feedback_job_for_attempt(attempt.id)
    session.add(job)
    session.commit()

    assert attempt.feedbacks == []

    job.run(session)
    # TODO: mock GPT call

    assert job.status == JobStatus.COMPLETED
    session.refresh(attempt)
    assert len(attempt.feedbacks) == 1
    feedback = attempt.feedbacks[0]

    assert feedback.is_ai and feedback.user_id is None

    feedback_data = FeedbackData(**feedback.data)  # should validate
