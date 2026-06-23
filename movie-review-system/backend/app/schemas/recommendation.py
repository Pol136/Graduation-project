from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.movie import MovieListItem


class RecommendationMovieRead(MovieListItem):
    pass


class RecommendationRead(BaseModel):
    recommendation_id: int
    run_id: int
    user_id: int
    movie_id: int
    recommendation_score: float
    rank_position: int
    created_at: datetime
    movie: RecommendationMovieRead | None = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationRunRead(BaseModel):
    run_id: int
    user_id: int
    created_at: datetime
    algorithm_version: str | None = None
    recommendations: list[RecommendationRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RecommendationRunListItem(BaseModel):
    run_id: int
    user_id: int
    created_at: datetime
    algorithm_version: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserPreferenceProfileRead(BaseModel):
    profile_id: int
    user_id: int
    positive_preferences: dict[str, float] | None = None
    negative_preferences: dict[str, float] | None = None
    aspect_weights: dict[str, float] | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
