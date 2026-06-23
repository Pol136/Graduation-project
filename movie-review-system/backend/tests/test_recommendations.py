import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import (
    MovieSummary,
    Recommendation,
    RecommendationRun,
    UserPreferenceProfile,
)
from app.services.user_preference_service import DEFAULT_ASPECT_WEIGHTS
from tests.conftest import requires_db
from tests.test_reviews_ml import SAMPLE_ML_RESULT


def _register_and_login(client: TestClient) -> tuple[str, int]:
    email = f"rec_{uuid.uuid4().hex}@example.com"
    password = "securepass123"
    user = client.post(
        "/api/auth/register",
        json={"username": "recuser", "email": email, "password": password},
    ).json()
    token = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    ).json()["access_token"]
    return token, user["user_id"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_movie(
    client: TestClient,
    *,
    title: str,
    external_rating: float | None = 8.0,
) -> int:
    payload: dict = {"title": title}
    if external_rating is not None:
        payload["external_rating"] = external_rating
    return client.post("/api/movies", json=payload).json()["movie_id"]


@requires_db
def test_new_user_gets_default_preference_profile(client: TestClient) -> None:
    token, _ = _register_and_login(client)
    response = client.get(
        "/api/users/me/preference-profile",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["positive_preferences"] == {}
    assert body["negative_preferences"] == {}
    assert body["aspect_weights"] == DEFAULT_ASPECT_WEIGHTS


@requires_db
def test_new_user_gets_cold_start_recommendations(client: TestClient) -> None:
    token, _ = _register_and_login(client)
    _create_movie(client, title="Cold Start Movie A", external_rating=9.0)
    _create_movie(client, title="Cold Start Movie B", external_rating=7.5)

    response = client.get(
        "/api/recommendations?limit=5&refresh=true",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) >= 1
    for item in recommendations:
        assert 0 <= item["recommendation_score"] <= 1
        assert item["rank_position"] >= 1
        assert item["movie"] is not None


@requires_db
def test_recommendation_run_is_created(client: TestClient) -> None:
    token, user_id = _register_and_login(client)
    _create_movie(client, title="Run Movie", external_rating=8.2)

    client.get(
        "/api/recommendations?limit=3&refresh=true",
        headers=_auth_headers(token),
    )

    with SessionLocal() as db:
        runs = list(
            db.scalars(
                select(RecommendationRun).where(RecommendationRun.user_id == user_id)
            ).all()
        )
        assert len(runs) == 1
        recommendations = list(
            db.scalars(
                select(Recommendation).where(Recommendation.run_id == runs[0].run_id)
            ).all()
        )
        assert len(recommendations) >= 1
        ranks = sorted(item.rank_position for item in recommendations)
        assert ranks == list(range(1, len(recommendations) + 1))


@requires_db
def test_reviewed_and_watchlist_movies_are_excluded(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.review_service.analyze_review_with_ml",
        lambda review_text, user_rating=None: SAMPLE_ML_RESULT.copy(),
    )
    token, _ = _register_and_login(client)
    reviewed_id = _create_movie(client, title="Reviewed Movie", external_rating=9.5)
    watchlist_id = _create_movie(client, title="Watchlist Movie", external_rating=9.0)
    candidate_id = _create_movie(client, title="Candidate Movie", external_rating=6.0)

    client.post(
        f"/api/watchlist/{watchlist_id}",
        headers=_auth_headers(token),
    )
    client.post(
        f"/api/movies/{reviewed_id}/reviews",
        headers=_auth_headers(token),
        json={"review_text": "Great film with strong plot.", "user_rating": 9.0},
    )

    response = client.get(
        "/api/recommendations?limit=10&refresh=true",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    movie_ids = {item["movie_id"] for item in response.json()}
    assert reviewed_id not in movie_ids
    assert watchlist_id not in movie_ids
    assert candidate_id in movie_ids


@requires_db
def test_watchlist_only_user_gets_recommendations(client: TestClient) -> None:
    token, user_id = _register_and_login(client)
    watchlist_id = _create_movie(client, title="Watchlist Only", external_rating=8.8)
    other_id = _create_movie(client, title="Other Movie", external_rating=7.0)

    client.post(
        f"/api/watchlist/{watchlist_id}",
        headers=_auth_headers(token),
    )

    with SessionLocal() as db:
        db.add(
            MovieSummary(
                movie_id=watchlist_id,
                average_user_rating=8.0,
                average_predicted_rating=7.8,
                review_count=3,
                sentiment_distribution={"positive": 2, "neutral": 1, "negative": 0},
                aspect_scores={"сюжет": 0.9, "актерская игра": 0.8},
                aspect_frequency={"сюжет": 2, "актерская игра": 1},
            )
        )
        db.commit()

    response = client.get(
        "/api/recommendations?limit=5&refresh=true",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    movie_ids = {item["movie_id"] for item in response.json()}
    assert watchlist_id not in movie_ids
    assert other_id in movie_ids

    profile_response = client.get(
        "/api/users/me/preference-profile",
        headers=_auth_headers(token),
    )
    assert profile_response.status_code == 200
    positive = profile_response.json()["positive_preferences"]
    assert positive.get("сюжет", 0) > 0


@requires_db
def test_latest_run_returned_when_refresh_false(client: TestClient) -> None:
    token, _ = _register_and_login(client)
    _create_movie(client, title="Stable Rec Movie", external_rating=8.0)

    first = client.get(
        "/api/recommendations?limit=3&refresh=true",
        headers=_auth_headers(token),
    ).json()
    second = client.get(
        "/api/recommendations?limit=3&refresh=false",
        headers=_auth_headers(token),
    ).json()

    assert first
    assert [item["recommendation_id"] for item in first] == [
        item["recommendation_id"] for item in second
    ]


@requires_db
def test_refresh_true_generates_new_run(client: TestClient) -> None:
    token, user_id = _register_and_login(client)
    _create_movie(client, title="Refresh Movie 1", external_rating=8.0)
    _create_movie(client, title="Refresh Movie 2", external_rating=7.0)

    client.get(
        "/api/recommendations?limit=3&refresh=true",
        headers=_auth_headers(token),
    )
    client.get(
        "/api/recommendations?limit=3&refresh=true",
        headers=_auth_headers(token),
    )

    with SessionLocal() as db:
        runs = list(
            db.scalars(
                select(RecommendationRun).where(RecommendationRun.user_id == user_id)
            ).all()
        )
        assert len(runs) == 2


@requires_db
def test_user_cannot_access_another_users_run(client: TestClient) -> None:
    token_a, _ = _register_and_login(client)
    token_b, _ = _register_and_login(client)
    _create_movie(client, title="Private Run Movie", external_rating=8.0)

    run_id = client.get(
        "/api/recommendations?limit=1&refresh=true",
        headers=_auth_headers(token_a),
    ).json()[0]["run_id"]

    response = client.get(
        f"/api/recommendations/runs/{run_id}",
        headers=_auth_headers(token_b),
    )
    assert response.status_code == 404


@requires_db
def test_no_candidate_movies_returns_empty_list(client: TestClient) -> None:
    token, _ = _register_and_login(client)
    only_movie = _create_movie(client, title="Only Movie", external_rating=9.0)

    client.post(
        f"/api/watchlist/{only_movie}",
        headers=_auth_headers(token),
    )
    client.post(
        f"/api/movies/{only_movie}/reviews",
        headers=_auth_headers(token),
        json={"review_text": "Only one movie reviewed.", "user_rating": 8.0},
    )

    response = client.get(
        "/api/recommendations?limit=10&refresh=true",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json() == []


@requires_db
def test_profile_is_created_or_updated(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.review_service.analyze_review_with_ml",
        lambda review_text, user_rating=None: SAMPLE_ML_RESULT.copy(),
    )
    token, user_id = _register_and_login(client)
    movie_id = _create_movie(client, title="Profile Movie", external_rating=8.0)

    client.get(
        "/api/users/me/preference-profile",
        headers=_auth_headers(token),
    )

    with SessionLocal() as db:
        profile = db.scalar(
            select(UserPreferenceProfile).where(UserPreferenceProfile.user_id == user_id)
        )
        assert profile is not None

    client.post(
        f"/api/movies/{movie_id}/reviews",
        headers=_auth_headers(token),
        json={"review_text": "Strong plot and acting.", "user_rating": 9.0},
    )

    updated = client.get(
        "/api/users/me/preference-profile",
        headers=_auth_headers(token),
    ).json()
    assert updated["positive_preferences"].get("сюжет", 0) > 0
