from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import MovieSummary, Review, ReviewAnalysis
from app.schemas.movie import MovieSummaryRead

_EMPTY_SENTIMENT_DISTRIBUTION = {"positive": 0, "neutral": 0, "negative": 0}
_VALID_SENTIMENTS = frozenset(_EMPTY_SENTIMENT_DISTRIBUTION)


def _empty_summary_values() -> dict[str, Any]:
    return {
        "average_user_rating": None,
        "average_predicted_rating": None,
        "review_count": 0,
        "sentiment_distribution": dict(_EMPTY_SENTIMENT_DISTRIBUTION),
        "aspect_scores": {},
        "aspect_frequency": {},
    }


def _coerce_score(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _average(values: list[float], *, decimals: int = 2) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), decimals)


def compute_summary_values(
    reviews: list[Review],
    analyses: list[ReviewAnalysis],
) -> dict[str, Any]:
    if not reviews:
        return _empty_summary_values()

    user_ratings = [
        float(review.user_rating)
        for review in reviews
        if review.user_rating is not None
    ]
    predicted_ratings = [
        float(analysis.predicted_rating)
        for analysis in analyses
        if analysis.predicted_rating is not None
    ]

    sentiment_distribution = dict(_EMPTY_SENTIMENT_DISTRIBUTION)
    for analysis in analyses:
        sentiment = analysis.overall_sentiment
        if sentiment in _VALID_SENTIMENTS:
            sentiment_distribution[sentiment] += 1

    score_sums: dict[str, float] = defaultdict(float)
    score_counts: dict[str, int] = defaultdict(int)
    aspect_frequency: dict[str, int] = defaultdict(int)

    for analysis in analyses:
        aspects = analysis.aspects
        if not isinstance(aspects, list):
            continue
        for item in aspects:
            if not isinstance(item, dict):
                continue
            aspect_name = item.get("aspect")
            if not isinstance(aspect_name, str) or not aspect_name:
                continue
            aspect_frequency[aspect_name] += 1
            score = _coerce_score(item.get("score"))
            if score is not None:
                score_sums[aspect_name] += score
                score_counts[aspect_name] += 1

    aspect_scores = {
        name: round(score_sums[name] / score_counts[name], 3)
        for name in score_counts
    }

    return {
        "average_user_rating": _average(user_ratings),
        "average_predicted_rating": _average(predicted_ratings),
        "review_count": len(reviews),
        "sentiment_distribution": sentiment_distribution,
        "aspect_scores": aspect_scores,
        "aspect_frequency": dict(aspect_frequency),
    }


def recalculate_movie_summary(db: Session, movie_id: int) -> MovieSummary:
    reviews = db.query(Review).filter(Review.movie_id == movie_id).all()
    summary = db.query(MovieSummary).filter(MovieSummary.movie_id == movie_id).one_or_none()

    if not reviews:
        values = _empty_summary_values()
        if summary is None:
            summary = MovieSummary(movie_id=movie_id, **values)
            db.add(summary)
        else:
            for key, value in values.items():
                setattr(summary, key, value)
        return summary

    review_ids = [review.review_id for review in reviews]
    analyses = (
        db.query(ReviewAnalysis)
        .filter(ReviewAnalysis.review_id.in_(review_ids))
        .all()
        if review_ids
        else []
    )

    values = compute_summary_values(reviews, analyses)

    if summary is None:
        summary = MovieSummary(movie_id=movie_id, **values)
        db.add(summary)
    else:
        for key, value in values.items():
            setattr(summary, key, value)

    return summary


def empty_summary_for_movie(movie_id: int) -> dict[str, Any]:
    values = _empty_summary_values()
    return {"movie_id": movie_id, "summary_id": None, "updated_at": None, **values}


def summary_to_read(summary: MovieSummary | None, movie_id: int) -> MovieSummaryRead:
    if summary is None:
        return MovieSummaryRead(**empty_summary_for_movie(movie_id))

    return MovieSummaryRead(
        summary_id=summary.summary_id,
        movie_id=summary.movie_id,
        average_user_rating=(
            float(summary.average_user_rating)
            if summary.average_user_rating is not None
            else None
        ),
        average_predicted_rating=(
            float(summary.average_predicted_rating)
            if summary.average_predicted_rating is not None
            else None
        ),
        review_count=summary.review_count,
        sentiment_distribution=summary.sentiment_distribution,
        aspect_scores=summary.aspect_scores,
        aspect_frequency=summary.aspect_frequency,
        updated_at=summary.updated_at,
    )
