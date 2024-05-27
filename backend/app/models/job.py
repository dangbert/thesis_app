from app.models.base import Base
import config
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import JSON, Integer, Enum
from typing import Optional, Any, Callable
from pydantic import BaseModel, ValidationError
import enum
from uuid import UUID
import json

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
        if self.status != JobStatus.IN_PROGRESS:
            logger.error(
                f"Job must be already have status '{JobStatus.IN_PROGRESS}' to run, not '{self.status}'"
            )
            return

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


from app.feedback import run_ai_feedback  # noqa: E402

JOB_RUN_MAP: dict[JobType, Callable[[Job, Session], None]] = {
    JobType.AI_FEEDBACK: run_ai_feedback,
}
