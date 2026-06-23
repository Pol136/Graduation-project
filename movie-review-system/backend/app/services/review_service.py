from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Review, ReviewAnalysis
from app.schemas.review import (
    ReviewAnalysisRead,
    ReviewCreate,
    ReviewReadWithAnalysis,
    ReviewUpdate,
)
from app.services.ml_client import analyze_review_with_ml
from app.services.movie_summary_service import recalculate_movie_summary

_MODEL_VERSION_MAX_LENGTH = 64


def get_review_by_id(db: Session, review_id: int) -> Review | None:
    return db.get(Review, review_id)


def get_review_with_analysis(db: Session, review_id: int) -> Review | None:
    return db.scalar(
        select(Review)
        .options(joinedload(Review.review_analysis))
        .where(Review.review_id == review_id)
    )


def get_review_by_user_and_movie(db: Session, user_id: int, movie_id: int) -> Review | None:
    return db.scalar(
        select(Review).where(
            Review.user_id == user_id,
            Review.movie_id == movie_id,
        )
    )


def get_reviews_by_movie(
    db: Session,
    movie_id: int,
    *,
    limit: int = 20,
    offset: int = 0,
) -> list[Review]:
    stmt = (
        select(Review)
        .options(joinedload(Review.user))
        .where(Review.movie_id == movie_id)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).unique().all())


def get_review_analysis_by_review_id(db: Session, review_id: int) -> ReviewAnalysis | None:
    return db.scalar(select(ReviewAnalysis).where(ReviewAnalysis.review_id == review_id))


def _truncate_model_version(model_version: str | None) -> str | None:
    if model_version is None:
        return None
    return model_version[:_MODEL_VERSION_MAX_LENGTH]


def _create_or_update_analysis(
    db: Session,
    review_id: int,
    ml_result: dict,
    existing: ReviewAnalysis | None = None,
) -> ReviewAnalysis:
    values = {
        "overall_sentiment": ml_result["overall_sentiment"],
        "predicted_rating": ml_result.get("predicted_rating"),
        "aspects": ml_result.get("aspects"),
        "model_version": _truncate_model_version(ml_result.get("model_version")),
    }
    if existing is not None:
        for key, value in values.items():
            setattr(existing, key, value)
        return existing

    analysis = ReviewAnalysis(review_id=review_id, **values)
    db.add(analysis)
    return analysis


def review_to_read_with_analysis(review: Review) -> ReviewReadWithAnalysis:
    analysis_read = None
    if review.review_analysis is not None:
        analysis = review.review_analysis
        analysis_read = ReviewAnalysisRead(
            analysis_id=analysis.analysis_id,
            review_id=analysis.review_id,
            overall_sentiment=analysis.overall_sentiment,
            predicted_rating=(
                float(analysis.predicted_rating)
                if analysis.predicted_rating is not None
                else None
            ),
            aspects=analysis.aspects,
            analyzed_at=analysis.analyzed_at,
            model_version=analysis.model_version,
        )
    return ReviewReadWithAnalysis(
        review_id=review.review_id,
        movie_id=review.movie_id,
        user_id=review.user_id,
        review_text=review.review_text,
        user_rating=float(review.user_rating),
        created_at=review.created_at,
        updated_at=review.updated_at,
        analysis=analysis_read,
    )


def create_review(
    db: Session,
    *,
    user_id: int,
    movie_id: int,
    payload: ReviewCreate,
) -> Review:
    review_text = payload.review_text.strip()
    user_rating = payload.user_rating

    ml_result = analyze_review_with_ml(review_text, user_rating)

    try:
        review = Review(
            user_id=user_id,
            movie_id=movie_id,
            review_text=review_text,
            user_rating=user_rating,
        )
        db.add(review)
        db.flush()

        _create_or_update_analysis(db, review.review_id, ml_result)
        db.flush()
        recalculate_movie_summary(db, movie_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_review_with_analysis(db, review.review_id)  # type: ignore[return-value]


def update_review(db: Session, review: Review, payload: ReviewUpdate) -> Review:
    final_review_text = (
        payload.review_text.strip() if payload.review_text is not None else review.review_text
    )
    final_user_rating = (
        payload.user_rating if payload.user_rating is not None else float(review.user_rating)
    )

    ml_result = analyze_review_with_ml(final_review_text, final_user_rating)

    try:
        review.review_text = final_review_text
        review.user_rating = final_user_rating

        existing_analysis = get_review_analysis_by_review_id(db, review.review_id)
        _create_or_update_analysis(db, review.review_id, ml_result, existing_analysis)
        db.flush()
        recalculate_movie_summary(db, review.movie_id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_review_with_analysis(db, review.review_id)  # type: ignore[return-value]


def delete_review(db: Session, review: Review) -> None:
    movie_id = review.movie_id
    try:
        if review.review_analysis is not None:
            db.delete(review.review_analysis)
        db.delete(review)
        db.flush()
        recalculate_movie_summary(db, movie_id)
        db.commit()
    except Exception:
        db.rollback()
        raise
