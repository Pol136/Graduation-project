import pytest
from fastapi.testclient import TestClient

from tests.conftest import requires_db


def test_register_rejects_password_longer_than_72_characters(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "longpass@example.com",
            "password": "a" * 73,
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(
        err.get("loc") == ["body", "password"] and "72" in err.get("msg", "")
        for err in detail
    )


@requires_db
def test_user_registration(client: TestClient, unique_email: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": unique_email,
            "password": "securepass123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert data["username"] == "testuser"
    assert "user_id" in data
    assert "password_hash" not in data


@requires_db
def test_duplicate_email_registration(client: TestClient, unique_email: str) -> None:
    payload = {
        "username": "testuser",
        "email": unique_email,
        "password": "securepass123",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


@requires_db
def test_login_with_valid_credentials(client: TestClient, unique_email: str) -> None:
    password = "securepass123"
    client.post(
        "/api/auth/register",
        json={"username": "loginuser", "email": unique_email, "password": password},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"


@requires_db
def test_login_with_invalid_credentials(client: TestClient, unique_email: str) -> None:
    client.post(
        "/api/auth/register",
        json={
            "username": "loginuser",
            "email": unique_email,
            "password": "securepass123",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "wrong-password"},
    )
    assert response.status_code == 401


@requires_db
def test_get_current_user(client: TestClient, unique_email: str) -> None:
    password = "securepass123"
    client.post(
        "/api/auth/register",
        json={"username": "meuser", "email": unique_email, "password": password},
    )
    token = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    ).json()["access_token"]

    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == unique_email


@requires_db
def test_create_and_list_movies(client: TestClient) -> None:
    create_response = client.post(
        "/api/movies",
        json={
            "title": "Test Movie",
            "original_title": "Test Original",
            "description": "A test movie",
            "genres": ["Drama"],
            "release_year": 2020,
            "poster_url": "https://example.com/poster.jpg",
            "external_rating": 7.5,
        },
    )
    assert create_response.status_code == 201
    movie = create_response.json()
    assert movie["title"] == "Test Movie"
    movie_id = movie["movie_id"]

    list_response = client.get("/api/movies")
    assert list_response.status_code == 200
    assert any(item["movie_id"] == movie_id for item in list_response.json())

    get_response = client.get(f"/api/movies/{movie_id}")
    assert get_response.status_code == 200
    assert get_response.json()["movie_id"] == movie_id


@requires_db
def test_create_review_as_authenticated_user(
    client: TestClient, unique_email: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_reviews_ml import SAMPLE_ML_RESULT

    monkeypatch.setattr(
        "app.services.review_service.analyze_review_with_ml",
        lambda review_text, user_rating=None: SAMPLE_ML_RESULT.copy(),
    )
    password = "securepass123"
    client.post(
        "/api/auth/register",
        json={"username": "reviewer", "email": unique_email, "password": password},
    )
    token = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    ).json()["access_token"]

    movie_id = client.post(
        "/api/movies",
        json={"title": "Review Target Movie"},
    ).json()["movie_id"]

    response = client.post(
        f"/api/movies/{movie_id}/reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"review_text": "Great movie!", "user_rating": 8.5},
    )
    assert response.status_code == 201
    assert response.json()["review_text"] == "Great movie!"


@requires_db
def test_reject_duplicate_review(
    client: TestClient, unique_email: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_reviews_ml import SAMPLE_ML_RESULT

    monkeypatch.setattr(
        "app.services.review_service.analyze_review_with_ml",
        lambda review_text, user_rating=None: SAMPLE_ML_RESULT.copy(),
    )
    password = "securepass123"
    client.post(
        "/api/auth/register",
        json={"username": "dupreviewer", "email": unique_email, "password": password},
    )
    token = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    ).json()["access_token"]

    movie_id = client.post("/api/movies", json={"title": "Duplicate Review Movie"}).json()[
        "movie_id"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"review_text": "First review", "user_rating": 7.0}

    assert client.post(f"/api/movies/{movie_id}/reviews", headers=headers, json=payload).status_code == 201
    duplicate = client.post(f"/api/movies/{movie_id}/reviews", headers=headers, json=payload)
    assert duplicate.status_code == 400


@requires_db
def test_reject_review_without_auth(client: TestClient) -> None:
    movie_id = client.post("/api/movies", json={"title": "Auth Required Movie"}).json()[
        "movie_id"
    ]
    response = client.post(
        f"/api/movies/{movie_id}/reviews",
        json={"review_text": "Should fail", "user_rating": 6.0},
    )
    assert response.status_code == 401
