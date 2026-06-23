import pytest

from app.sentiment_analyzer import SentimentAnalyzer


class _Cfg:
    id2label = {0: "negative", 1: "neutral", 2: "positive"}


class _Model:
    config = _Cfg()


class _FakePipe:
    model = _Model()

    def __call__(self, chunk: str, **kwargs):  # noqa: ANN003, ARG002
        return [
            {"label": "LABEL_2", "score": 0.85},
            {"label": "LABEL_1", "score": 0.10},
            {"label": "LABEL_0", "score": 0.05},
        ]


def test_analyze_chunks_aggregates_label_ids(monkeypatch) -> None:
    monkeypatch.setattr("app.sentiment_analyzer.get_sentiment_pipeline", lambda: _FakePipe())
    sa = SentimentAnalyzer()
    r = sa.analyze_chunks(["Отличный фильм.", "Очень понравился."])
    assert r.sentiment == "positive"
    assert r.probabilities["positive"] == pytest.approx(0.85)
    assert r.score == pytest.approx(0.85)
