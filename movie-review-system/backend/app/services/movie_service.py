from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Movie
from app.schemas.movie import MovieCreate


def get_movies(db: Session, *, limit: int = 20, offset: int = 0) -> list[Movie]:
    stmt = (
        select(Movie)
        .order_by(Movie.created_at.desc(), Movie.movie_id.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def search_movies(
    db: Session,
    query: str,
    *,
    limit: int = 20,
    offset: int = 0,
) -> list[Movie]:
    pattern = f"%{query}%"
    stmt = (
        select(Movie)
        .where(
            or_(
                Movie.title.ilike(pattern),
                Movie.original_title.ilike(pattern),
            )
        )
        .order_by(Movie.created_at.desc(), Movie.movie_id.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def get_movie_by_id(db: Session, movie_id: int) -> Movie | None:
    return db.get(Movie, movie_id)


def get_movie_by_tmdb_id(db: Session, tmdb_id: int) -> Movie | None:
    return db.scalar(select(Movie).where(Movie.tmdb_id == tmdb_id))


def create_movie(db: Session, payload: MovieCreate) -> Movie:
    movie = Movie(
        tmdb_id=payload.tmdb_id,
        title=payload.title,
        original_title=payload.original_title,
        description=payload.description,
        genres=payload.genres,
        release_year=payload.release_year,
        poster_url=payload.poster_url,
        external_rating=payload.external_rating,
    )
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie
