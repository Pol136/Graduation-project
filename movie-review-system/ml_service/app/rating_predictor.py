"""
Rating prediction via interpretable improved baseline (active in /ml/analyze-review).

Trained regressor artifacts (rating_model_loader, training scripts) are experimental
and are not used by the active API pipeline.
"""

from __future__ import annotations

from typing import Any, Sequence


def _clip_rating(value: float) -> float:
    return round(max(1.0, min(10.0, value)), 1)


def _overall_sentiment_rating(sentiment: str, sentiment_score: float) -> float:
    s = max(0.0, min(1.0, float(sentiment_score)))
    if sentiment == "positive":
        return 7.0 + 3.0 * s
    if sentiment == "neutral":
        return 4.0 + 3.0 * s
    if sentiment == "negative":
        return 4.0 - 3.0 * s
    return 5.0


def _aspect_contribution(sentiment: str, score: float) -> float:
    s = max(0.0, min(1.0, float(score)))
    if sentiment == "positive":
        return 8.5 + 1.5 * s
    if sentiment == "neutral":
        return 5.0 + 1.0 * s
    if sentiment == "negative":
        return 4.0 - 3.0 * s
    return 5.0


def predict_rating_baseline(
    sentiment: str,
    sentiment_score: float,
    aspects: Sequence[Any],
) -> float:
    """
    Interpretable rating from overall sentiment, aspect sentiments, and balance adjustment.
    """
    overall_rating = _overall_sentiment_rating(sentiment, sentiment_score)

    if not aspects:
        aspect_rating = overall_rating
        positive_count = neutral_count = negative_count = 0
    else:
        contributions: list[float] = []
        positive_count = neutral_count = negative_count = 0
        for aspect in aspects:
            a_sent = getattr(aspect, "sentiment", None) or (
                aspect.get("sentiment") if isinstance(aspect, dict) else "neutral"
            )
            a_score = float(
                getattr(aspect, "score", None)
                or (aspect.get("score") if isinstance(aspect, dict) else 0.0)
            )
            contributions.append(_aspect_contribution(str(a_sent), a_score))
            if a_sent == "positive":
                positive_count += 1
            elif a_sent == "negative":
                negative_count += 1
            else:
                neutral_count += 1
        aspect_rating = sum(contributions) / len(contributions)

    total_aspect_count = positive_count + neutral_count + negative_count
    if total_aspect_count > 0:
        positive_ratio = positive_count / total_aspect_count
        negative_ratio = negative_count / total_aspect_count
    else:
        positive_ratio = 0.0
        negative_ratio = 0.0

    bonus = min(0.7, positive_ratio * 0.7)
    penalty = min(1.5, negative_ratio * 1.5)

    predicted = 0.55 * overall_rating + 0.45 * aspect_rating + bonus - penalty
    return _clip_rating(predicted)


def predict_rating_from_sentiment(sentiment: str, score: float) -> float:
    """Legacy helper: overall-sentiment component only (kept for compatibility)."""
    return _clip_rating(_overall_sentiment_rating(sentiment, score))


def predict_rating(
    text: str,
    sentiment_result: Any,
    aspects: Sequence[Any],
) -> tuple[float, str]:
    """
    Predict numeric rating 1–10 using the improved interpretable baseline.

    Returns (rating, ``"improved_baseline"``). Does not use trained regressor artifacts.
    """
    _ = text
    sentiment = str(getattr(sentiment_result, "sentiment", "neutral"))
    score = float(getattr(sentiment_result, "score", 0.5))
    rating = predict_rating_baseline(sentiment, score, aspects)
    return rating, "improved_baseline"
