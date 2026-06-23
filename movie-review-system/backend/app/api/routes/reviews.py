from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.api.deps_ml import raise_http_for_ml_error
from app.db.database import get_db
from app.db.models import User
from app.schemas.review import ReviewAnalysisRead, ReviewReadWithAnalysis, ReviewUpdate
from app.services import review_service

router = APIRouter()


@router.get("/{review_id}/analysis", response_model=ReviewAnalysisRead)
def get_review_analysis(review_id: int, db: Session = Depends(get_db)) -> ReviewAnalysisRead:
    review = review_service.get_review_by_id(db, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    analysis = review_service.get_review_analysis_by_review_id(db, review_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return ReviewAnalysisRead(
        analysis_id=analysis.analysis_id,
        review_id=analysis.review_id,
        overall_sentiment=analysis.overall_sentiment,
        predicted_rating=(
            float(analysis.predicted_rating) if analysis.predicted_rating is not None else None
        ),
        aspects=analysis.aspects,
        analyzed_at=analysis.analyzed_at,
        model_version=analysis.model_version,
    )


@router.patch("/{review_id}", response_model=ReviewReadWithAnalysis)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReviewReadWithAnalysis:
    if payload.review_text is None and payload.user_rating is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one field must be provided",
        )

    review = review_service.get_review_by_id(db, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this review",
        )

    try:
        updated = review_service.update_review(db, review, payload)
    except Exception as exc:
        raise_http_for_ml_error(exc)

    return review_service.review_to_read_with_analysis(updated)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    review = review_service.get_review_with_analysis(db, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this review",
        )

    review_service.delete_review(db, review)
