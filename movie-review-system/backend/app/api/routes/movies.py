from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.api.deps_ml import raise_http_for_ml_error
from app.db.database import get_db
from app.db.models import MovieSummary, User
from app.schemas.movie import MovieCreate, MovieListItem, MovieRead, MovieSummaryRead
from app.schemas.review import ReviewCreate, ReviewReadWithAnalysis, ReviewWithUserRead
from app.services import movie_service, review_service
from app.services.movie_summary_service import recalculate_movie_summary, summary_to_read

router = APIRouter()


@router.get("", response_model=list[MovieListItem])
def list_movies(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[MovieListItem]:
    movies = movie_service.get_movies(db, limit=limit, offset=offset)
    return [MovieListItem.model_validate(movie) for movie in movies]


@router.get("/search", response_model=list[MovieListItem])
def search_movies(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[MovieListItem]:
    movies = movie_service.search_movies(db, q, limit=limit, offset=offset)
    return [MovieListItem.model_validate(movie) for movie in movies]


@router.get("/{movie_id}", response_model=MovieRead)
def get_movie(movie_id: int, db: Session = Depends(get_db)) -> MovieRead:
    movie = movie_service.get_movie_by_id(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")
    return MovieRead.model_validate(movie)


@router.post("", response_model=MovieRead, status_code=status.HTTP_201_CREATED)
def create_movie(payload: MovieCreate, db: Session = Depends(get_db)) -> MovieRead:
    if payload.tmdb_id is not None:
        existing = movie_service.get_movie_by_tmdb_id(db, payload.tmdb_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movie with this tmdb_id already exists",
            )

    movie = movie_service.create_movie(db, payload)
    return MovieRead.model_validate(movie)


@router.get("/{movie_id}/reviews", response_model=list[ReviewWithUserRead])
def list_movie_reviews(
    movie_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[ReviewWithUserRead]:
    movie = movie_service.get_movie_by_id(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    reviews = review_service.get_reviews_by_movie(db, movie_id, limit=limit, offset=offset)
    return [
        ReviewWithUserRead(
            review_id=review.review_id,
            movie_id=review.movie_id,
            user_id=review.user_id,
            username=review.user.username,
            review_text=review.review_text,
            user_rating=float(review.user_rating),
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
        for review in reviews
    ]


@router.get("/{movie_id}/summary", response_model=MovieSummaryRead)
def get_movie_summary(
    movie_id: int,
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> MovieSummaryRead:
    movie = movie_service.get_movie_by_id(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    if refresh:
        summary = recalculate_movie_summary(db, movie_id)
        db.commit()
        db.refresh(summary)
        return summary_to_read(summary, movie_id)

    summary = db.query(MovieSummary).filter(MovieSummary.movie_id == movie_id).one_or_none()
    return summary_to_read(summary, movie_id)


@router.post(
    "/{movie_id}/reviews",
    response_model=ReviewReadWithAnalysis,
    status_code=status.HTTP_201_CREATED,
)
def create_movie_review(
    movie_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ReviewReadWithAnalysis:
    movie = movie_service.get_movie_by_id(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    existing = review_service.get_review_by_user_and_movie(db, current_user.user_id, movie_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this movie",
        )

    try:
        review = review_service.create_review(
            db,
            user_id=current_user.user_id,
            movie_id=movie_id,
            payload=payload,
        )
    except Exception as exc:
        raise_http_for_ml_error(exc)

    return review_service.review_to_read_with_analysis(review)
