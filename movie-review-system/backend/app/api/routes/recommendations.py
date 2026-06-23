from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.recommendation import (
    RecommendationRead,
    RecommendationRunListItem,
    RecommendationRunRead,
)
from app.services import recommendation_service, user_preference_service

router = APIRouter()


def _to_recommendation_read(recommendation) -> RecommendationRead:
    return RecommendationRead.model_validate(recommendation)


@router.get("", response_model=list[RecommendationRead])
def get_recommendations(
    limit: int = Query(default=10, ge=1, le=100),
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[RecommendationRead]:
    user_preference_service.build_user_preference_profile(db, current_user.user_id)
    db.commit()

    if refresh:
        recommendations = recommendation_service.generate_recommendations(
            db, current_user.user_id, limit=limit
        )
    else:
        recommendations = recommendation_service.get_latest_recommendations(
            db, current_user.user_id
        )
        if not recommendations:
            recommendations = recommendation_service.generate_recommendations(
                db, current_user.user_id, limit=limit
            )

    return [_to_recommendation_read(item) for item in recommendations]


@router.post("/refresh", response_model=list[RecommendationRead])
def refresh_recommendations(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[RecommendationRead]:
    user_preference_service.build_user_preference_profile(db, current_user.user_id)
    db.commit()

    recommendations = recommendation_service.generate_recommendations(
        db, current_user.user_id, limit=limit
    )
    return [_to_recommendation_read(item) for item in recommendations]


@router.get("/runs", response_model=list[RecommendationRunListItem])
def list_recommendation_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[RecommendationRunListItem]:
    runs = recommendation_service.get_user_recommendation_runs(db, current_user.user_id)
    return [RecommendationRunListItem.model_validate(run) for run in runs]


@router.get("/runs/{run_id}", response_model=RecommendationRunRead)
def get_recommendation_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationRunRead:
    run = recommendation_service.get_recommendation_run(
        db, current_user.user_id, run_id
    )
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation run not found",
        )

    recommendations = recommendation_service.get_recommendations_for_run(db, run.run_id)
    return RecommendationRunRead(
        run_id=run.run_id,
        user_id=run.user_id,
        created_at=run.created_at,
        algorithm_version=run.algorithm_version,
        recommendations=[_to_recommendation_read(item) for item in recommendations],
    )
