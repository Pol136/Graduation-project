from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.movie import MovieListItem


class WatchlistMovieRead(MovieListItem):
    """Movie details embedded in a watchlist item."""

    pass


class WatchlistItemRead(BaseModel):
    watchlist_id: int
    movie_id: int
    added_at: datetime
    movie: WatchlistMovieRead

    model_config = ConfigDict(from_attributes=True)


class WatchlistRemoveResponse(BaseModel):
    message: str
