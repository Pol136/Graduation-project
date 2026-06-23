"""
Delete local movie_id=1 (optional) and seed a fixed list of 100 TMDB movies.

Run from the backend directory:
    python scripts/seed_fixed_tmdb_movies.py
    python scripts/seed_fixed_tmdb_movies.py --skip-delete-movie-1
    python scripts/seed_fixed_tmdb_movies.py --language ru-RU
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy import delete, func, select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.core.config import settings  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.db.models import (  # noqa: E402
    Movie,
    MovieSummary,
    Recommendation,
    Review,
    ReviewAnalysis,
    Watchlist,
)

TMDB_MOVIE_IDS: list[int] = [
    550, 155, 272, 49026, 13, 680, 238, 240, 424, 497,
    278, 129, 769, 389, 120, 121, 122, 11, 1891, 1892,
    603, 604, 605, 157336, 27205, 24428, 299536, 299534, 19995, 76600,
    1726, 10138, 10195, 68721, 118340, 283995, 447365, 293660, 383498, 533535,
    634649, 429617, 315635, 324857, 569094, 76341, 786892, 78, 335984, 807,
    857, 98, 346, 372058, 496243, 637, 105, 77, 11324, 274,
    289, 194, 22, 58, 285, 597, 671, 672, 673, 674,
    675, 767, 12444, 12445, 475557, 414906, 346698, 872585, 361743, 744,
    694, 629, 562, 862, 863, 10193, 301528, 19913, 10681, 354912,
    102278, 1022789, 808, 809, 585, 12, 14160, 2062, 38757, 109445,
]

LANG_EN = "en-US"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
REQUEST_TIMEOUT_SECONDS = 15
TARGET_MOVIE_ID = 1


def dedupe_preserve_order(ids: list[int]) -> list[int]:
    seen: set[int] = set()
    unique: list[int] = []
    for tmdb_id in ids:
        if tmdb_id not in seen:
            seen.add(tmdb_id)
            unique.append(tmdb_id)
    return unique


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_release_year(release_date: str | None) -> int | None:
    if not release_date or len(release_date) < 4:
        return None
    try:
        return int(release_date[:4])
    except ValueError:
        return None


def normalize_external_rating(vote: object) -> float | None:
    if vote is None:
        return None
    try:
        value = round(float(vote), 1)
        return max(0.0, min(10.0, value))
    except (TypeError, ValueError):
        return None


def _strip_nonempty(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _genre_names(data: dict) -> list[str]:
    return [genre["name"] for genre in data.get("genres", []) if genre.get("name")]


def fetch_tmdb_movie(
    session: requests.Session,
    *,
    base_url: str,
    api_key: str,
    tmdb_id: int,
    language: str,
) -> dict | None:
    url = f"{base_url.rstrip('/')}/movie/{tmdb_id}"
    try:
        response = session.get(
            url,
            params={"api_key": api_key, "language": language},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"WARNING: TMDB request failed for tmdb_id={tmdb_id} ({language}): {exc}")
        return None


def primary_title_or_overview_missing(data: dict) -> bool:
    title = _strip_nonempty(data.get("title"))
    overview = _strip_nonempty(data.get("overview"))
    return title is None or overview is None


def merge_tmdb_responses(primary: dict, fallback: dict | None) -> tuple[dict, str]:
    fields_from_fallback: list[str] = []
    used_fallback = fallback is not None

    title = _strip_nonempty(primary.get("title"))
    if title is None and fallback:
        title = _strip_nonempty(fallback.get("title"))
        if title is not None:
            fields_from_fallback.append("title")
    if title is None:
        title = _strip_nonempty(primary.get("original_title"))
    if title is None and fallback:
        title = _strip_nonempty(fallback.get("original_title"))
        if title is not None:
            fields_from_fallback.append("original_title")
    if title is None:
        title = "Unknown"

    original_title = _strip_nonempty(primary.get("original_title"))
    if original_title is None and fallback:
        original_title = _strip_nonempty(fallback.get("original_title"))
        if original_title is not None:
            fields_from_fallback.append("original_title")

    description = _strip_nonempty(primary.get("overview"))
    if description is None and fallback:
        description = _strip_nonempty(fallback.get("overview"))
        if description is not None:
            fields_from_fallback.append("overview")

    genres_primary = _genre_names(primary)
    if genres_primary:
        genres: list[str] | None = genres_primary
    elif fallback:
        genres_fallback = _genre_names(fallback)
        if genres_fallback:
            genres = genres_fallback
            fields_from_fallback.append("genres")
        else:
            genres = None
    else:
        genres = None

    release_date = _strip_nonempty(primary.get("release_date"))
    if release_date is None and fallback:
        release_date = _strip_nonempty(fallback.get("release_date"))
        if release_date is not None:
            fields_from_fallback.append("release_date")

    poster_path = primary.get("poster_path")
    if not poster_path and fallback:
        poster_path = fallback.get("poster_path")
        if poster_path:
            fields_from_fallback.append("poster_path")

    vote = primary.get("vote_average")
    if vote is None and fallback:
        vote = fallback.get("vote_average")
        if vote is not None:
            fields_from_fallback.append("vote_average")

    movie_data = {
        "tmdb_id": primary["id"],
        "title": title,
        "original_title": original_title,
        "description": description,
        "genres": genres,
        "release_year": parse_release_year(release_date),
        "poster_url": f"{POSTER_BASE_URL}{poster_path}" if poster_path else None,
        "external_rating": normalize_external_rating(vote),
    }

    if not used_fallback:
        summary = "primary only"
    elif fields_from_fallback:
        summary = f"primary + en fallback ({', '.join(sorted(set(fields_from_fallback)))})"
    else:
        summary = "primary + en fetched (no field gaps)"

    return movie_data, summary


def load_movie_payload(
    http: requests.Session,
    *,
    base_url: str,
    api_key: str,
    tmdb_id: int,
    language: str,
) -> tuple[dict | None, str | None]:
    primary = fetch_tmdb_movie(
        http,
        base_url=base_url,
        api_key=api_key,
        tmdb_id=tmdb_id,
        language=language,
    )
    if primary is None:
        return None, None

    fallback: dict | None = None
    if primary_title_or_overview_missing(primary):
        fallback = fetch_tmdb_movie(
            http,
            base_url=base_url,
            api_key=api_key,
            tmdb_id=tmdb_id,
            language=LANG_EN,
        )

    return merge_tmdb_responses(primary, fallback)


def delete_movie_by_id(db, movie_id: int) -> dict[str, int]:
    """Delete one movie and related rows; return deleted row counts per table."""
    counts = {
        "review_analysis": 0,
        "reviews": 0,
        "movie_summaries": 0,
        "watchlist": 0,
        "recommendations": 0,
        "movies": 0,
    }

    movie = db.get(Movie, movie_id)
    if movie is None:
        return counts

    review_ids = db.scalars(
        select(Review.review_id).where(Review.movie_id == movie_id)
    ).all()
    if review_ids:
        result = db.execute(
            delete(ReviewAnalysis).where(ReviewAnalysis.review_id.in_(review_ids))
        )
        counts["review_analysis"] = result.rowcount or 0

    result = db.execute(delete(Review).where(Review.movie_id == movie_id))
    counts["reviews"] = result.rowcount or 0

    result = db.execute(delete(MovieSummary).where(MovieSummary.movie_id == movie_id))
    counts["movie_summaries"] = result.rowcount or 0

    result = db.execute(delete(Watchlist).where(Watchlist.movie_id == movie_id))
    counts["watchlist"] = result.rowcount or 0

    result = db.execute(delete(Recommendation).where(Recommendation.movie_id == movie_id))
    counts["recommendations"] = result.rowcount or 0

    result = db.execute(delete(Movie).where(Movie.movie_id == movie_id))
    counts["movies"] = result.rowcount or 0

    db.commit()
    return counts


def upsert_movie(db, movie_data: dict) -> tuple[str, str]:
    existing = db.scalar(select(Movie).where(Movie.tmdb_id == movie_data["tmdb_id"]))

    if existing is None:
        movie = Movie(**movie_data)
        db.add(movie)
        db.commit()
        db.refresh(movie)
        return "inserted", movie.title

    for field, value in movie_data.items():
        setattr(existing, field, value)
    db.commit()
    db.refresh(existing)
    return "updated", existing.title


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete movie_id=1 and seed 100 fixed TMDB movies."
    )
    parser.add_argument(
        "--skip-delete-movie-1",
        action="store_true",
        help="Skip deleting local movie_id=1 before seeding.",
    )
    parser.add_argument(
        "--language",
        default="ru-RU",
        help="Primary TMDB language (default: ru-RU).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tmdb_ids = dedupe_preserve_order(TMDB_MOVIE_IDS)

    print(f"Unique TMDB IDs to process: {len(tmdb_ids)} (from {len(TMDB_MOVIE_IDS)} listed)")

    base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    api_key = get_required_env("TMDB_API_KEY")

    db_url_display = settings.database_url.split("@")[-1]
    print(f"Database: {db_url_display}")
    print(f"TMDB base URL: {base_url}")
    print(f"Primary language: {args.language}")

    inserted = 0
    updated = 0
    failed = 0
    skipped = 0
    total_movies: int | None = None
    processed_lines: list[str] = []

    db = SessionLocal()
    http = requests.Session()

    try:
        if not args.skip_delete_movie_1:
            print()
            print("Deleting local movie_id=1 and related records...")
            movie_exists = db.get(Movie, TARGET_MOVIE_ID) is not None
            if movie_exists:
                counts = delete_movie_by_id(db, TARGET_MOVIE_ID)
                print(f"  movie_id={TARGET_MOVIE_ID} found: yes")
                print(f"  review_analysis deleted: {counts['review_analysis']}")
                print(f"  reviews deleted: {counts['reviews']}")
                print(f"  movie_summaries deleted: {counts['movie_summaries']}")
                print(f"  watchlist deleted: {counts['watchlist']}")
                print(f"  recommendations deleted: {counts['recommendations']}")
                print(f"  movies deleted: {counts['movies']}")
                print(f"  Confirmation: movie_id={TARGET_MOVIE_ID} deleted.")
            else:
                print(f"  movie_id={TARGET_MOVIE_ID} not found; skipping delete.")
        else:
            print()
            print("Skipping delete of movie_id=1 (--skip-delete-movie-1).")

        print()
        print(f"Seeding {len(tmdb_ids)} movies from TMDB...")

        for tmdb_id in tmdb_ids:
            movie_data, loc_summary = load_movie_payload(
                http,
                base_url=base_url,
                api_key=api_key,
                tmdb_id=tmdb_id,
                language=args.language,
            )
            if movie_data is None:
                failed += 1
                continue

            if not movie_data.get("title"):
                print(f"WARNING: skipped tmdb_id={tmdb_id} (empty title)")
                skipped += 1
                continue

            try:
                action, title = upsert_movie(db, movie_data)
            except Exception as exc:
                db.rollback()
                print(f"WARNING: failed to save tmdb_id={tmdb_id}: {exc}")
                failed += 1
                continue

            line = f"  [{action}] {title} (tmdb_id={tmdb_id}) — {loc_summary}"
            processed_lines.append(line)
            print(line)

            if action == "inserted":
                inserted += 1
            else:
                updated += 1

        total_movies = db.scalar(select(func.count()).select_from(Movie))
    finally:
        http.close()
        db.close()

    print()
    print("Seed complete.")
    print(f"  Inserted: {inserted}")
    print(f"  Updated:  {updated}")
    print(f"  Failed:   {failed}")
    print(f"  Skipped:  {skipped}")
    if total_movies is not None:
        print(f"  Total movies in database: {total_movies}")
    print("  Processed movies:")
    for line in processed_lines:
        print(line)


if __name__ == "__main__":
    main()
