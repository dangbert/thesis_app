"""Hardcoded implementation details for the SMART goal specific use case of this thesis project."""

from pydantic import BaseModel


class SMARTData(BaseModel):
    """A SMART goal and plan."""

    goal: str  # SMART goal formulation
    plan: str  # action plan
