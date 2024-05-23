from app.models.base import Base
import config
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import JSON, Integer
from typing import Optional, Any, Callable
from pydantic import BaseModel, ValidationError
import enum

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
    status: Mapped[JobStatus]
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    error: Mapped[Optional[str]]  # possible error description if job failed
    retries: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return f"<job id={self.id}, job_type={self.job_type}, status={self.status} />"

    def run(self, session: Session):
        if self.status != JobStatus.PENDING:
            logger.warning(
                f"Job must be in status 'pending' to run, not '{self.status}'"
            )
            return

        if self.job_type not in JOB_RUN_MAP:
            raise NotImplementedError(f"Job type '{self.job_type}' not implemented")

        JOB_RUN_MAP[self.job_type](self)


class AI_FEEDBACK_DATA(BaseModel):
    attempt_id: str


def _run_ai_feedback(job: Job):
    pass


JOB_RUN_MAP: dict[JobType, Callable] = {
    JobType.AI_FEEDBACK: _run_ai_feedback,
}
