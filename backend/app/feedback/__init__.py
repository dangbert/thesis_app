"""Good for providing AI generated feedback to students."""

from sqlalchemy.orm import Session
from pydantic import ValidationError
import config

from .AbstractModel import AbstractModel, IPrompt, IConversation

logger = config.get_logger(__name__)


def run_ai_feedback(job: "Job", session: Session):
    """Generates AI feedback for a particular attempt."""

    try:
        data = AI_FEEDBACK_JOB_DATA(**job.data)  # noqa: F841
    except ValidationError as e:
        logger.error(f"Failed to parse data for {job}: {e}")
        job.status = JobStatus.FAILED
        job.error = "failed to parse data for job"
        session.commit()
        return

    # TODO: for now noop function and marking job completed
    job.status = JobStatus.COMPLETED
    session.commit()


from app.models.job import Job, JobStatus, AI_FEEDBACK_JOB_DATA  # noqa: E402
