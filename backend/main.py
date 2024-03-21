from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, Query, Request
from typing import Annotated
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Handy middleware for tracking how long it takes to process every request.
    https://fastapi.tiangolo.com/tutorial/middleware/
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["x-process-time-secs"] = str(process_time)
    return response

@app.get("/")
async def root():
    return {"hello": "thesis"}

COURSES = {
    "wetenschap": {"1234567890"}
}

@app.get("/join")
#async def join(invite_code: str):
async def join(invite_code: Annotated[str, Query(min_length=10, max_length=10)]):
    for course, codes in COURSES.items():
        if invite_code in codes:
            return {"welcome": course}

    # 400 error
    raise HTTPException(status_code=400, detail="Invalid invite code")