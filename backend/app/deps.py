from fastapi import Header, HTTPException, Depends
from typing_extensions import Annotated
from collections.abc import Generator
from .database import SessionFactory, engine
from sqlalchemy.orm import Session


# dummy function for now
async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


def get_db() -> Generator[Session, None, None]:
    with SessionFactory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
