"""HTTP contract tests for /ml routes."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app import model_loader as model_loader_module
from app import rating_model_loader as rating_loader_module
from app.main import app
from app.schemas import AnalyzeReviewResponse, AspectSentiment


@pytest.fixture(autouse=True)
def _reset_pipelines() -> None:
    model_loader_module.reset_sentiment_pipeline_for_tests()
    model_loader_module.reset_aspect_pipeline_for_tests()
    rating_loader_module.reset_rating_model_for_tests()
    yield
    model_loader_module.reset_sentiment_pipeline_for_tests()
    model_loader_module.reset_aspect_pipeline_for_tests()
    rating_loader_module.reset_rating_model_for_tests()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_ml_health(client: TestClient) -> None:
    r = client.get("/ml/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "ml_service"
    assert data["sentiment_model_loaded"] is False
    assert data["aspect_model_loaded"] is False
    assert data["rating_method"] == "improved_baseline"
    assert data["rating_model_available"] is False
    assert data["rating_model_loaded"] is False
    assert data["model_loaded"] is False
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


def test_health_does_not_load_models(client: TestClient, monkeypatch) -> None:
    sentiment_spy = MagicMock(side_effect=AssertionError("sentiment pipeline should not load on /ml/health"))
    aspect_spy = MagicMock(side_effect=AssertionError("aspect pipeline should not load on /ml/health"))
    rating_spy = MagicMock(side_effect=AssertionError("rating model should not load on /ml/health"))
    monkeypatch.setattr(model_loader_module, "get_sentiment_pipeline", sentiment_spy)
    monkeypatch.setattr(model_loader_module, "get_aspect_pipeline", aspect_spy)
    monkeypatch.setattr(rating_loader_module, "get_rating_model", rating_spy)
    r = client.get("/ml/health")
    assert r.status_code == 200
    sentiment_spy.assert_not_called()
    aspect_spy.assert_not_called()
    rating_spy.assert_not_called()


def test_health_model_loaded_flags_when_pipelines_cached(client: TestClient) -> None:
    class _P:
        model = None

    model_loader_module.set_sentiment_pipeline_for_tests(_P())
    model_loader_module.set_aspect_pipeline_for_tests(_P())
    r = client.get("/ml/health")
    data = r.json()
    assert data["sentiment_model_loaded"] is True
    assert data["aspect_model_loaded"] is True
    assert data["model_loaded"] is True


def test_analyze_review_with_stub_pipeline(client: TestClient, monkeypatch) -> None:
    class _Cfg:
        id2label = {0: "negative", 1: "neutral", 2: "positive"}

    class _Model:
        config = _Cfg()

    class _FakeSentimentPipe:
        model = _Model()

        def __call__(self, chunk: str, **kwargs):  # noqa: ANN003, ARG002
            return [
                {"label": "positive", "score": 0.9},
                {"label": "neutral", "score": 0.08},
                {"label": "negative", "score": 0.02},
            ]

    monkeypatch.setattr("app.sentiment_analyzer.get_sentiment_pipeline", lambda: _FakeSentimentPipe())
    monkeypatch.setattr("app.analyzer.extract_aspects", lambda text, sentiment_analyzer=None: [])
    get_rating_spy = MagicMock(side_effect=AssertionError("rating regressor must not load"))
    monkeypatch.setattr(rating_loader_module, "is_rating_model_available", lambda: True)
    monkeypatch.setattr(rating_loader_module, "get_rating_model", get_rating_spy)
    r = client.post(
        "/ml/analyze-review",
        json={
            "review_text": "Фильм очень понравился.",
            "user_rating": 8.0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["overall_sentiment"] == "positive"
    assert body["sentiment_score"] == pytest.approx(0.9)
    assert 1.0 <= body["predicted_rating"] <= 10.0
    assert body["rating_comparison"]["user_rating"] == 8.0
    assert body["rating_comparison"]["predicted_rating"] == body["predicted_rating"]
    assert body["rating_comparison"]["difference"] is not None
    assert body["aspects"] == []
    get_rating_spy.assert_not_called()
    assert "rating-improved-baseline-v1" in body["model_version"]
    assert "rating-regressor" not in body["model_version"]
    AnalyzeReviewResponse.model_validate(body)


def test_analyze_review_without_user_rating(client: TestClient, monkeypatch) -> None:
    class _FakePipe:
        model = type("M", (), {"config": type("C", (), {"id2label": {}})()})()

        def __call__(self, chunk: str, **kwargs):  # noqa: ANN003, ARG002
            return [
                {"label": "neutral", "score": 0.7},
                {"label": "positive", "score": 0.2},
                {"label": "negative", "score": 0.1},
            ]

    monkeypatch.setattr("app.sentiment_analyzer.get_sentiment_pipeline", lambda: _FakePipe())
    monkeypatch.setattr("app.analyzer.extract_aspects", lambda text, sentiment_analyzer=None: [])
    r = client.post("/ml/analyze-review", json={"review_text": "ok"})
    assert r.status_code == 200
    rc = r.json()["rating_comparison"]
    assert rc["user_rating"] is None
    assert rc["difference"] is None
    assert rc["consistency"] == "not_available"


def test_rejects_empty_review_text(client: TestClient) -> None:
    r = client.post("/ml/analyze-review", json={"review_text": ""})
    assert r.status_code == 422


def test_rejects_whitespace_only_review_text(client: TestClient, monkeypatch) -> None:
    class _FakePipe:
        model = None

        def __call__(self, chunk: str, **kwargs):  # noqa: ANN003, ARG002
            return [{"label": "neutral", "score": 1.0}]

    monkeypatch.setattr("app.sentiment_analyzer.get_sentiment_pipeline", lambda: _FakePipe())
    monkeypatch.setattr("app.analyzer.extract_aspects", lambda text, sentiment_analyzer=None: [])
    r = client.post("/ml/analyze-review", json={"review_text": "   \n"})
    assert r.status_code == 422


def test_rejects_user_rating_out_of_range(client: TestClient) -> None:
    for rating in (0.5, 10.5):
        r = client.post(
            "/ml/analyze-review",
            json={"review_text": "x", "user_rating": rating},
        )
        assert r.status_code == 422


def test_import_app_module() -> None:
    import app.main as main_module  # noqa: PLC0415

    assert main_module.app.title
