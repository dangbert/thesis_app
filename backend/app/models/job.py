from app.models.base import Base
from app.models.course import Attempt, Feedback, AttemptFeedbackLink
import config
from app.settings import get_settings
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import JSON, Integer, Enum
from typing import Optional, Any, Callable
from pydantic import BaseModel, ValidationError
import enum
from uuid import UUID
import json
from app.hardcoded import SMARTData, FeedbackData
import app.feedback_utils as feedback_utils

logger = config.get_logger(__name__)
settings = get_settings()


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

    def custom_dump_dict(self):
        # hack to avoid sqlalchemy.exc.StatementError: (builtins.TypeError) Object of type UUID is not JSON serializable
        return json.loads(json.dumps(self.model_dump(), default=str))


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
    attempt = session.get(Attempt, attempt_id)
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

    prompt = feedback_utils.prompts.PROMPT_SMART_FEEDBACK_TEXT_ONLY.format(
        FEEDBACK_PRINCIPLES=feedback_utils.prompts.FEEDBACK_PRINCIPLES,
        SMART_RUBRIC=feedback_utils.prompts.SMART_RUBRIC,
        learning_goal=smart_data.goal,
        action_plan=smart_data.plan,
        language="Dutch",
    )

    gpt = feedback_utils.GPTModel(
        api_key=settings.openai_api_key, model_name=settings.gpt_model
    )
    outputs, meta = gpt(
        [prompt],
        max_tokens=settings.gpt_max_tokens,
        temperature=settings.gpt_temperature,
    )
    cost = gpt.compute_price(meta)
    logger.info(
        f"generated feedback for attempt {attempt.id}, cost=${cost:.5f}, {gpt.model_name=}"
    )

    feedback_data = FeedbackData(
        feedback=outputs[0],
        prompt=prompt,
        cost=cost,
        approved=False,  # only relevant for teacher feedback
    )
    ai_feedback = Feedback(
        attempt_id=attempt.id,
        user_id=None,
        is_ai=True,
        data=feedback_data.model_dump(),
    )
    session.add(ai_feedback)
    session.flush()  # need an ID
    session.add(AttemptFeedbackLink(attempt_id=attempt.id, feedback_id=ai_feedback.id))

    # TODO: for now noop function and marking job completed
    job.status = JobStatus.COMPLETED
    session.commit()
    logger.info(
        f"created feedback {ai_feedback.id} (length {len(feedback_data.feedback)})"
    )


JOB_RUN_MAP: dict[JobType, Callable[[Job, Session], None]] = {
    JobType.AI_FEEDBACK: _run_ai_feedback,
}
