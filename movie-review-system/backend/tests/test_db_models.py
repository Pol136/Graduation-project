from sqlalchemy.dialects.postgresql import JSONB

from app.db.database import Base
from app.db import models  # noqa: F401


EXPECTED_TABLES = {
    "users",
    "movies",
    "reviews",
    "review_analysis",
    "movie_summaries",
    "user_preference_profiles",
    "recommendation_runs",
    "recommendations",
    "watchlist",
}

JSONB_COLUMNS = {
    ("movies", "genres"),
    ("review_analysis", "aspects"),
    ("movie_summaries", "sentiment_distribution"),
    ("movie_summaries", "aspect_scores"),
    ("movie_summaries", "aspect_frequency"),
    ("user_preference_profiles", "positive_preferences"),
    ("user_preference_profiles", "negative_preferences"),
    ("user_preference_profiles", "aspect_weights"),
}


def test_all_tables_registered() -> None:
    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES


def test_jsonb_columns_use_postgresql_jsonb() -> None:
    for table_name, column_name in JSONB_COLUMNS:
        column = Base.metadata.tables[table_name].c[column_name]
        assert isinstance(column.type, JSONB)


def test_review_constraints() -> None:
    table = Base.metadata.tables["reviews"]
    constraint_names = {c.name for c in table.constraints if hasattr(c, "name")}
    assert "ck_reviews_user_rating_range" in constraint_names
    assert "ck_reviews_review_text_not_empty" in constraint_names
    assert "uq_reviews_user_id_movie_id" in constraint_names


def test_recommendation_constraints() -> None:
    table = Base.metadata.tables["recommendations"]
    constraint_names = {c.name for c in table.constraints if hasattr(c, "name")}
    assert "ck_recommendations_score_range" in constraint_names
    assert "ck_recommendations_rank_position_positive" in constraint_names
    assert "uq_recommendations_run_id_movie_id" in constraint_names
    assert "uq_recommendations_run_id_rank_position" in constraint_names


def test_review_analysis_constraints() -> None:
    table = Base.metadata.tables["review_analysis"]
    constraint_names = {c.name for c in table.constraints if hasattr(c, "name")}
    assert "ck_review_analysis_overall_sentiment" in constraint_names
    assert "ck_review_analysis_predicted_rating_range" in constraint_names
    assert table.c.review_id.unique is True


def test_watchlist_unique_constraint() -> None:
    table = Base.metadata.tables["watchlist"]
    constraint_names = {c.name for c in table.constraints if hasattr(c, "name")}
    assert "uq_watchlist_user_id_movie_id" in constraint_names


def test_database_url_loaded_from_environment(monkeypatch) -> None:
    from app.core.config import Settings

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@postgres:5432/movie_review_db",
    )
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://postgres:postgres@postgres:5432/movie_review_db"
