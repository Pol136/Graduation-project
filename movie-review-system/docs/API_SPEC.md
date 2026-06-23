# API Specification

Base URL: `http://localhost:8000`

Authentication uses JWT bearer tokens:

```http
Authorization: Bearer <access_token>
```

OpenAPI docs: `http://localhost:8000/docs`

---

## Auth

### POST `/api/auth/register`

Register a new user.

**Request**

```json
{
  "username": "jane",
  "email": "jane@example.com",
  "password": "securepass123"
}
```

**Response `201`**

```json
{
  "user_id": 1,
  "username": "jane",
  "email": "jane@example.com",
  "created_at": "2026-05-18T12:00:00Z"
}
```

**Errors**

- `400` — email already registered
- `422` — validation error

**Example**

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"jane","email":"jane@example.com","password":"securepass123"}'
```

### POST `/api/auth/login`

Authenticate and receive a JWT access token.

**Request**

```json
{
  "email": "jane@example.com",
  "password": "securepass123"
}
```

**Response `200`**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors**

- `401` — invalid email or password

**Example**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"securepass123"}'
```

---

## Users

### GET `/api/users/me`

Return the currently authenticated user. Requires bearer token.

**Response `200`**

```json
{
  "user_id": 1,
  "username": "jane",
  "email": "jane@example.com",
  "created_at": "2026-05-18T12:00:00Z"
}
```

**Example**

```bash
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer <access_token>"
```

### GET `/api/users/me/preference-profile`

Return the current user's recommendation preference profile (built on demand). See [User preference profile](#user-preference-profile) for details.

---

## Movies

### GET `/api/movies`

List movies with pagination.

**Query parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | int | 20 | Page size (1–100) |
| `offset` | int | 0 | Offset |

**Response `200`**

```json
[
  {
    "movie_id": 1,
    "tmdb_id": 123,
    "title": "Movie title",
    "original_title": "Original title",
    "description": "Description",
    "genres": ["Drama", "Thriller"],
    "release_year": 2020,
    "poster_url": "https://example.com/poster.jpg",
    "external_rating": 7.8
  }
]
```

### GET `/api/movies/search`

Search movies by title or original title (case-insensitive partial match).

**Query parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `q` | string | required | Search query |
| `limit` | int | 20 | Page size |
| `offset` | int | 0 | Offset |

**Example**

```bash
curl "http://localhost:8000/api/movies/search?q=inception&limit=10"
```

### GET `/api/movies/{movie_id}`

Return a single movie by ID.

**Errors**

- `404` — movie not found

### POST `/api/movies`

Development endpoint for manually adding movies (TMDB import not implemented yet).

**Request**

```json
{
  "tmdb_id": 123,
  "title": "Movie title",
  "original_title": "Original title",
  "description": "Description",
  "genres": ["Drama", "Thriller"],
  "release_year": 2020,
  "poster_url": "https://example.com/poster.jpg",
  "external_rating": 7.8
}
```

**Response `201`** — created movie object

**Errors**

- `400` — duplicate `tmdb_id`

**Example**

```bash
curl -X POST http://localhost:8000/api/movies \
  -H "Content-Type: application/json" \
  -d '{"title":"Inception","release_year":2010,"genres":["Sci-Fi"]}'
```

---

## Reviews

### GET `/api/movies/{movie_id}/reviews`

List reviews for a movie, newest first. Includes reviewer username.

**Query parameters**

| Name | Type | Default |
|------|------|---------|
| `limit` | int | 20 |
| `offset` | int | 0 |

**Response `200`**

```json
[
  {
    "review_id": 1,
    "movie_id": 1,
    "user_id": 1,
    "username": "jane",
    "review_text": "Great movie!",
    "user_rating": 8.5,
    "created_at": "2026-05-18T12:00:00Z",
    "updated_at": "2026-05-18T12:00:00Z"
  }
]
```

**Errors**

- `404` — movie not found

### POST `/api/movies/{movie_id}/reviews`

Create a review for the authenticated user. One review per user per movie.

**Automatic ML pipeline**

1. Backend sends `review_text` and `user_rating` to the ML service (`POST /ml/analyze-review`).
2. On success, backend saves the review in `reviews` and ML output in `review_analysis`.
3. Backend recalculates `movie_summaries` for the movie.
4. Response includes embedded `analysis`.

If the ML service is unavailable, the request fails with `503` and **no** review row is created.

**Request**

```json
{
  "review_text": "Great movie!",
  "user_rating": 8.5
}
```

**Response `201`**

```json
{
  "review_id": 1,
  "movie_id": 1,
  "user_id": 1,
  "review_text": "Great movie!",
  "user_rating": 8.5,
  "created_at": "2026-05-18T12:00:00Z",
  "updated_at": "2026-05-18T12:00:00Z",
  "analysis": {
    "analysis_id": 1,
    "review_id": 1,
    "overall_sentiment": "positive",
    "predicted_rating": 8.4,
    "aspects": [
      {
        "aspect": "сюжет",
        "sentiment": "positive",
        "score": 0.82,
        "evidence": "Сюжет держит в напряжении."
      }
    ],
    "analyzed_at": "2026-05-18T12:00:00Z",
    "model_version": "sentiment-rubert-tiny-v1+rating-improved-baseline-v1"
  }
}
```

**Errors**

- `401` — not authenticated
- `404` — movie not found
- `400` — user already reviewed this movie
- `422` — validation error
- `502` — ML service returned invalid response or analysis failed
- `503` — ML service unavailable; review not saved

**Example**

```bash
curl -X POST http://localhost:8000/api/movies/1/reviews \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"review_text":"Great movie!","user_rating":8.5}'
```

### GET `/api/movies/{movie_id}/summary`

Return aggregated movie statistics from `movie_summaries`. Does not call the ML service.

**Query parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `refresh` | bool | false | If `true`, recalculates the summary from `reviews` and `review_analysis` before returning (fixes stale rows) |

If the movie exists but has no summary row yet, returns an empty summary (`review_count: 0`, zeroed sentiment distribution).

**Response `200`**

```json
{
  "summary_id": 1,
  "movie_id": 1,
  "average_user_rating": 8.5,
  "average_predicted_rating": 8.4,
  "review_count": 1,
  "sentiment_distribution": {
    "positive": 1,
    "neutral": 0,
    "negative": 0
  },
  "aspect_scores": {
    "сюжет": 0.82
  },
  "aspect_frequency": {
    "сюжет": 1
  },
  "updated_at": "2026-05-18T12:00:00Z"
}
```

**Errors**

- `404` — movie not found

### PATCH `/api/reviews/{review_id}`

Update own review (`review_text` and/or `user_rating`). Triggers full re-analysis via the ML service, updates `review_analysis`, and recalculates `movie_summaries`.

**Request**

```json
{
  "review_text": "Updated review text",
  "user_rating": 9.0
}
```

**Response `200`** — review with embedded `analysis` (same shape as create)

**Errors**

- `403` — not the review owner
- `404` — review not found
- `502` / `503` — ML errors (review is not updated on failure)

### DELETE `/api/reviews/{review_id}`

Delete own review. Removes associated `review_analysis` and recalculates `movie_summaries` for the movie (including zero-review empty state).

**Response `204`** — no content

**Errors**

- `403` — not the review owner
- `404` — review not found

### GET `/api/reviews/{review_id}/analysis`

Return stored ML analysis for a review. Public (no auth required).

**Response `200`**

```json
{
  "analysis_id": 1,
  "review_id": 1,
  "overall_sentiment": "positive",
  "predicted_rating": 8.4,
  "aspects": [
    {
      "aspect": "сюжет",
      "sentiment": "positive",
      "score": 0.82,
      "evidence": "Сюжет держит в напряжении."
    }
  ],
  "analyzed_at": "2026-05-18T12:00:00Z",
  "model_version": "sentiment-rubert-tiny-v1+rating-improved-baseline-v1"
}
```

**Errors**

- `404` — review or analysis not found

---

## Watchlist

All watchlist endpoints require authentication:

```http
Authorization: Bearer <access_token>
```

### GET `/api/watchlist`

Return the current user's watchlist, newest items first. Each entry includes full movie details.

**Response `200`**

```json
[
  {
    "watchlist_id": 1,
    "movie_id": 1,
    "added_at": "2026-05-18T12:00:00Z",
    "movie": {
      "movie_id": 1,
      "tmdb_id": 123,
      "title": "Movie title",
      "original_title": "Original title",
      "description": "Description",
      "genres": ["Drama", "Thriller"],
      "release_year": 2020,
      "poster_url": "https://example.com/poster.jpg",
      "external_rating": 7.8
    }
  }
]
```

**Errors**

- `401` — not authenticated

**Example**

```bash
curl http://localhost:8000/api/watchlist \
  -H "Authorization: Bearer <access_token>"
```

### POST `/api/watchlist/{movie_id}`

Add a movie to the current user's watchlist.

**Response `201`** — created watchlist item with embedded movie

**Errors**

- `401` — not authenticated
- `404` — movie not found
- `400` — movie already in watchlist (`"Movie is already in watchlist"`)

**Example**

```bash
curl -X POST http://localhost:8000/api/watchlist/1 \
  -H "Authorization: Bearer <access_token>"
```

### DELETE `/api/watchlist/{movie_id}`

Remove a movie from the current user's watchlist.

**Response `200`**

```json
{
  "message": "Movie removed from watchlist"
}
```

**Errors**

- `401` — not authenticated
- `404` — movie is not in the current user's watchlist

**Example**

```bash
curl -X DELETE http://localhost:8000/api/watchlist/1 \
  -H "Authorization: Bearer <access_token>"
```

---

## ML (backend proxy)

### GET `/api/ml/health`

Proxies the ML service health check (`GET /ml/health` on the ML service).

**Response `200`** — ML service health JSON (e.g. `status`, `service`, model load flags)

**Errors**

- `503` — ML service unavailable

**Example**

```bash
curl http://localhost:8000/api/ml/health
```

Configure the ML service URL with `ML_SERVICE_URL` (default `http://127.0.0.1:8001`).

---

## Recommendations

Recommendations are generated from user reviews, ML `review_analysis`, aggregated `movie_summaries`, watchlist items, and global movie quality signals (`external_rating`, summary ratings, sentiment).

- **New users** (no reviews, no watchlist) receive **cold-start** recommendations based on globally strong movies.
- Users with **watchlist only** use watchlist `movie_summaries` as **weak positive feedback** (half weight vs explicit reviews).
- **Reviewed movies** and **watchlist movies** are always excluded from results.
- Each generation creates a persisted **`recommendation_runs`** row and ranked **`recommendations`** rows.
- This MVP does **not** store textual explanations on recommendations.

All recommendation endpoints require authentication:

```http
Authorization: Bearer <access_token>
```

### GET `/api/recommendations`

Return recommendations for the current user.

**Query parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | int | 10 | Number of items (1–100) |
| `refresh` | bool | false | If `true`, always generate a new run |

**Behavior**

- Rebuilds/updates `user_preference_profiles` on each request.
- If `refresh=false` and a previous run exists, returns the latest run.
- If `refresh=false` and no run exists, generates a new run.
- If `refresh=true`, always generates a new run.
- Ordered by `rank_position` ascending.
- Returns `[]` when no candidate movies remain (not an error).

**Response `200`**

```json
[
  {
    "recommendation_id": 1,
    "run_id": 1,
    "user_id": 1,
    "movie_id": 5,
    "recommendation_score": 0.8125,
    "rank_position": 1,
    "created_at": "2026-05-18T12:00:00Z",
    "movie": {
      "movie_id": 5,
      "tmdb_id": null,
      "title": "Example Movie",
      "original_title": null,
      "description": null,
      "genres": ["Drama"],
      "release_year": 2020,
      "poster_url": null,
      "external_rating": 8.2
    }
  }
]
```

**Example**

```bash
curl "http://localhost:8000/api/recommendations?limit=10&refresh=true" \
  -H "Authorization: Bearer <access_token>"
```

### POST `/api/recommendations/refresh`

Always generate a new recommendation run.

**Query parameters**

| Name | Type | Default |
|------|------|---------|
| `limit` | int | 10 |

**Response `200`** — same shape as `GET /api/recommendations`

### GET `/api/recommendations/runs`

List the current user's recommendation runs, newest first.

**Response `200`**

```json
[
  {
    "run_id": 2,
    "user_id": 1,
    "created_at": "2026-05-18T13:00:00Z",
    "algorithm_version": "hybrid-mvp-v1"
  }
]
```

### GET `/api/recommendations/runs/{run_id}`

Return one run and its recommendations. Returns `404` if the run does not exist or belongs to another user.

**Response `200`**

```json
{
  "run_id": 1,
  "user_id": 1,
  "created_at": "2026-05-18T12:00:00Z",
  "algorithm_version": "hybrid-mvp-v1",
  "recommendations": []
}
```

---

## User preference profile

### GET `/api/users/me/preference-profile`

Return the current user's preference profile. If none exists, builds a default profile (empty positive/negative preferences, default aspect weights).

**Response `200`**

```json
{
  "profile_id": 1,
  "user_id": 1,
  "positive_preferences": {},
  "negative_preferences": {},
  "aspect_weights": {
    "сюжет": 0.25,
    "актерская игра": 0.15,
    "персонажи": 0.1,
    "визуальная составляющая": 0.15,
    "музыка": 0.1,
    "атмосфера": 0.1,
    "режиссура": 0.1,
    "темп повествования": 0.05
  },
  "updated_at": "2026-05-18T12:00:00Z"
}
```

**Example**

```bash
curl http://localhost:8000/api/users/me/preference-profile \
  -H "Authorization: Bearer <access_token>"
```

### Manual validation (recommendations)

**Scenario A — new user cold start**

1. Register and log in (no reviews, no watchlist).
2. `GET /api/users/me/preference-profile` → default profile.
3. `GET /api/recommendations?limit=10&refresh=true` → recommendations if movies exist; scores in `[0, 1]`.

**Scenario B — watchlist only**

1. Add 1–2 movies to watchlist.
2. `GET /api/recommendations?limit=10&refresh=true` → watchlist movies excluded; profile may reflect weak watchlist signals when summaries exist.

**Scenario C — user with reviews**

1. Create reviews (with `review_analysis` and `movie_summaries`).
2. `GET /api/users/me/preference-profile` and `GET /api/recommendations?limit=10&refresh=true`.
3. Reviewed and watchlist movies excluded; run and ranks persisted.

**Database checks**

```sql
SELECT * FROM user_preference_profiles;
SELECT * FROM recommendation_runs ORDER BY created_at DESC LIMIT 5;
SELECT recommendation_id, run_id, user_id, movie_id, recommendation_score, rank_position
FROM recommendations
ORDER BY created_at DESC
LIMIT 20;
```

---

## Not implemented in this MVP step

| Area | Status |
|------|--------|
| TMDB import | Not implemented |

---

## Health

### GET `/health`

```json
{
  "status": "ok",
  "service": "backend"
}
```

---

## ML Service (`http://127.0.0.1:8001`)

Separate service invoked by review create/update. See `docs/ML_PIPELINE.md` for ML service API details.

### Manual validation (Windows)

1. Start ML service:

```cmd
cd C:\Users\polin\University\Diplom_project\movie-review-system\ml_service
.venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8001
```

2. Start backend (second terminal):

```cmd
cd C:\Users\polin\University\Diplom_project\movie-review-system\backend
set DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5433/movie_review_db
set ML_SERVICE_URL=http://127.0.0.1:8001
python -m uvicorn app.main:app --reload --port 8000
```

3. In Swagger (`http://localhost:8000/docs`): `GET /api/ml/health`, `POST /api/movies/{movie_id}/reviews`, `GET /api/reviews/{review_id}/analysis`, `GET /api/movies/{movie_id}/summary`, `PATCH /api/reviews/{review_id}`, `DELETE /api/reviews/{review_id}`.

4. Verify database:

```cmd
docker exec -it mrs-postgres psql -U postgres -d movie_review_db -c "SELECT review_id, user_id, movie_id, review_text, user_rating FROM reviews ORDER BY review_id DESC LIMIT 5;"
docker exec -it mrs-postgres psql -U postgres -d movie_review_db -c "SELECT analysis_id, review_id, overall_sentiment, predicted_rating, aspects, model_version FROM review_analysis ORDER BY analysis_id DESC LIMIT 5;"
docker exec -it mrs-postgres psql -U postgres -d movie_review_db -c "SELECT movie_id, average_user_rating, average_predicted_rating, review_count, sentiment_distribution, aspect_scores, aspect_frequency FROM movie_summaries ORDER BY updated_at DESC LIMIT 5;"
```

Expected: rows in `reviews`, `review_analysis`, and updated `movie_summaries`; `model_version` contains `rating-improved-baseline-v1`.
