from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import require_admin, require_analyst
from app.database.session import get_db
from app.models import User
from app.repositories import GroupRepository
from app.schemas import ErrorResponse, GroupResponse, UploadResponse
from app.services.chat_parser import ChatParserError
from app.services.upload_service import UploadService
from app.utils.file_validation import validate_upload_file
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "",
    response_model=UploadResponse,
    responses={
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
    summary="Upload and import WhatsApp chat export file",
)
async def upload_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    file: UploadFile = File(..., description="WhatsApp exported .txt chat file"),
    group_name: str = Form(..., min_length=1, max_length=255),
):
    content = await validate_upload_file(file)
    service = UploadService(db)

    try:
        group, count = await service.import_chat(content, group_name, current_user.id)
    except ChatParserError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return UploadResponse(group_id=group.id, group_name=group.group_name, message_count=count)


@router.get(
    "/groups",
    response_model=list[GroupResponse],
    summary="List all imported WhatsApp groups",
)
async def list_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
):
    groups = await GroupRepository(db).list_all()
    return groups
