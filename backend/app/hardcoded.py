"""Hardcoded implementation details for the SMART goal specific use case of this thesis project."""

from pydantic import BaseModel


class SMARTData(BaseModel):
    """
    A SMART goal and plan.
    Must match frontend/apps/frontend/models.ts
    """

    goal: str  # SMART goal formulation
    plan: str  # action plan


def email_can_signup(email: str):
    """Gatekeeper for email addresses that can sign up."""
    return email.endswith("@vu.nl") or email.endswith("@student.vu.nl")
