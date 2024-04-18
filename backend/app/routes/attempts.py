from fastapi import APIRouter, Depends, HTTPException
from app.models.course import (
    Course,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
    Attempt,
    AttemptCreate,
    AttemptPublic,
)
from app.hardcoded import SMARTData

router = APIRouter()
