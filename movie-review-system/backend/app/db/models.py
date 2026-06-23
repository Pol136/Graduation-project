from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

SENTIMENT_VALUES = ("positive", "neutral", "negative")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    reviews: Mapped[list["Review"]] = relationship(back_populates="user")
    user_preference_profile: Mapped["UserPreferenceProfile | None"] = relationship(
        back_populates="user", uselist=False
    )
    recommendation_runs: Mapped[list["RecommendationRun"]] = relationship(back_populates="user")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="user")
    watchlist_items: Mapped[list["Watchlist"]] = relationship(back_populates="user")


class Movie(Base):
    __tablename__ = "movies"

    movie_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    original_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    genres: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_rating: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    reviews: Mapped[list["Review"]] = relationship(back_populates="movie")
    movie_summary: Mapped["MovieSummary | None"] = relationship(
        back_populates="movie", uselist=False
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="movie")
    watchlist_items: Mapped[list["Watchlist"]] = relationship(back_populates="movie")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_reviews_user_id_movie_id"),
        CheckConstraint("user_rating >= 1 AND user_rating <= 10", name="ck_reviews_user_rating_range"),
        CheckConstraint("length(trim(review_text)) > 0", name="ck_reviews_review_text_not_empty"),
        Index("ix_reviews_user_id", "user_id"),
        Index("ix_reviews_movie_id", "movie_id"),
    )

    review_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movies.movie_id", ondelete="CASCADE"), nullable=False
    )
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    user_rating: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="reviews")
    movie: Mapped["Movie"] = relationship(back_populates="reviews")
    review_analysis: Mapped["ReviewAnalysis | None"] = relationship(
        back_populates="review", uselist=False
    )


class ReviewAnalysis(Base):
    __tablename__ = "review_analysis"
    __table_args__ = (
        CheckConstraint(
            "overall_sentiment IN ('positive', 'neutral', 'negative')",
            name="ck_review_analysis_overall_sentiment",
        ),
        CheckConstraint(
            "predicted_rating IS NULL OR (predicted_rating >= 1 AND predicted_rating <= 10)",
            name="ck_review_analysis_predicted_rating_range",
        ),
        Index("ix_review_analysis_review_id", "review_id"),
    )

    analysis_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("reviews.review_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    overall_sentiment: Mapped[str] = mapped_column(String(32), nullable=False)
    predicted_rating: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    aspects: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    review: Mapped["Review"] = relationship(back_populates="review_analysis")


class MovieSummary(Base):
    __tablename__ = "movie_summaries"
    __table_args__ = (Index("ix_movie_summaries_movie_id", "movie_id"),)

    summary_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    movie_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("movies.movie_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    average_user_rating: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    average_predicted_rating: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    sentiment_distribution: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    aspect_scores: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    aspect_frequency: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    movie: Mapped["Movie"] = relationship(back_populates="movie_summary")


class UserPreferenceProfile(Base):
    __tablename__ = "user_preference_profiles"
    __table_args__ = (Index("ix_user_preference_profiles_user_id", "user_id"),)

    profile_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    positive_preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    negative_preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    aspect_weights: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="user_preference_profile")


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"
    __table_args__ = (Index("ix_recommendation_runs_user_id", "user_id"),)

    run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    algorithm_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship(back_populates="recommendation_runs")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="run")


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        UniqueConstraint("run_id", "movie_id", name="uq_recommendations_run_id_movie_id"),
        UniqueConstraint("run_id", "rank_position", name="uq_recommendations_run_id_rank_position"),
        CheckConstraint(
            "recommendation_score >= 0 AND recommendation_score <= 1",
            name="ck_recommendations_score_range",
        ),
        CheckConstraint("rank_position > 0", name="ck_recommendations_rank_position_positive"),
        Index("ix_recommendations_user_id", "user_id"),
        Index("ix_recommendations_movie_id", "movie_id"),
        Index("ix_recommendations_run_id", "run_id"),
    )

    recommendation_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    run_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("recommendation_runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movies.movie_id", ondelete="CASCADE"), nullable=False
    )
    recommendation_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    rank_position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped["RecommendationRun"] = relationship(back_populates="recommendations")
    user: Mapped["User"] = relationship(back_populates="recommendations")
    movie: Mapped["Movie"] = relationship(back_populates="recommendations")


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_watchlist_user_id_movie_id"),
        Index("ix_watchlist_user_id", "user_id"),
        Index("ix_watchlist_movie_id", "movie_id"),
    )

    watchlist_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movies.movie_id", ondelete="CASCADE"), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="watchlist_items")
    movie: Mapped["Movie"] = relationship(back_populates="watchlist_items")


__all__ = [
    "User",
    "Movie",
    "Review",
    "ReviewAnalysis",
    "MovieSummary",
    "UserPreferenceProfile",
    "RecommendationRun",
    "Recommendation",
    "Watchlist",
    "SENTIMENT_VALUES",
]
