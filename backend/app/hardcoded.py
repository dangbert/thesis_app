"""Hardcoded implementation details for the SMART goal specific use case of this thesis project."""

from pydantic import BaseModel


# these schemas must match frontend/apps/frontend/models.ts
class SMARTData(BaseModel):
    """A SMART goal and plan."""

    goal: str  # SMART goal formulation
    plan: str  # action plan


class FeedbackData(BaseModel):
    """Schema for validating the Feedback.data column."""

    feedback: str
    approved: bool


def email_can_signup(email: str):
    """Gatekeeper for email addresses that can sign up."""
    return email.endswith("@vu.nl") or email.endswith("@student.vu.nl")
