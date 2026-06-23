# Database Schema (Planned)

PostgreSQL database: `movie_review_db`

## Tables

### users

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| email | VARCHAR UNIQUE | |
| username | VARCHAR UNIQUE | |
| hashed_password | VARCHAR | |
| created_at | TIMESTAMPTZ | |

### movies

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| title | VARCHAR | |
| year | INTEGER | nullable |
| genre | VARCHAR | nullable |
| description | TEXT | nullable |
| external_id | VARCHAR | IMDb/TMDB ref |
| created_at | TIMESTAMPTZ | |

### reviews

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| user_id | FK → users | |
| movie_id | FK → movies | |
| rating | DECIMAL | 0–10 |
| text | TEXT | |
| created_at | TIMESTAMPTZ | |

### review_analyses

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| review_id | FK → reviews | |
| overall_sentiment | VARCHAR | |
| confidence | FLOAT | |
| aspects | JSONB | ABSA results |
| analyzed_at | TIMESTAMPTZ | |

### watchlist_items

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL PK | |
| user_id | FK → users | |
| movie_id | FK → movies | |
| added_at | TIMESTAMPTZ | |

### user_preferences (future)

Stores aggregated taste vectors for recommendations.

---

Migrations: `backend/alembic/` (to be initialized with models).
