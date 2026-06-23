"""Initial database schema.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "movies",
        sa.Column("movie_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tmdb_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("original_title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("genres", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("release_year", sa.Integer(), nullable=True),
        sa.Column("poster_url", sa.Text(), nullable=True),
        sa.Column("external_rating", sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("movie_id"),
    )
    op.create_index("ix_movies_tmdb_id", "movies", ["tmdb_id"], unique=True)
    op.create_index("ix_movies_title", "movies", ["title"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("review_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("movie_id", sa.BigInteger(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=False),
        sa.Column("user_rating", sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "user_rating >= 1 AND user_rating <= 10", name="ck_reviews_user_rating_range"
        ),
        sa.CheckConstraint(
            "length(trim(review_text)) > 0", name="ck_reviews_review_text_not_empty"
        ),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.movie_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("review_id"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_reviews_user_id_movie_id"),
    )
    op.create_index("ix_reviews_movie_id", "reviews", ["movie_id"], unique=False)
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"], unique=False)

    op.create_table(
        "review_analysis",
        sa.Column("analysis_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("review_id", sa.BigInteger(), nullable=False),
        sa.Column("overall_sentiment", sa.String(length=32), nullable=False),
        sa.Column("predicted_rating", sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column("aspects", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "analyzed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "overall_sentiment IN ('positive', 'neutral', 'negative')",
            name="ck_review_analysis_overall_sentiment",
        ),
        sa.CheckConstraint(
            "predicted_rating IS NULL OR (predicted_rating >= 1 AND predicted_rating <= 10)",
            name="ck_review_analysis_predicted_rating_range",
        ),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.review_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("analysis_id"),
        sa.UniqueConstraint("review_id"),
    )
    op.create_index(
        "ix_review_analysis_review_id", "review_analysis", ["review_id"], unique=False
    )

    op.create_table(
        "movie_summaries",
        sa.Column("summary_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("movie_id", sa.BigInteger(), nullable=False),
        sa.Column("average_user_rating", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("average_predicted_rating", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "sentiment_distribution",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("aspect_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("aspect_frequency", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.movie_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("summary_id"),
        sa.UniqueConstraint("movie_id"),
    )
    op.create_index(
        "ix_movie_summaries_movie_id", "movie_summaries", ["movie_id"], unique=False
    )

    op.create_table(
        "user_preference_profiles",
        sa.Column("profile_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "positive_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "negative_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("aspect_weights", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_user_preference_profiles_user_id",
        "user_preference_profiles",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "recommendation_runs",
        sa.Column("run_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("algorithm_version", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index(
        "ix_recommendation_runs_user_id", "recommendation_runs", ["user_id"], unique=False
    )

    op.create_table(
        "recommendations",
        sa.Column("recommendation_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("movie_id", sa.BigInteger(), nullable=False),
        sa.Column("recommendation_score", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "recommendation_score >= 0 AND recommendation_score <= 1",
            name="ck_recommendations_score_range",
        ),
        sa.CheckConstraint("rank_position > 0", name="ck_recommendations_rank_position_positive"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.movie_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["recommendation_runs.run_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("recommendation_id"),
        sa.UniqueConstraint("run_id", "movie_id", name="uq_recommendations_run_id_movie_id"),
        sa.UniqueConstraint(
            "run_id", "rank_position", name="uq_recommendations_run_id_rank_position"
        ),
    )
    op.create_index("ix_recommendations_movie_id", "recommendations", ["movie_id"], unique=False)
    op.create_index("ix_recommendations_run_id", "recommendations", ["run_id"], unique=False)
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"], unique=False)

    op.create_table(
        "watchlist",
        sa.Column("watchlist_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("movie_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.movie_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("watchlist_id"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_watchlist_user_id_movie_id"),
    )
    op.create_index("ix_watchlist_movie_id", "watchlist", ["movie_id"], unique=False)
    op.create_index("ix_watchlist_user_id", "watchlist", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_watchlist_user_id", table_name="watchlist")
    op.drop_index("ix_watchlist_movie_id", table_name="watchlist")
    op.drop_table("watchlist")

    op.drop_index("ix_recommendations_user_id", table_name="recommendations")
    op.drop_index("ix_recommendations_run_id", table_name="recommendations")
    op.drop_index("ix_recommendations_movie_id", table_name="recommendations")
    op.drop_table("recommendations")

    op.drop_index("ix_recommendation_runs_user_id", table_name="recommendation_runs")
    op.drop_table("recommendation_runs")

    op.drop_index("ix_user_preference_profiles_user_id", table_name="user_preference_profiles")
    op.drop_table("user_preference_profiles")

    op.drop_index("ix_movie_summaries_movie_id", table_name="movie_summaries")
    op.drop_table("movie_summaries")

    op.drop_index("ix_review_analysis_review_id", table_name="review_analysis")
    op.drop_table("review_analysis")

    op.drop_index("ix_reviews_user_id", table_name="reviews")
    op.drop_index("ix_reviews_movie_id", table_name="reviews")
    op.drop_table("reviews")

    op.drop_index("ix_movies_title", table_name="movies")
    op.drop_index("ix_movies_tmdb_id", table_name="movies")
    op.drop_table("movies")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
