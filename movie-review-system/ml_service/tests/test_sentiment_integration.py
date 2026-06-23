"""Optional end-to-end test against Hugging Face Hub (network + large deps)."""

import os

import pytest
from fastapi.testclient import TestClient

from app import model_loader as model_loader_module
from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.skipif(
    not os.environ.get("RUN_ML_INTEGRATION"),
    reason="Set RUN_ML_INTEGRATION=1 to download and run the real rubert-tiny model.",
)
def test_analyze_review_real_model_positive_russian(client: TestClient) -> None:
    model_loader_module.reset_sentiment_pipeline_for_tests()
    try:
        r = client.post(
            "/ml/analyze-review",
            json={
                "review_text": (
                    "Фильм очень понравился. Сюжет интересный, атмосфера сильная, "
                    "но местами немного затянуто."
                ),
                "user_rating": 8.0,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["overall_sentiment"] in ("positive", "neutral", "negative")
        assert 0.0 <= body["sentiment_score"] <= 1.0
        assert 1.0 <= body["predicted_rating"] <= 10.0
        assert body["aspects"] == []
        assert "+rating-" in body["model_version"]
        assert body["rating_comparison"]["predicted_rating"] == body["predicted_rating"]
    finally:
        model_loader_module.reset_sentiment_pipeline_for_tests()
