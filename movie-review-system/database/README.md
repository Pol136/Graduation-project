# Database

PostgreSQL configuration for the movie review system.

## Layout

- `init/` — SQL scripts run on first container start (via `docker-entrypoint-initdb.d`)
- `.env.example` — connection variables for local tooling

## Connection (Docker Compose)

| Variable | Default |
|----------|---------|
| Host | `localhost` (or `db` inside compose network) |
| Port | `5432` |
| User | `mrs_user` |
| Password | `mrs_password` |
| Database | `movie_review_db` |

URL: `postgresql://mrs_user:mrs_password@localhost:5432/movie_review_db`

Schema migrations are managed by Alembic in `backend/alembic/` (to be configured).

See [docs/DB_SCHEMA.md](../docs/DB_SCHEMA.md) for planned tables.
