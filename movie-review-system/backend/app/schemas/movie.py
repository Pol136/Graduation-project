from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MovieBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    original_title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    genres: list[str] | None = None
    release_year: int | None = Field(default=None, ge=1888, le=2100)
    poster_url: str | None = None
    external_rating: float | None = Field(default=None, ge=0, le=10)


class MovieCreate(MovieBase):
    tmdb_id: int | None = None


class MovieListItem(MovieBase):
    movie_id: int
    tmdb_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class MovieRead(MovieListItem):
    pass


class MovieSummaryRead(BaseModel):
    summary_id: int | None = None
    movie_id: int
    average_user_rating: float | None = None
    average_predicted_rating: float | None = None
    review_count: int = 0
    sentiment_distribution: dict[str, int] | None = None
    aspect_scores: dict[str, float] | None = None
    aspect_frequency: dict[str, int] | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
