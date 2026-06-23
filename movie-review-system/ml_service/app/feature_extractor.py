"""
Numeric features for rating regression (sentiment, aspects, text length).

Used by the experimental Kinopoisk training pipeline only — not by active /ml/analyze-review.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from app.preprocessing import split_into_sentences

# Russian aspect label -> ASCII feature name suffix
ASPECT_NAME_MAP: dict[str, str] = {
    "сюжет": "plot",
    "актерская игра": "acting",
    "персонажи": "characters",
    "визуальная составляющая": "visuals",
    "музыка": "music",
    "атмосфера": "atmosphere",
    "режиссура": "directing",
    "темп повествования": "pace",
    "эмоциональное впечатление": "emotional_impression",
}

ASPECT_NORMALIZED_NAMES: tuple[str, ...] = tuple(ASPECT_NAME_MAP.values())

_BASE_FEATURE_NAMES: tuple[str, ...] = (
    "review_length_chars",
    "review_length_words",
    "sentence_count",
    "sentiment_score",
    "sentiment_positive",
    "sentiment_neutral",
    "sentiment_negative",
    "probability_positive",
    "probability_neutral",
    "probability_negative",
    "aspect_count",
    "positive_aspect_count",
    "neutral_aspect_count",
    "negative_aspect_count",
    "positive_aspect_ratio",
    "neutral_aspect_ratio",
    "negative_aspect_ratio",
)


def _aspect_feature_names() -> list[str]:
    names: list[str] = []
    for norm in ASPECT_NORMALIZED_NAMES:
        names.extend(
            [
                f"aspect_{norm}_present",
                f"aspect_{norm}_positive",
                f"aspect_{norm}_neutral",
                f"aspect_{norm}_negative",
                f"aspect_{norm}_score",
            ]
        )
    return names


def rating_feature_column_names() -> list[str]:
    """Stable feature column order for training and inference."""
    return list(_BASE_FEATURE_NAMES) + _aspect_feature_names()


def _sentiment_one_hot(sentiment: str) -> tuple[float, float, float]:
    s = (sentiment or "").lower()
    return (
        1.0 if s == "positive" else 0.0,
        1.0 if s == "neutral" else 0.0,
        1.0 if s == "negative" else 0.0,
    )


def _aspect_lookup(aspects: Sequence[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in aspects:
        label = getattr(item, "aspect", None) or (item.get("aspect") if isinstance(item, dict) else None)
        if label:
            out[str(label)] = item
    return out


def build_rating_features(
    text: str,
    sentiment_result: Any,
    aspects: Sequence[Any],
) -> dict[str, float]:
    """
    Build numeric features for rating prediction.

    Does not include user_rating, grade10, or baseline predicted_rating.
    """
    normalized = (text or "").strip()
    words = normalized.split()
    sentences = split_into_sentences(normalized) if normalized else []
    sentence_count = float(len(sentences)) if sentences else (1.0 if normalized else 0.0)

    sentiment = getattr(sentiment_result, "sentiment", None) or "neutral"
    sentiment_score = float(getattr(sentiment_result, "score", 0.0) or 0.0)
    probs: Mapping[str, float] = getattr(sentiment_result, "probabilities", None) or {}
    sp, sn, sg = _sentiment_one_hot(str(sentiment))
    prob_pos = float(probs.get("positive", 0.0))
    prob_neu = float(probs.get("neutral", 0.0))
    prob_neg = float(probs.get("negative", 0.0))

    aspect_list = list(aspects)
    aspect_count = float(len(aspect_list))
    pos_c = neu_c = neg_c = 0.0
    for a in aspect_list:
        s = getattr(a, "sentiment", None) or (a.get("sentiment") if isinstance(a, dict) else "neutral")
        if s == "positive":
            pos_c += 1.0
        elif s == "negative":
            neg_c += 1.0
        else:
            neu_c += 1.0
    denom = aspect_count if aspect_count > 0 else 1.0

    by_label = _aspect_lookup(aspect_list)
    values: dict[str, float] = {
        "review_length_chars": float(len(normalized)),
        "review_length_words": float(len(words)),
        "sentence_count": sentence_count,
        "sentiment_score": sentiment_score,
        "sentiment_positive": sp,
        "sentiment_neutral": sn,
        "sentiment_negative": sg,
        "probability_positive": prob_pos,
        "probability_neutral": prob_neu,
        "probability_negative": prob_neg,
        "aspect_count": aspect_count,
        "positive_aspect_count": pos_c,
        "neutral_aspect_count": neu_c,
        "negative_aspect_count": neg_c,
        "positive_aspect_ratio": pos_c / denom,
        "neutral_aspect_ratio": neu_c / denom,
        "negative_aspect_ratio": neg_c / denom,
    }

    for ru_label, norm in ASPECT_NAME_MAP.items():
        present = 0.0
        pos = neu = neg = 0.0
        score = 0.0
        if ru_label in by_label:
            a = by_label[ru_label]
            present = 1.0
            s = getattr(a, "sentiment", None) or (
                a.get("sentiment") if isinstance(a, dict) else "neutral"
            )
            score = float(getattr(a, "score", None) or (a.get("score") if isinstance(a, dict) else 0.0))
            if s == "positive":
                pos = 1.0
            elif s == "negative":
                neg = 1.0
            else:
                neu = 1.0
        values[f"aspect_{norm}_present"] = present
        values[f"aspect_{norm}_positive"] = pos
        values[f"aspect_{norm}_neutral"] = neu
        values[f"aspect_{norm}_negative"] = neg
        values[f"aspect_{norm}_score"] = score

    ordered: dict[str, float] = {}
    for key in rating_feature_column_names():
        ordered[key] = float(values.get(key, 0.0))
    return ordered


def features_to_row_vector(
    features: Mapping[str, float],
    column_names: Iterable[str],
) -> list[float]:
    """Align features to saved column order (missing keys -> 0)."""
    return [float(features.get(name, 0.0)) for name in column_names]
