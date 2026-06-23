"""Unit tests for improved interpretable rating baseline."""

from unittest.mock import MagicMock

import pytest

from app import rating_model_loader as rating_loader
from app.rating_predictor import predict_rating, predict_rating_baseline
from app.schemas import AspectSentiment
from app.sentiment_analyzer import SentimentResult


@pytest.fixture(autouse=True)
def _reset_rating_model() -> None:
    rating_loader.reset_rating_model_for_tests()
    yield
    rating_loader.reset_rating_model_for_tests()


def _aspect(sentiment: str, score: float) -> AspectSentiment:
    return AspectSentiment(
        aspect="сюжет",
        sentiment=sentiment,  # type: ignore[arg-type]
        score=score,
        evidence="фрагмент",
    )


def test_positive_sentiment_without_aspects_high_rating() -> None:
    r = predict_rating_baseline("positive", 0.9, [])
    assert r >= 8.0


def test_negative_sentiment_without_aspects_low_rating() -> None:
    r = predict_rating_baseline("negative", 0.9, [])
    assert r <= 3.0


def test_positive_overall_with_negative_aspects_lower_than_positive_only() -> None:
    only_positive = predict_rating_baseline("positive", 0.85, [_aspect("positive", 0.9)])
    mixed = predict_rating_baseline(
        "positive",
        0.85,
        [_aspect("positive", 0.9), _aspect("negative", 0.8)],
    )
    assert mixed < only_positive


def test_neutral_with_mixed_aspects_middle_range() -> None:
    r = predict_rating_baseline(
        "neutral",
        0.6,
        [
            _aspect("positive", 0.7),
            _aspect("negative", 0.7),
            _aspect("neutral", 0.6),
        ],
    )
    assert 4.0 <= r <= 8.0


def test_rating_always_in_range() -> None:
    cases = [
        ("positive", 1.0, [_aspect("positive", 1.0)] * 5),
        ("negative", 1.0, [_aspect("negative", 1.0)] * 5),
        ("neutral", 0.0, []),
    ]
    for sentiment, score, aspects in cases:
        r = predict_rating_baseline(sentiment, score, aspects)
        assert 1.0 <= r <= 10.0


def test_predict_rating_returns_improved_baseline_source() -> None:
    sentiment = SentimentResult(
        sentiment="positive",
        score=0.8,
        probabilities={"positive": 0.8, "neutral": 0.1, "negative": 0.1},
    )
    rating, source = predict_rating("текст", sentiment, [])
    assert source == "improved_baseline"
    assert 1.0 <= rating <= 10.0


def test_predict_rating_never_calls_trained_regressor(monkeypatch) -> None:
    get_model = MagicMock(side_effect=AssertionError("regressor must not load"))
    monkeypatch.setattr(rating_loader, "is_rating_model_available", lambda: True)
    monkeypatch.setattr(rating_loader, "get_rating_model", get_model)
    sentiment = SentimentResult(
        sentiment="neutral",
        score=0.5,
        probabilities={"positive": 0.2, "neutral": 0.5, "negative": 0.3},
    )
    rating, source = predict_rating("текст", sentiment, [])
    get_model.assert_not_called()
    assert source == "improved_baseline"
    assert 1.0 <= rating <= 10.0
