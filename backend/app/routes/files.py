from fastapi import APIRouter, HTTPException
from app.deps import SessionDep
from app.models.course import (
    Course,
    CourseCreate,
    CoursePublic,
    Assignment,
    AssignmentCreate,
    AssignmentPublic,
)
from uuid import UUID

router = APIRouter()
