from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.database import get_db
from app.db.models import User, Watchlist
from app.schemas.watchlist import (
    WatchlistItemRead,
    WatchlistMovieRead,
    WatchlistRemoveResponse,
)
from app.services import movie_service, watchlist_service

router = APIRouter()


def _to_watchlist_item_read(item: Watchlist) -> WatchlistItemRead:
    return WatchlistItemRead(
        watchlist_id=item.watchlist_id,
        movie_id=item.movie_id,
        added_at=item.added_at,
        movie=WatchlistMovieRead.model_validate(item.movie),
    )


@router.get("", response_model=list[WatchlistItemRead])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[WatchlistItemRead]:
    items = watchlist_service.get_user_watchlist(db, current_user.user_id)
    return [_to_watchlist_item_read(item) for item in items]


@router.post(
    "/{movie_id}",
    response_model=WatchlistItemRead,
    status_code=status.HTTP_201_CREATED,
)
def add_to_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WatchlistItemRead:
    movie = movie_service.get_movie_by_id(db, movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    existing = watchlist_service.get_watchlist_item(db, current_user.user_id, movie_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is already in watchlist",
        )

    try:
        item = watchlist_service.add_movie_to_watchlist(db, current_user.user_id, movie_id)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is already in watchlist",
        ) from None

    return _to_watchlist_item_read(item)


@router.delete("/{movie_id}", response_model=WatchlistRemoveResponse)
def remove_from_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WatchlistRemoveResponse:
    removed = watchlist_service.remove_movie_from_watchlist(
        db,
        current_user.user_id,
        movie_id,
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie is not in watchlist",
        )

    return WatchlistRemoveResponse(message="Movie removed from watchlist")
