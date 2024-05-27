"""Hardcoded implementation details for the SMART goal specific use case of this thesis project."""

from pydantic import BaseModel
from typing import Optional


# these schemas must match frontend/apps/frontend/models.ts
class SMARTData(BaseModel):
    """A SMART goal and plan."""

    goal: str  # SMART goal formulation
    plan: str  # action plan


class FeedbackData(BaseModel):
    """Schema for validating the Feedback.data column."""

    feedback: str
    prompt: Optional[str] = None  # prompt given to GPT model if any
    cost: float = 0.0  # GPT cost in USD (if any)
    other_comments: Optional[str] = None
    approved: bool  # whether the feedback is approved by the teacher
    score: Optional[int] = None
    eval_metrics: Optional["EvalMetrics"] = None


class EvalMetrics(BaseModel):
    """Evaluation metrics for AI feedback."""

    problems: list[str]


def email_can_signup(email: str):
    """Gatekeeper for email addresses that can sign up."""
    return email.endswith("@vu.nl") or email.endswith("@student.vu.nl")
