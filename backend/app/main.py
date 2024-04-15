from fastapi import FastAPI, APIRouter
from fastapi.routing import APIRoute
# TODO: consider using this https://github.com/tiangolo/full-stack-fastapi-template/blob/a230f4fb2ca0e341e74727bae695687f1ea124b0/backend/app/main.py
# from starlette.middleware.cors import CORSMiddleware

from app.routes import courses

api_router = APIRouter()
# api_router.include_router(courses.router, tags=["login"])
api_router.include_router(courses.router, prefix="/course", tags=["courses"])
# api_router.include_router(users.router, prefix="/user", tags=["user"])


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


API_V1_STR = "/api/v1"

app = FastAPI(
    title="thesis app",
    # openapi_url=f"{API_V1_STR}/openapi.json",
    # generate_unique_id_function=custom_generate_unique_id,
)
app.include_router(api_router, prefix=API_V1_STR)
