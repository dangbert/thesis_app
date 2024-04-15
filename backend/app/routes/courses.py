from fastapi import APIRouter, Depends, HTTPException
from app.deps import SessionDep
from app.models import Course

router = APIRouter()


@router.get("/")
async def list_courses(session: SessionDep):
    # query  all Course objects
    # courses = session.query(Course).all()
    # breakpoint()
    return
