from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.deps import SessionDep
from app.settings import get_settings
from app.models.course import (
    File as FileModel,
    FilePublic,
)
from uuid import UUID
from typing import Annotated

router = APIRouter()


# https://fastapi.tiangolo.com/tutorial/request-files/#uploadfile-with-additional-metadata
@router.put("/", status_code=201)
async def upload_file(
    file: UploadFile,
    # TODO: read user from cookies!
    user_id: Annotated[UUID, Form()],
    session: SessionDep,
) -> FilePublic:
    Annotated[UploadFile, File(description="A file read as UploadFile")]
    settings = get_settings()  # Retrieve settings containing file directory info

    if not file.filename:
        raise HTTPException(status_code=400, detail="expected a file upload")

    # Create a new file record in the database
    db_file = FileModel(
        filename=file.filename,
        user_id=user_id,  # Assuming user_id is provided as an argument or via authentication
        ext=file.filename.split(".")[-1],  # Extract file extension directly
    )
    session.add(db_file)
    session.commit()
    session.refresh(db_file)  # Refresh to get the auto-generated ID

    file_location = f"{settings.file_dir}/{db_file.id}.{db_file.ext}"

    try:
        # Write file to disk
        with open(file_location, "wb") as file_object:
            while content := await file.read(1024):  # Read chunks of 1024 bytes
                file_object.write(content)
        return db_file.to_public()

    except Exception as e:
        session.delete(db_file)
        session.commit()
        raise HTTPException(status_code=500, detail=str(e))
