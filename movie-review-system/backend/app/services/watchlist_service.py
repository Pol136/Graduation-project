from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db.models import Watchlist


def get_user_watchlist(db: Session, user_id: int) -> list[Watchlist]:
    stmt = (
        select(Watchlist)
        .options(joinedload(Watchlist.movie))
        .where(Watchlist.user_id == user_id)
        .order_by(Watchlist.added_at.desc())
    )
    return list(db.scalars(stmt).unique().all())


def get_watchlist_item(db: Session, user_id: int, movie_id: int) -> Watchlist | None:
    return db.scalar(
        select(Watchlist)
        .options(joinedload(Watchlist.movie))
        .where(
            Watchlist.user_id == user_id,
            Watchlist.movie_id == movie_id,
        )
    )


def add_movie_to_watchlist(db: Session, user_id: int, movie_id: int) -> Watchlist:
    item = Watchlist(user_id=user_id, movie_id=movie_id)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    loaded = get_watchlist_item(db, user_id, movie_id)
    if loaded is None:
        raise RuntimeError("Watchlist item was not found after insert")
    return loaded


def remove_movie_from_watchlist(db: Session, user_id: int, movie_id: int) -> bool:
    item = get_watchlist_item(db, user_id, movie_id)
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True
