import uuid

from fastapi.testclient import TestClient

from tests.conftest import requires_db


def _register_and_login(client: TestClient) -> tuple[str, str]:
    email = f"watchlist_{uuid.uuid4().hex}@example.com"
    password = "securepass123"
    client.post(
        "/api/auth/register",
        json={"username": "watchlistuser", "email": email, "password": password},
    )
    token = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    ).json()["access_token"]
    return token, email


def test_get_watchlist_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/watchlist")
    assert response.status_code == 401


@requires_db
def test_post_watchlist_without_token_returns_401(client: TestClient) -> None:
    movie_id = client.post("/api/movies", json={"title": "Watchlist Auth Movie"}).json()[
        "movie_id"
    ]
    response = client.post(f"/api/watchlist/{movie_id}")
    assert response.status_code == 401


@requires_db
def test_watchlist_add_list_and_remove(client: TestClient) -> None:
    token, _ = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    movie_id = client.post("/api/movies", json={"title": "Watchlist Flow Movie"}).json()[
        "movie_id"
    ]

    add_response = client.post(f"/api/watchlist/{movie_id}", headers=headers)
    assert add_response.status_code == 201
    added = add_response.json()
    assert added["movie_id"] == movie_id
    assert added["movie"]["title"] == "Watchlist Flow Movie"
    assert "watchlist_id" in added
    assert "added_at" in added

    duplicate = client.post(f"/api/watchlist/{movie_id}", headers=headers)
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"] == "Movie is already in watchlist"

    list_response = client.get("/api/watchlist", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["movie_id"] == movie_id
    assert items[0]["movie"]["title"] == "Watchlist Flow Movie"

    delete_response = client.delete(f"/api/watchlist/{movie_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Movie removed from watchlist"

    delete_again = client.delete(f"/api/watchlist/{movie_id}", headers=headers)
    assert delete_again.status_code == 404


@requires_db
def test_add_nonexistent_movie_to_watchlist_returns_404(client: TestClient) -> None:
    token, _ = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/watchlist/999999999", headers=headers)
    assert response.status_code == 404
