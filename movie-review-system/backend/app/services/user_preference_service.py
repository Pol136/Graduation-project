from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    MovieSummary,
    Review,
    ReviewAnalysis,
    UserPreferenceProfile,
    Watchlist,
)

DEFAULT_ASPECT_WEIGHTS: dict[str, float] = {
    "сюжет": 0.25,
    "актерская игра": 0.15,
    "персонажи": 0.10,
    "визуальная составляющая": 0.15,
    "музыка": 0.10,
    "атмосфера": 0.10,
    "режиссура": 0.10,
    "темп повествования": 0.05,
}

_NEUTRAL_RATING_WEIGHT = 0.25
_WATCHLIST_SIGNAL_WEIGHT = 0.5


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _default_profile_values() -> dict[str, Any]:
    return {
        "positive_preferences": {},
        "negative_preferences": {},
        "aspect_weights": dict(DEFAULT_ASPECT_WEIGHTS),
    }


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return dict(DEFAULT_ASPECT_WEIGHTS)
    return {name: round(value / total, 4) for name, value in weights.items()}


def _parse_review_aspects(aspects: object) -> list[tuple[str, str, float]]:
    if not isinstance(aspects, list):
        return []
    parsed: list[tuple[str, str, float]] = []
    for item in aspects:
        if not isinstance(item, dict):
            continue
        aspect_name = item.get("aspect")
        if not isinstance(aspect_name, str) or not aspect_name:
            continue
        sentiment = item.get("sentiment")
        if not isinstance(sentiment, str):
            sentiment = "neutral"
        score = _coerce_float(item.get("score"))
        if score is None:
            score = 1.0
        parsed.append((aspect_name, sentiment, score))
    return parsed


def _add_preference(
    preferences: dict[str, float],
    aspect: str,
    amount: float,
) -> None:
    if amount <= 0:
        return
    preferences[aspect] = round(preferences.get(aspect, 0.0) + amount, 4)


def _apply_review_signals(
    review: Review,
    analysis: ReviewAnalysis | None,
    positive_preferences: dict[str, float],
    negative_preferences: dict[str, float],
    aspect_mentions: dict[str, float],
) -> None:
    rating = _coerce_float(review.user_rating)
    sentiment = analysis.overall_sentiment if analysis is not None else None
    aspects = _parse_review_aspects(analysis.aspects if analysis is not None else None)

    is_strongly_positive = rating is not None and rating >= 7
    is_strongly_negative = rating is not None and rating <= 4
    is_neutral_rating = rating is not None and 5 <= rating <= 6

    positive_signal = is_strongly_positive or sentiment == "positive"
    negative_signal = is_strongly_negative or sentiment == "negative"

    for aspect_name, aspect_sentiment, aspect_score in aspects:
        aspect_mentions[aspect_name] += 1.0

        if is_neutral_rating:
            weak = _NEUTRAL_RATING_WEIGHT * aspect_score
            if aspect_sentiment == "positive":
                _add_preference(positive_preferences, aspect_name, weak)
            elif aspect_sentiment == "negative":
                _add_preference(negative_preferences, aspect_name, weak)
            continue

        if positive_signal and aspect_sentiment == "positive":
            _add_preference(positive_preferences, aspect_name, aspect_score)

        if negative_signal and aspect_sentiment == "negative":
            _add_preference(negative_preferences, aspect_name, aspect_score)


def _apply_watchlist_signals(
    summaries: list[MovieSummary],
    positive_preferences: dict[str, float],
    aspect_mentions: dict[str, float],
) -> None:
    for summary in summaries:
        aspect_scores = summary.aspect_scores
        if not isinstance(aspect_scores, dict):
            continue
        for aspect_name, raw_score in aspect_scores.items():
            if not isinstance(aspect_name, str) or not aspect_name:
                continue
            score = _coerce_float(raw_score)
            if score is None or score <= 0:
                continue
            aspect_mentions[aspect_name] += _WATCHLIST_SIGNAL_WEIGHT
            _add_preference(
                positive_preferences,
                aspect_name,
                score * _WATCHLIST_SIGNAL_WEIGHT,
            )


def has_meaningful_preferences(profile: UserPreferenceProfile) -> bool:
    positive = profile.positive_preferences if isinstance(profile.positive_preferences, dict) else {}
    negative = profile.negative_preferences if isinstance(profile.negative_preferences, dict) else {}
    if any(_coerce_float(value) and float(value) > 0 for value in positive.values()):
        return True
    if any(_coerce_float(value) and float(value) > 0 for value in negative.values()):
        return True
    return False


def build_user_preference_profile(db: Session, user_id: int) -> UserPreferenceProfile:
    reviews = list(
        db.scalars(select(Review).where(Review.user_id == user_id)).all()
    )
    review_ids = [review.review_id for review in reviews]
    analyses_by_review_id: dict[int, ReviewAnalysis] = {}
    if review_ids:
        analyses = db.scalars(
            select(ReviewAnalysis).where(ReviewAnalysis.review_id.in_(review_ids))
        ).all()
        analyses_by_review_id = {analysis.review_id: analysis for analysis in analyses}

    watchlist_items = list(
        db.scalars(
            select(Watchlist)
            .options(joinedload(Watchlist.movie))
            .where(Watchlist.user_id == user_id)
        ).unique().all()
    )
    watchlist_movie_ids = [item.movie_id for item in watchlist_items]
    summaries_by_movie_id: dict[int, MovieSummary] = {}
    if watchlist_movie_ids:
        summaries = db.scalars(
            select(MovieSummary).where(MovieSummary.movie_id.in_(watchlist_movie_ids))
        ).all()
        summaries_by_movie_id = {summary.movie_id: summary for summary in summaries}

    positive_preferences: dict[str, float] = {}
    negative_preferences: dict[str, float] = {}
    aspect_mentions: dict[str, float] = defaultdict(float)

    for review in reviews:
        analysis = analyses_by_review_id.get(review.review_id)
        _apply_review_signals(
            review,
            analysis,
            positive_preferences,
            negative_preferences,
            aspect_mentions,
        )

    watchlist_summaries = [
        summaries_by_movie_id[movie_id]
        for movie_id in watchlist_movie_ids
        if movie_id in summaries_by_movie_id
    ]
    _apply_watchlist_signals(
        watchlist_summaries,
        positive_preferences,
        aspect_mentions,
    )

    if aspect_mentions:
        aspect_weights = _normalize_weights(dict(aspect_mentions))
    else:
        aspect_weights = dict(DEFAULT_ASPECT_WEIGHTS)

    profile = db.scalar(
        select(UserPreferenceProfile).where(UserPreferenceProfile.user_id == user_id)
    )
    if profile is None:
        profile = UserPreferenceProfile(
            user_id=user_id,
            positive_preferences=positive_preferences,
            negative_preferences=negative_preferences,
            aspect_weights=aspect_weights,
        )
        db.add(profile)
    else:
        profile.positive_preferences = positive_preferences
        profile.negative_preferences = negative_preferences
        profile.aspect_weights = aspect_weights

    db.flush()
    return profile
