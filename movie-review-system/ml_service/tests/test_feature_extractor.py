"""Unit tests for rating feature extraction."""

from app.feature_extractor import (
    ASPECT_NAME_MAP,
    build_rating_features,
    rating_feature_column_names,
)
from app.schemas import AspectSentiment
from app.sentiment_analyzer import SentimentResult


def test_rating_feature_columns_stable_order() -> None:
    cols = rating_feature_column_names()
    assert cols == rating_feature_column_names()
    assert cols[0] == "review_length_chars"
    assert len(cols) == len(set(cols))
    assert len([c for c in cols if c.startswith("aspect_plot_")]) == 5


def test_build_rating_features_numeric_and_stable_keys() -> None:
    text = "Сюжет отличный. Музыка слабая."
    sentiment = SentimentResult(
        sentiment="positive",
        score=0.8,
        probabilities={"positive": 0.8, "neutral": 0.15, "negative": 0.05},
    )
    aspects = [
        AspectSentiment(aspect="сюжет", sentiment="positive", score=0.9, evidence="Сюжет отличный."),
        AspectSentiment(aspect="музыка", sentiment="negative", score=0.7, evidence="Музыка слабая."),
    ]
    feats = build_rating_features(text, sentiment, aspects)
    assert list(feats.keys()) == rating_feature_column_names()
    assert all(isinstance(v, float) for v in feats.values())
    assert feats["sentiment_positive"] == 1.0
    assert feats["aspect_count"] == 2.0
    assert feats["aspect_plot_present"] == 1.0
    assert feats["aspect_plot_positive"] == 1.0
    assert feats["aspect_music_negative"] == 1.0
    assert feats["aspect_acting_present"] == 0.0
    assert len(ASPECT_NAME_MAP) == 9
