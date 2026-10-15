from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.schemas import UserRead
from app.models import User
from app.schemas import UserRead, UserUpdate
from app.deps import get_current_user
from app.database import get_db
from app.config import settings
from app.storage import process_avatar, InvalidImageError, save_avatar


router = APIRouter(tags=["users"])

@router.get("/users/me", response_model=UserRead)
def read_me(user:User = Depends(get_current_user)):
    return user

@router.patch("/users/me", response_model=UserRead)
def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # exclude_unset: only touch fields the app actually sent
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,  "No fields to update")
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/me.profile-pic", response_model=UserRead)
def upload_profile_pic(
    file: UploadFile = File(..., description="JPEG, PNG or WebP, max 5 MB"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = file.file.read(settings.avatar_max_bytes + 1)
    if len(data) > settings.avatar_max_bytes:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Image must be 5 MB or smaller")
    try:
        processed = process_avatar(data)
    except InvalidImageError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))

    old_key = user.avatar_key
    user.avatar_key = save_avatar(processed)