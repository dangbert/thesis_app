import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from starlette.responses import FileResponse
from app.deps import SessionDep, AuthUserDep
from app.settings import get_settings
from app.models.user import User
from app.models.course import (
    File as FileModel,
    FilePublic,
)
from uuid import UUID
from typing import Annotated

router = APIRouter()

FILE_NOT_FOUND = "File not found or not authorized"


def get_files_or_fail(
    session: SessionDep, file_ids: list[UUID], user: User, error_code: int = 404
) -> list[FileModel]:
    """Get's a list of file by ID(s), or raises a 404 if it doesn't exist or the user doesn't have access."""
    # file = session.query(FileModel).filter(FileModel.id == file_id).first()
    files = session.query(FileModel).filter(FileModel.id.in_(file_ids)).all()
    if len(files) != len(file_ids):
        raise HTTPException(status_code=error_code, detail=FILE_NOT_FOUND)

    for file in files:
        if not user.can_view(session, file):
            raise HTTPException(status_code=error_code, detail=FILE_NOT_FOUND)
    return files


# https://fastapi.tiangolo.com/tutorial/request-files/#uploadfile-with-additional-metadata
@router.put("/", status_code=201)
async def upload_file(
    user: AuthUserDep,
    file: UploadFile,
    session: SessionDep,
) -> FilePublic:
    Annotated[UploadFile, File(description="A file read as UploadFile")]
    settings = get_settings()

    if not file.filename:
        raise HTTPException(status_code=400, detail="expected a file upload")

    if "." not in file.filename:
        raise HTTPException(status_code=400, detail="no file extension in filename")
    ext = file.filename.split(".")[-1]
    db_file = FileModel(
        filename=file.filename,
        user_id=user.id,
        ext=ext,
    )
    session.add(db_file)
    session.commit()
    session.refresh(db_file)

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


@router.get("/{file_id}", response_class=FileResponse)
async def read_file(
    user: AuthUserDep, file_id: UUID, session: SessionDep
) -> FileResponse:
    db_file = get_files_or_fail(session, [file_id], user)[0]

    if not os.path.isfile(db_file.disk_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        db_file.disk_path,
        media_type="application/octet-stream",
        filename=db_file.filename,
    )
