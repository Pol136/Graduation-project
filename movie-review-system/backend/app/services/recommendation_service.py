from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Movie,
    MovieSummary,
    Recommendation,
    RecommendationRun,
    Review,
    UserPreferenceProfile,
    Watchlist,
)
from app.services.user_preference_service import (
    build_user_preference_profile,
    has_meaningful_preferences,
)

ALGORITHM_VERSION = "hybrid-mvp-v1"
_NEUTRAL_SCORE = 0.5


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _round_score(value: float) -> float:
    return round(_clamp(value), 4)


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_rating_1_10(value: object) -> float:
    rating = _coerce_float(value)
    if rating is None:
        return _NEUTRAL_SCORE
    return _round_score((rating - 1.0) / 9.0)


def _sentiment_positive_ratio(distribution: object) -> float:
    if not isinstance(distribution, dict):
        return _NEUTRAL_SCORE
    positive = _coerce_float(distribution.get("positive")) or 0.0
    neutral = _coerce_float(distribution.get("neutral")) or 0.0
    negative = _coerce_float(distribution.get("negative")) or 0.0
    total = positive + neutral + negative
    if total <= 0:
        return _NEUTRAL_SCORE
    return _round_score(positive / total)


def _review_count_bonus(summary: MovieSummary | None) -> float:
    if summary is None:
        return 0.0
    review_count = summary.review_count or 0
    if review_count <= 0:
        return 0.0
    return _round_score(min(review_count / 20.0, 1.0))


def _safe_aspect_scores(summary: MovieSummary | None) -> dict[str, float]:
    if summary is None or not isinstance(summary.aspect_scores, dict):
        return {}
    scores: dict[str, float] = {}
    for aspect, raw_value in summary.aspect_scores.items():
        if not isinstance(aspect, str) or not aspect:
            continue
        score = _coerce_float(raw_value)
        if score is not None:
            scores[aspect] = score
    return scores


def _candidate_has_rating_signal(movie: Movie, summary: MovieSummary | None) -> bool:
    if _coerce_float(movie.external_rating) is not None:
        return True
    if summary is None:
        return False
    if _coerce_float(summary.average_user_rating) is not None:
        return True
    if _coerce_float(summary.average_predicted_rating) is not None:
        return True
    if (summary.review_count or 0) > 0:
        return True
    return False


def _cold_start_score(movie: Movie, summary: MovieSummary | None) -> float:
    external_rating_score = _normalize_rating_1_10(movie.external_rating)
    average_user_rating_score = _normalize_rating_1_10(
        summary.average_user_rating if summary is not None else None
    )
    average_predicted_rating_score = _normalize_rating_1_10(
        summary.average_predicted_rating if summary is not None else None
    )
    sentiment_score = _sentiment_positive_ratio(
        summary.sentiment_distribution if summary is not None else None
    )
    review_count_bonus = _review_count_bonus(summary)

    score = (
        0.35 * external_rating_score
        + 0.25 * average_user_rating_score
        + 0.20 * average_predicted_rating_score
        + 0.15 * sentiment_score
        + 0.05 * review_count_bonus
    )
    return _round_score(score)


def _aspect_match_score(
    profile: UserPreferenceProfile,
    summary: MovieSummary | None,
) -> float:
    aspect_weights = profile.aspect_weights
    if not isinstance(aspect_weights, dict) or not aspect_weights:
        return _NEUTRAL_SCORE

    positive_preferences = profile.positive_preferences
    negative_preferences = profile.negative_preferences
    if not isinstance(positive_preferences, dict):
        positive_preferences = {}
    if not isinstance(negative_preferences, dict):
        negative_preferences = {}

    movie_aspect_scores = _safe_aspect_scores(summary)
    if not movie_aspect_scores:
        return _NEUTRAL_SCORE

    contributions: list[float] = []
    for aspect, weight in aspect_weights.items():
        if not isinstance(aspect, str):
            continue
        aspect_weight = _coerce_float(weight)
        if aspect_weight is None or aspect_weight <= 0:
            continue
        movie_aspect_score = movie_aspect_scores.get(aspect)
        if movie_aspect_score is None:
            movie_aspect_score = _NEUTRAL_SCORE
        positive_pref = _coerce_float(positive_preferences.get(aspect)) or 0.0
        negative_pref = _coerce_float(negative_preferences.get(aspect)) or 0.0
        contribution = aspect_weight * movie_aspect_score * (
            1.0 + positive_pref - negative_pref
        )
        contributions.append(contribution)

    if not contributions:
        return _NEUTRAL_SCORE

    weight_sum = sum(
        _coerce_float(weight) or 0.0
        for weight in aspect_weights.values()
        if _coerce_float(weight) is not None
    )
    if weight_sum <= 0:
        return _NEUTRAL_SCORE

    return _round_score(sum(contributions) / weight_sum)


def _personalized_score(
    movie: Movie,
    summary: MovieSummary | None,
    profile: UserPreferenceProfile,
) -> float:
    rating_score = _normalize_rating_1_10(
        summary.average_user_rating if summary is not None and summary.average_user_rating is not None
        else movie.external_rating
    )
    predicted_rating_score = _normalize_rating_1_10(
        summary.average_predicted_rating if summary is not None else None
    )
    sentiment_score = _sentiment_positive_ratio(
        summary.sentiment_distribution if summary is not None else None
    )
    aspect_match = _aspect_match_score(profile, summary)

    score = (
        0.30 * rating_score
        + 0.25 * predicted_rating_score
        + 0.20 * sentiment_score
        + 0.25 * aspect_match
    )
    return _round_score(score)


def _get_excluded_movie_ids(db: Session, user_id: int) -> set[int]:
    reviewed_ids = set(
        db.scalars(select(Review.movie_id).where(Review.user_id == user_id)).all()
    )
    watchlist_ids = set(
        db.scalars(select(Watchlist.movie_id).where(Watchlist.user_id == user_id)).all()
    )
    return reviewed_ids | watchlist_ids


def _load_summaries(db: Session, movie_ids: list[int]) -> dict[int, MovieSummary]:
    if not movie_ids:
        return {}
    summaries = db.scalars(
        select(MovieSummary).where(MovieSummary.movie_id.in_(movie_ids))
    ).all()
    return {summary.movie_id: summary for summary in summaries}


def _score_candidates(
    candidates: list[Movie],
    summaries_by_movie_id: dict[int, MovieSummary],
    profile: UserPreferenceProfile,
    *,
    use_personalized: bool,
) -> list[tuple[Movie, float]]:
    has_rating_signal = any(
        _candidate_has_rating_signal(movie, summaries_by_movie_id.get(movie.movie_id))
        for movie in candidates
    )

    scored: list[tuple[Movie, float]] = []
    for movie in candidates:
        summary = summaries_by_movie_id.get(movie.movie_id)
        if not has_rating_signal:
            score = _NEUTRAL_SCORE
        elif use_personalized:
            score = _personalized_score(movie, summary, profile)
        else:
            score = _cold_start_score(movie, summary)
        scored.append((movie, score))

    if not has_rating_signal:
        scored.sort(key=lambda item: (-item[0].created_at.timestamp(), item[0].movie_id))
    else:
        scored.sort(key=lambda item: (-item[1], item[0].movie_id))

    return scored


def _recommendations_with_movies(
    db: Session,
    recommendations: list[Recommendation],
) -> list[Recommendation]:
    if not recommendations:
        return []
    return list(
        db.scalars(
            select(Recommendation)
            .options(joinedload(Recommendation.movie))
            .where(
                Recommendation.recommendation_id.in_(
                    [item.recommendation_id for item in recommendations]
                )
            )
            .order_by(Recommendation.rank_position.asc())
        ).unique().all()
    )


def get_latest_recommendations(
    db: Session,
    user_id: int,
) -> list[Recommendation]:
    latest_run = db.scalar(
        select(RecommendationRun)
        .where(RecommendationRun.user_id == user_id)
        .order_by(RecommendationRun.created_at.desc())
        .limit(1)
    )
    if latest_run is None:
        return []

    recommendations = list(
        db.scalars(
            select(Recommendation)
            .options(joinedload(Recommendation.movie))
            .where(Recommendation.run_id == latest_run.run_id)
            .order_by(Recommendation.rank_position.asc())
        ).unique().all()
    )
    return recommendations


def get_user_recommendation_runs(
    db: Session,
    user_id: int,
) -> list[RecommendationRun]:
    return list(
        db.scalars(
            select(RecommendationRun)
            .where(RecommendationRun.user_id == user_id)
            .order_by(RecommendationRun.created_at.desc())
        ).all()
    )


def get_recommendation_run(
    db: Session,
    user_id: int,
    run_id: int,
) -> RecommendationRun | None:
    return db.scalar(
        select(RecommendationRun).where(
            RecommendationRun.run_id == run_id,
            RecommendationRun.user_id == user_id,
        )
    )


def get_recommendations_for_run(
    db: Session,
    run_id: int,
) -> list[Recommendation]:
    return list(
        db.scalars(
            select(Recommendation)
            .options(joinedload(Recommendation.movie))
            .where(Recommendation.run_id == run_id)
            .order_by(Recommendation.rank_position.asc())
        ).unique().all()
    )


def generate_recommendations(
    db: Session,
    user_id: int,
    limit: int = 10,
) -> list[Recommendation]:
    profile = build_user_preference_profile(db, user_id)
    use_personalized = has_meaningful_preferences(profile)

    excluded_ids = _get_excluded_movie_ids(db, user_id)
    candidate_stmt = select(Movie)
    if excluded_ids:
        candidate_stmt = candidate_stmt.where(~Movie.movie_id.in_(excluded_ids))
    candidates = list(db.scalars(candidate_stmt.order_by(Movie.movie_id.asc())).all())

    if not candidates:
        return []

    summaries_by_movie_id = _load_summaries(
        db, [movie.movie_id for movie in candidates]
    )
    scored_candidates = _score_candidates(
        candidates,
        summaries_by_movie_id,
        profile,
        use_personalized=use_personalized,
    )
    top_candidates = scored_candidates[:limit]

    run = RecommendationRun(
        user_id=user_id,
        algorithm_version=ALGORITHM_VERSION,
    )
    db.add(run)
    db.flush()

    saved: list[Recommendation] = []
    for rank_position, (movie, score) in enumerate(top_candidates, start=1):
        recommendation = Recommendation(
            run_id=run.run_id,
            user_id=user_id,
            movie_id=movie.movie_id,
            recommendation_score=score,
            rank_position=rank_position,
        )
        db.add(recommendation)
        saved.append(recommendation)

    db.commit()

    for recommendation in saved:
        db.refresh(recommendation)

    return _recommendations_with_movies(db, saved)
