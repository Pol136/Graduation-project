from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import MovieSummary, Review, ReviewAnalysis
from app.services.ml_client import MLServiceUnavailableError
from tests.conftest import requires_db

SAMPLE_ML_RESULT = {
    "overall_sentiment": "positive",
    "sentiment_score": 0.91,
    "predicted_rating": 8.4,
    "rating_comparison": {
        "user_rating": 8.5,
        "predicted_rating": 8.4,
        "difference": 0.1,
        "consistency": "consistent",
        "message": "Close match",
    },
    "aspects": [
        {
            "aspect": "сюжет",
            "sentiment": "positive",
            "score": 0.82,
            "evidence": "Сюжет держит в напряжении.",
        }
    ],
    "model_version": "sentiment-rubert-tiny-v1+rating-improved-baseline-v1",
}


@pytest.fixture
def mock_ml_analyze():
    with patch(
        "app.services.review_service.analyze_review_with_ml",
        return_value=SAMPLE_ML_RESULT.copy(),
    ) as mocked:
        yield mocked


@pytest.fixture
def mock_ml_health():
    with patch(
        "app.api.routes.ml.check_ml_health",
        return_value={"status": "ok", "service": "ml_service"},
    ) as mocked:
        yield mocked


def _register_and_login(client: TestClient, unique_email: str) -> str:
    password = "securepass123"
    client.post(
        "/api/auth/register",
        json={"username": "mluser", "email": unique_email, "password": password},
    )
    return client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    ).json()["access_token"]


@requires_db
def test_create_review_persists_analysis_and_summary(
    client: TestClient,
    unique_email: str,
    mock_ml_analyze,
) -> None:
    token = _register_and_login(client, unique_email)
    movie_id = client.post("/api/movies", json={"title": "ML Pipeline Movie"}).json()["movie_id"]

    response = client.post(
        f"/api/movies/{movie_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"review_text": "Отличный фильм, сюжет держит в напряжении.", "user_rating": 8.5},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["analysis"] is not None
    assert body["analysis"]["overall_sentiment"] == "positive"
    assert body["analysis"]["predicted_rating"] == 8.4
    assert "rating-improved-baseline-v1" in body["analysis"]["model_version"]

    review_id = body["review_id"]
    mock_ml_analyze.assert_called_once_with(
        "Отличный фильм, сюжет держит в напряжении.",
        8.5,
    )

    with SessionLocal() as db:
        review = db.get(Review, review_id)
        assert review is not None
        analysis = db.scalar(
            select(ReviewAnalysis).where(ReviewAnalysis.review_id == review_id)
        )
        assert analysis is not None
        assert analysis.overall_sentiment == "positive"
        assert float(analysis.predicted_rating) == 8.4
        assert analysis.aspects[0]["aspect"] == "сюжет"

        summary = db.scalar(select(MovieSummary).where(MovieSummary.movie_id == movie_id))
        assert summary is not None
        assert summary.review_count == 1
        assert float(summary.average_user_rating) == 8.5
        assert float(summary.average_predicted_rating) == 8.4
        assert summary.sentiment_distribution["positive"] == 1
        assert summary.aspect_scores["сюжет"] == 0.82
        assert summary.aspect_frequency["сюжет"] == 1


@requires_db
def test_duplicate_review_still_rejected(
    client: TestClient,
    unique_email: str,
    mock_ml_analyze,
) -> None:
    token = _register_and_login(client, unique_email)
    movie_id = client.post("/api/movies", json={"title": "Dup ML Movie"}).json()["movie_id"]
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"review_text": "First", "user_rating": 7.0}

    assert client.post(f"/api/movies/{movie_id}/reviews", headers=headers, json=payload).status_code == 201
    duplicate = client.post(f"/api/movies/{movie_id}/reviews", headers=headers, json=payload)
    assert duplicate.status_code == 400


@requires_db
def test_ml_unavailable_returns_503_and_no_review_created(
    client: TestClient,
    unique_email: str,
) -> None:
    token = _register_and_login(client, unique_email)
    movie_id = client.post("/api/movies", json={"title": "ML Down Movie"}).json()["movie_id"]

    with patch(
        "app.services.review_service.analyze_review_with_ml",
        side_effect=MLServiceUnavailableError("down"),
    ):
        response = client.post(
            f"/api/movies/{movie_id}/reviews",
            headers={"Authorization": f"Bearer {token}"},
            json={"review_text": "Should not persist", "user_rating": 6.0},
        )

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()

    with SessionLocal() as db:
        count = db.scalar(
            select(Review).where(
                Review.movie_id == movie_id,
                Review.review_text == "Should not persist",
            )
        )
        assert count is None


@requires_db
def test_patch_review_updates_analysis_and_summary(
    client: TestClient,
    unique_email: str,
    mock_ml_analyze,
) -> None:
    token = _register_and_login(client, unique_email)
    movie_id = client.post("/api/movies", json={"title": "Patch ML Movie"}).json()["movie_id"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        f"/api/movies/{movie_id}/reviews",
        headers=headers,
        json={"review_text": "Initial review", "user_rating": 7.0},
    ).json()
    review_id = created["review_id"]

    updated_ml = SAMPLE_ML_RESULT.copy()
    updated_ml["overall_sentiment"] = "neutral"
    updated_ml["predicted_rating"] = 6.0

    with patch(
        "app.services.review_service.analyze_review_with_ml",
        return_value=updated_ml,
    ):
        response = client.patch(
            f"/api/reviews/{review_id}",
            headers=headers,
            json={"review_text": "Updated review", "user_rating": 6.5},
        )

    assert response.status_code == 200
    assert response.json()["analysis"]["overall_sentiment"] == "neutral"
    assert response.json()["analysis"]["predicted_rating"] == 6.0

    with SessionLocal() as db:
        analysis = db.scalar(
            select(ReviewAnalysis).where(ReviewAnalysis.review_id == review_id)
        )
        assert analysis is not None
        assert analysis.overall_sentiment == "neutral"


@requires_db
def test_delete_review_recalculates_summary(
    client: TestClient,
    unique_email: str,
    mock_ml_analyze,
) -> None:
    token = _register_and_login(client, unique_email)
    movie_id = client.post("/api/movies", json={"title": "Delete ML Movie"}).json()["movie_id"]
    headers = {"Authorization": f"Bearer {token}"}

    review_id = client.post(
        f"/api/movies/{movie_id}/reviews",
        headers=headers,
        json={"review_text": "To delete", "user_rating": 8.0},
    ).json()["review_id"]

    delete_response = client.delete(f"/api/reviews/{review_id}", headers=headers)
    assert delete_response.status_code == 204

    summary_response = client.get(f"/api/movies/{movie_id}/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["review_count"] == 0
    assert summary["average_user_rating"] is None


@requires_db
def test_get_review_analysis_endpoint(
    client: TestClient,
    unique_email: str,
    mock_ml_analyze,
) -> None:
    token = _register_and_login(client, unique_email)
    movie_id = client.post("/api/movies", json={"title": "Analysis GET Movie"}).json()["movie_id"]
    review_id = client.post(
        f"/api/movies/{movie_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"review_text": "Analysis endpoint test", "user_rating": 9.0},
    ).json()["review_id"]

    response = client.get(f"/api/reviews/{review_id}/analysis")
    assert response.status_code == 200
    assert response.json()["review_id"] == review_id
    assert response.json()["overall_sentiment"] == "positive"


@requires_db
def test_get_movie_summary_endpoint(
    client: TestClient,
    unique_email: str,
    mock_ml_analyze,
) -> None:
    token = _register_and_login(client, unique_email)
    movie_id = client.post("/api/movies", json={"title": "Summary GET Movie"}).json()["movie_id"]

    empty_summary = client.get(f"/api/movies/{movie_id}/summary")
    assert empty_summary.status_code == 200
    assert empty_summary.json()["review_count"] == 0

    client.post(
        f"/api/movies/{movie_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"review_text": "Summary test", "user_rating": 8.0},
    )

    summary = client.get(f"/api/movies/{movie_id}/summary").json()
    assert summary["review_count"] == 1
    assert summary["average_user_rating"] == 8.0
    assert summary["average_predicted_rating"] == 8.4
    assert summary["sentiment_distribution"]["positive"] == 1
    assert summary["aspect_scores"]["сюжет"] == 0.82


@requires_db
def test_ml_health_endpoint(client: TestClient, mock_ml_health) -> None:
    response = client.get("/api/ml/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
