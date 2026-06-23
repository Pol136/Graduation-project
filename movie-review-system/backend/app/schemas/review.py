from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewBase(BaseModel):
    review_text: str = Field(min_length=1)
    user_rating: float = Field(ge=1, le=10)

    @field_validator("review_text")
    @classmethod
    def review_text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("review_text must not be empty")
        return value


class ReviewCreate(BaseModel):
    review_text: str = Field(min_length=1)
    user_rating: float = Field(ge=1, le=10)

    @field_validator("review_text")
    @classmethod
    def review_text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("review_text must not be empty")
        return value


class ReviewUpdate(BaseModel):
    review_text: str | None = Field(default=None, min_length=1)
    user_rating: float | None = Field(default=None, ge=1, le=10)

    @field_validator("review_text")
    @classmethod
    def review_text_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("review_text must not be empty")
        return value


class ReviewRead(BaseModel):
    review_id: int
    movie_id: int
    user_id: int
    review_text: str
    user_rating: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewWithUserRead(ReviewRead):
    username: str


class ReviewAnalysisRead(BaseModel):
    analysis_id: int
    review_id: int
    overall_sentiment: str
    predicted_rating: float | None
    aspects: list[dict[str, Any]] | None
    analyzed_at: datetime
    model_version: str | None

    model_config = ConfigDict(from_attributes=True)


class ReviewReadWithAnalysis(ReviewRead):
    analysis: ReviewAnalysisRead | None = None
