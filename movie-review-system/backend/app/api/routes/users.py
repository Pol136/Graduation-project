from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.recommendation import UserPreferenceProfileRead
from app.schemas.user import UserRead
from app.services import user_preference_service

router = APIRouter()


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_active_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("/me/preference-profile", response_model=UserPreferenceProfileRead)
def get_my_preference_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserPreferenceProfileRead:
    profile = user_preference_service.build_user_preference_profile(
        db, current_user.user_id
    )
    db.commit()
    db.refresh(profile)
    return UserPreferenceProfileRead.model_validate(profile)
