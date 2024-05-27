from app.models.base import Base
from app.models.course import Attempt
import config
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import JSON, Integer, Enum
from typing import Optional, Any, Callable
from pydantic import BaseModel, ValidationError
import enum
from uuid import UUID
import json
import app.feedback as feedback
from app.hardcoded import SMARTData, FeedbackData

logger = config.get_logger(__name__)


class JobType(enum.Enum):
    AI_FEEDBACK = "AI_FEEDBACK"


class JobStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "job"

    job_type: Mapped[JobType]
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.PENDING
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    error: Mapped[Optional[str]]  # possible error description if job failed
    retries: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return f"<job id={self.id}, job_type={self.job_type}, status={self.status} />"

    def run(self, session: Session):
        if self.status != JobStatus.PENDING:
            logger.error(
                f"Job must be have status '{JobStatus.PENDING}' to run, not '{self.status}'"
            )
            return
        self.status = JobStatus.IN_PROGRESS
        session.commit()

        if self.job_type not in JOB_RUN_MAP:
            raise NotImplementedError(f"Job type '{self.job_type}' not implemented")

        JOB_RUN_MAP[self.job_type](self, session)


class AI_FEEDBACK_JOB_DATA(BaseModel):
    attempt_id: UUID

    class Config:
        json_encoders = {
            UUID: lambda uuid: str(uuid),  # Convert UUIDs to strings
        }

    def custom_dump_dict(self):
        # hack to avoid sqlalchemy.exc.StatementError: (builtins.TypeError) Object of type UUID is not JSON serializable
        return json.loads(json.dumps(self.dict(), default=str))


def _run_ai_feedback(job: Job, session: Session):
    """
    Generates AI feedback for a particular attempt, attaching a Feedback object.
    This is the crux of this project...
    """

    try:
        job_data = AI_FEEDBACK_JOB_DATA(**job.data)  # noqa: F841
    except ValidationError as e:
        logger.error(f"Failed to parse data for {job}: {e}")
        job.status = JobStatus.FAILED
        job.error = "failed to parse data for job"
        session.commit()
        return

    attempt_id = job_data.attempt_id
    attempt = session.query(Attempt).get(attempt_id)
    if attempt is None:
        logger.error(
            f"Attempt with id {attempt_id} not found but referenced in job {job}"
        )
        job.status = JobStatus.FAILED
        job.error = "attempt not found"
        session.commit()
        return

    try:
        smart_data = SMARTData(**attempt.data)
    except ValidationError as e:
        logger.error(f"Failed to parse data for attempt {attempt_id}: {e}")
        job.status = JobStatus.FAILED
        job.error = "failed to parse data for attempt"
        session.commit()
        return

    job.status = JobStatus.IN_PROGRESS
    session.commit()

    prompt = feedback.prompts.PROMPT_SMART_FEEDBACK_TEXT_ONLY.format(
        FEEDBACK_PRINCIPLES=feedback.prompts.FEEDBACK_PRINCIPLES,
        SMART_RUBRIC=feedback.prompts.SMART_RUBRIC,
        learning_goal=smart_data.goal,
        action_plan=smart_data.plan,
        language="Dutch",
    )

    # TODO: for now noop function and marking job completed
    job.status = JobStatus.COMPLETED
    session.commit()


JOB_RUN_MAP: dict[JobType, Callable[[Job, Session], None]] = {
    JobType.AI_FEEDBACK: _run_ai_feedback,
}
