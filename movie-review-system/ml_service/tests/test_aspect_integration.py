"""Optional integration test for real zero-shot aspect model."""

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
    reason="Set RUN_ML_INTEGRATION=1 to download and run real HF models.",
)
def test_analyze_review_detects_aspects_russian(client: TestClient) -> None:
    model_loader_module.reset_sentiment_pipeline_for_tests()
    model_loader_module.reset_aspect_pipeline_for_tests()
    try:
        r = client.post(
            "/ml/analyze-review",
            json={
                "review_text": (
                    "Фильм очень понравился. Сюжет держит в напряжении, "
                    "музыка отлично поддерживает атмосферу, но актерская игра местами слабая."
                ),
                "user_rating": 8.0,
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["overall_sentiment"] in ("positive", "neutral", "negative")
        assert isinstance(body["aspects"], list)
        if body["aspects"]:
            a0 = body["aspects"][0]
            assert "aspect" in a0 and "sentiment" in a0 and "score" in a0
    finally:
        model_loader_module.reset_sentiment_pipeline_for_tests()
        model_loader_module.reset_aspect_pipeline_for_tests()
