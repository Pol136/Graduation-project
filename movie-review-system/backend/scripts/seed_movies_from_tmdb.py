"""
Seed the movies table from TMDB movie details (Russian locale, English fallback).

Run from the backend directory:
    python scripts/seed_movies_from_tmdb.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.core.config import settings  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.db.models import Movie  # noqa: E402

TMDB_MOVIE_IDS: list[int] = [
    550,  # Fight Club
    680,  # Pulp Fiction
    13,  # Forrest Gump
    155,  # The Dark Knight
    27205,  # Inception
    157336,  # Interstellar
    603,  # The Matrix
    238,  # The Godfather
    278,  # The Shawshank Redemption
    122,  # The Lord of the Rings: The Return of the King
    120,  # The Lord of the Rings: The Fellowship of the Ring
    121,  # The Lord of the Rings: The Two Towers
    11,  # Star Wars
    1891,  # The Empire Strikes Back
    1892,  # Return of the Jedi
    424,  # Schindler's List
    769,  # GoodFellas
    807,  # Se7en
    497,  # The Green Mile
    274,  # The Silence of the Lambs
    77,  # Memento
    389,  # 12 Angry Men
    194,  # Amélie
    38,  # Eternal Sunshine of the Spotless Mind
    24428,  # The Avengers
    299536,  # Avengers: Infinity War
    299534,  # Avengers: Endgame
    19995,  # Avatar
    597,  # Titanic
    862,  # Toy Story
    129,  # Spirited Away
    372058,  # Your Name.
    150540,  # Inside Out
    98,  # Gladiator
    496243,  # Parasite
]

LANG_RU = "ru-RU"
LANG_EN = "en-US"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"
REQUEST_TIMEOUT_SECONDS = 15


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


def _strip_nonempty(value: str | None) -> str | None:
    if value is None:
        return None
    s = value.strip()
    return s if s else None


def _genre_names(data: dict) -> list[str]:
    return [g["name"] for g in data.get("genres", []) if g.get("name")]


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
        print(f"WARNING: TMDB request failed for movie_id={tmdb_id} ({language}): {exc}")
        return None


def russian_title_or_overview_missing(ru: dict) -> bool:
    title = _strip_nonempty(ru.get("title"))
    overview = _strip_nonempty(ru.get("overview"))
    return title is None or overview is None


def merge_tmdb_responses(ru: dict, en: dict | None) -> tuple[dict, str]:
    """
    Build Movie row fields from TMDB payloads. Prefer Russian; fill gaps from English.

    Returns (movie_data dict, localization summary for logging).
    """
    fields_from_en: list[str] = []
    used_en_request = en is not None

    # Title: Russian TMDB title, then English title, then original_title chain
    title = _strip_nonempty(ru.get("title"))
    if title is None and en:
        title = _strip_nonempty(en.get("title"))
        if title is not None:
            fields_from_en.append("title")
    if title is None:
        title = _strip_nonempty(ru.get("original_title"))
    if title is None and en:
        title = _strip_nonempty(en.get("original_title"))
        if title is not None:
            fields_from_en.append("original_title")
    if title is None:
        title = "Unknown"

    # Original title: canonical original from TMDB (same in both locales; prefer ru then en)
    original_title = _strip_nonempty(ru.get("original_title"))
    if original_title is None and en:
        original_title = _strip_nonempty(en.get("original_title"))
        if original_title is not None:
            fields_from_en.append("original_title")

    # Description / overview
    description = _strip_nonempty(ru.get("overview"))
    if description is None and en:
        description = _strip_nonempty(en.get("overview"))
        if description is not None:
            fields_from_en.append("overview")

    # Genres: Russian names first
    genres_ru = _genre_names(ru)
    genres: list[str] | None
    if genres_ru:
        genres = genres_ru
    elif en:
        genres_en = _genre_names(en)
        if genres_en:
            genres = genres_en
            fields_from_en.append("genres")
        else:
            genres = None
    else:
        genres = None

    # release_date, poster_path, vote_average: prefer ru, then en if missing
    release_date = _strip_nonempty(ru.get("release_date"))
    if release_date is None and en:
        release_date = _strip_nonempty(en.get("release_date"))
        if release_date is not None:
            fields_from_en.append("release_date")

    poster_path = ru.get("poster_path")
    if not poster_path and en:
        poster_path = en.get("poster_path")
        if poster_path:
            fields_from_en.append("poster_path")

    vote = ru.get("vote_average")
    if vote is None and en:
        vote = en.get("vote_average")
        if vote is not None:
            fields_from_en.append("vote_average")

    movie_data = {
        "tmdb_id": ru["id"],
        "title": title,
        "original_title": original_title,
        "description": description,
        "genres": genres,
        "release_year": parse_release_year(release_date),
        "poster_url": f"{POSTER_BASE_URL}{poster_path}" if poster_path else None,
        "external_rating": vote,
    }

    if not used_en_request:
        summary = "ru only"
    elif fields_from_en:
        summary = f"ru + en fallback ({', '.join(sorted(set(fields_from_en)))})"
    else:
        summary = "ru + en fetched (no field gaps)"

    return movie_data, summary


def load_movie_payloads(
    session: requests.Session,
    *,
    base_url: str,
    api_key: str,
    tmdb_id: int,
) -> tuple[dict | None, str | None]:
    """
    Fetch ru-RU, optionally en-US if Russian title or overview is missing.
    Returns (merged movie_data dict or None on hard failure, localization summary or None).
    """
    ru = fetch_tmdb_movie(
        session,
        base_url=base_url,
        api_key=api_key,
        tmdb_id=tmdb_id,
        language=LANG_RU,
    )
    if ru is None:
        return None, None

    en: dict | None = None
    if russian_title_or_overview_missing(ru):
        en = fetch_tmdb_movie(
            session,
            base_url=base_url,
            api_key=api_key,
            tmdb_id=tmdb_id,
            language=LANG_EN,
        )

    movie_data, summary = merge_tmdb_responses(ru, en)
    return movie_data, summary


def upsert_movie(db, movie_data: dict) -> tuple[str, str]:
    """Insert or update a movie. Returns (action, title)."""
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


def main() -> None:
    base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
    api_key = get_required_env("TMDB_API_KEY")

    inserted = 0
    updated = 0
    failed = 0
    processed_lines: list[str] = []

    print(f"Seeding movies from TMDB ({len(TMDB_MOVIE_IDS)} IDs), primary language: {LANG_RU}")
    print(f"Database: {settings.database_url.split('@')[-1]}")
    print(f"TMDB base URL: {base_url}")

    db = SessionLocal()
    http = requests.Session()

    try:
        for tmdb_id in TMDB_MOVIE_IDS:
            movie_data, loc_summary = load_movie_payloads(
                http,
                base_url=base_url,
                api_key=api_key,
                tmdb_id=tmdb_id,
            )
            if movie_data is None:
                failed += 1
                continue

            action, title = upsert_movie(db, movie_data)
            line = f"  [{action}] {title} (tmdb_id={tmdb_id}) — {loc_summary}"
            processed_lines.append(line)
            print(line)

            if action == "inserted":
                inserted += 1
            else:
                updated += 1
    finally:
        http.close()
        db.close()

    print()
    print("Seed complete.")
    print(f"  Inserted: {inserted}")
    print(f"  Updated:  {updated}")
    print(f"  Failed:   {failed}")
    print("  Processed movies:")
    for line in processed_lines:
        print(line)


if __name__ == "__main__":
    main()
