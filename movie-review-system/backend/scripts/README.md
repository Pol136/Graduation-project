# Backend scripts

## `seed_fixed_tmdb_movies.py`

Deletes local `movie_id=1` (and related rows), then seeds or updates 100 movies from a fixed TMDB ID list (`tmdb_id` is the natural unique key).

### Windows (cmd)

```cmd
cd C:\Users\polin\University\Diplom_project\movie-review-system\backend
set DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5433/movie_review_db
set TMDB_API_KEY=your_key_here
set TMDB_BASE_URL=https://api.themoviedb.org/3
python scripts\seed_fixed_tmdb_movies.py
```

Skip deleting `movie_id=1`:

```cmd
python scripts\seed_fixed_tmdb_movies.py --skip-delete-movie-1
```

### Verification

```cmd
docker exec -it mrs-postgres psql -U postgres -d movie_review_db -c "SELECT COUNT(*) FROM movies;"

docker exec -it mrs-postgres psql -U postgres -d movie_review_db -c "SELECT movie_id, tmdb_id, title, release_year, external_rating FROM movies ORDER BY movie_id LIMIT 20;"

docker exec -it mrs-postgres psql -U postgres -d movie_review_db -c "SELECT movie_id, tmdb_id, title, release_year, external_rating FROM movies ORDER BY external_rating DESC NULLS LAST LIMIT 20;"
```

## `seed_movies_from_tmdb.py`

Older seed script with a shorter fixed ID list (no `movie_id=1` delete step).
