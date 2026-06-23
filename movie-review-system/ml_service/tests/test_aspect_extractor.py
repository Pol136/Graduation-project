"""Unit tests for aspect extraction (no Hugging Face download)."""

from unittest.mock import MagicMock

import pytest

from app.aspect_extractor import (
    ASPECT_KEYWORDS,
    _AspectCandidate,
    _keyword_aspects_for_sentence,
    _merge_aspect_candidates,
    extract_aspects,
)
from app.schemas import AspectSentiment
from app.sentiment_analyzer import SentimentResult


class _StubSentimentAnalyzer:
    def __init__(self, sentiment: str = "positive", score: float = 0.82) -> None:
        self.sentiment = sentiment
        self.score = score

    def analyze_text(self, text: str) -> SentimentResult:
        _ = text
        return SentimentResult(
            sentiment=self.sentiment,
            score=self.score,
            probabilities={"positive": self.score, "neutral": 0.1, "negative": 0.08},
        )


class _EmptyZeroShotPipe:
    def __call__(self, sentence: str, **kwargs):  # noqa: ANN003, ARG002
        _ = sentence
        return {"labels": ASPECT_KEYWORDS.keys(), "scores": [0.1] * len(ASPECT_KEYWORDS)}


def test_keyword_fallback_detects_sjuzhet(monkeypatch) -> None:
    monkeypatch.setattr("app.aspect_extractor.get_aspect_pipeline", lambda: _EmptyZeroShotPipe())
    aspects = extract_aspects(
        "Сюжет держит в напряжении до самого финала.",
        sentiment_analyzer=_StubSentimentAnalyzer(),
    )
    names = {a.aspect for a in aspects}
    assert "сюжет" in names
    assert aspects[0].evidence
    assert aspects[0].sentiment in ("positive", "neutral", "negative")
    assert 0.0 <= aspects[0].score <= 1.0


def test_keyword_aspects_for_sentence_music() -> None:
    found = _keyword_aspects_for_sentence("Музыка отлично поддерживает атмосферу.")
    assert "музыка" in found
    assert found["музыка"] >= 0.5


def test_merge_prefers_higher_sentiment_score() -> None:
    candidates = [
        _AspectCandidate("сюжет", "S1.", "neutral", 0.55),
        _AspectCandidate("сюжет", "S2.", "positive", 0.85),
    ]
    merged = _merge_aspect_candidates(candidates)
    assert len(merged) == 1
    assert merged[0].sentiment == "positive"
    assert merged[0].sentiment_score == 0.85


def test_merge_prefers_non_neutral_on_close_scores() -> None:
    candidates = [
        _AspectCandidate("музыка", "S1.", "neutral", 0.60),
        _AspectCandidate("музыка", "S2.", "negative", 0.62),
    ]
    merged = _merge_aspect_candidates(candidates)
    assert merged[0].sentiment == "negative"


def test_no_aspects_when_no_keywords_and_empty_zero_shot(monkeypatch) -> None:
    monkeypatch.setattr("app.aspect_extractor.get_aspect_pipeline", lambda: _EmptyZeroShotPipe())
    aspects = extract_aspects(
        "xyz qwerty",
        sentiment_analyzer=_StubSentimentAnalyzer(),
    )
    assert aspects == []


def test_zero_shot_labels_above_threshold(monkeypatch) -> None:
    class _ZsPipe:
        def __call__(self, sentence: str, **kwargs):  # noqa: ANN003, ARG002
            _ = sentence
            return {
                "labels": ["сюжет", "музыка"],
                "scores": [0.9, 0.1],
            }

    monkeypatch.setattr("app.aspect_extractor.get_aspect_pipeline", lambda: _ZsPipe())
    aspects = extract_aspects(
        "Текст без ключевых слов.",
        sentiment_analyzer=_StubSentimentAnalyzer(sentiment="neutral", score=0.7),
    )
    assert len(aspects) == 1
    assert aspects[0].aspect == "сюжет"
