"""Pydantic v2 request/response models for review analysis API contracts."""

from typing import Literal

from pydantic import BaseModel, Field

SentimentLabel = Literal["positive", "neutral", "negative"]

RatingConsistency = Literal[
    "not_available",
    "consistent",
    "slightly_different",
    "inconsistent",
    "user_rating_higher",
    "user_rating_lower",
]


class AnalyzeReviewRequest(BaseModel):
    """Input for a single review analysis request."""

    review_text: str = Field(
        ...,
        min_length=1,
        description="Text of the user's movie review",
    )
    user_rating: float | None = Field(
        None,
        ge=1,
        le=10,
        description="Numeric rating provided by the user (1–10), if available",
    )


class AspectSentiment(BaseModel):
    """Sentiment toward one extracted aspect."""

    aspect: str = Field(..., description='Aspect label, e.g. "сюжет"')
    sentiment: SentimentLabel
    score: float = Field(..., ge=0, le=1, description="Confidence-style score in [0, 1]")
    evidence: str | None = Field(
        None,
        description="Optional short text fragment where the aspect was found",
    )


class RatingComparison(BaseModel):
    """Comparison between the user's numeric rating and the model prediction."""

    user_rating: float | None
    predicted_rating: float
    difference: float | None = Field(
        None,
        description="Absolute gap when user_rating is present; null otherwise",
    )
    consistency: RatingConsistency
    message: str


class AnalyzeReviewResponse(BaseModel):
    """Full structured output of review analysis (populated by analyzer pipeline)."""

    overall_sentiment: SentimentLabel
    sentiment_score: float = Field(..., ge=0, le=1)
    predicted_rating: float = Field(..., ge=1, le=10)
    rating_comparison: RatingComparison
    aspects: list[AspectSentiment]
    model_version: str = Field(
        ...,
        description="Logical model or schema version string returned to clients",
    )
