from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import MovieSummary, ReviewAnalysis
from app.services.movie_summary_service import compute_summary_values, recalculate_movie_summary
from tests.conftest import requires_db
from tests.test_reviews_ml import SAMPLE_ML_RESULT, _register_and_login

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _make_review(review_id: int, user_rating: float) -> SimpleNamespace:
    return SimpleNamespace(review_id=review_id, user_rating=user_rating)


def _make_analysis(
    review_id: int,
    *,
    overall_sentiment: str = "positive",
    predicted_rating: float | None = 8.4,
    aspects: list | None = None,
) -> SimpleNamespace:
    if aspects is None:
        aspects = [
            {
                "aspect": "сюжет",
                "sentiment": "positive",
                "score": 0.82,
                "evidence": "Сюжет держит в напряжении.",
            },
            {
                "aspect": "актеры",
                "sentiment": "positive",
                "score": 0.9,
                "evidence": "Сильная игра.",
            },
        ]
    return SimpleNamespace(
        review_id=review_id,
        overall_sentiment=overall_sentiment,
        predicted_rating=predicted_rating,
        aspects=aspects,
    )


def test_compute_summary_values_aggregates_analysis_fields() -> None:
    reviews = [_make_review(1, 8.5), _make_review(2, 7.0)]
    analyses = [
        _make_analysis(1, overall_sentiment="positive", predicted_rating=8.4),
        _make_analysis(2, overall_sentiment="neutral", predicted_rating=6.0),
    ]

    values = compute_summary_values(reviews, analyses)

    assert values["review_count"] == 2
    assert values["average_user_rating"] == 7.75
    assert values["average_predicted_rating"] == 7.2
    assert values["sentiment_distribution"] == {
        "positive": 1,
        "neutral": 1,
        "negative": 0,
    }
    assert values["aspect_frequency"]["сюжет"] == 2
    assert values["aspect_frequency"]["актеры"] == 2
    assert values["aspect_scores"]["сюжет"] == 0.82
    assert values["aspect_scores"]["актеры"] == 0.9


def test_compute_summary_values_supports_rating_10() -> None:
    reviews = [_make_review(1, 10.0)]
    analyses = [_make_analysis(1, predicted_rating=10.0)]

    values = compute_summary_values(reviews, analyses)

    assert values["average_user_rating"] == 10.0
    assert values["average_predicted_rating"] == 10.0


def test_compute_summary_values_skips_invalid_aspects() -> None:
    reviews = [_make_review(1, 8.0)]
    analyses = [
        _make_analysis(
            1,
            aspects=[
                {"aspect": "сюжет", "score": "not-a-number"},
                {"aspect": "", "score": 0.5},
                "broken",
                None,
            ],
        )
    ]

    values = compute_summary_values(reviews, analyses)

    assert values["aspect_frequency"]["сюжет"] == 1
    assert values["aspect_scores"] == {}


def test_recalculate_movie_summary_queries_analyses_by_review_ids() -> None:
    from app.db.models import MovieSummary, Review, ReviewAnalysis

    db = MagicMock()
    review = _make_review(10, 8.5)
    analysis = _make_analysis(10)

    review_query = MagicMock()
    review_query.filter.return_value.all.return_value = [review]

    summary_query = MagicMock()
    summary_query.filter.return_value.one_or_none.return_value = None

    analysis_query = MagicMock()
    analysis_query.filter.return_value.all.return_value = [analysis]

    def query_side_effect(model: type) -> MagicMock:
        if model is Review:
            return review_query
        if model is MovieSummary:
            return summary_query
        if model is ReviewAnalysis:
            return analysis_query
        raise AssertionError(f"Unexpected model: {model}")

    db.query.side_effect = query_side_effect

    summary = recalculate_movie_summary(db, movie_id=1)

    assert summary.average_predicted_rating == 8.4
    assert summary.sentiment_distribution["positive"] == 1
    assert summary.aspect_scores["сюжет"] == 0.82
    db.add.assert_called_once()


@requires_db
def test_summary_refresh_recalculates_stale_row(
    client: TestClient,
    unique_email: str,
) -> None:
    with patch(
        "app.services.review_service.analyze_review_with_ml",
        return_value=SAMPLE_ML_RESULT.copy(),
    ):
        token = _register_and_login(client, unique_email)
        movie_id = client.post("/api/movies", json={"title": "Refresh Summary Movie"}).json()[
            "movie_id"
        ]
        client.post(
            f"/api/movies/{movie_id}/reviews",
            headers={"Authorization": f"Bearer {token}"},
            json={"review_text": "Refresh test", "user_rating": 8.0},
        )

    with SessionLocal() as db:
        summary = db.scalar(select(MovieSummary).where(MovieSummary.movie_id == movie_id))
        assert summary is not None
        summary.average_predicted_rating = None
        summary.sentiment_distribution = {"positive": 0, "neutral": 0, "negative": 0}
        summary.aspect_scores = {}
        summary.aspect_frequency = {}
        db.commit()

    stale = client.get(f"/api/movies/{movie_id}/summary").json()
    assert stale["average_predicted_rating"] is None

    refreshed = client.get(f"/api/movies/{movie_id}/summary?refresh=true").json()
    assert refreshed["average_predicted_rating"] == 8.4
    assert refreshed["sentiment_distribution"]["positive"] == 1
    assert refreshed["aspect_scores"]["сюжет"] == 0.82
    assert refreshed["aspect_frequency"]["сюжет"] == 1


@requires_db
def test_create_review_summary_includes_analysis_aggregates(
    client: TestClient,
    unique_email: str,
) -> None:
    with patch(
        "app.services.review_service.analyze_review_with_ml",
        return_value=SAMPLE_ML_RESULT.copy(),
    ):
        token = _register_and_login(client, unique_email)
        movie_id = client.post("/api/movies", json={"title": "Summary Aggregate Movie"}).json()[
            "movie_id"
        ]
        client.post(
            f"/api/movies/{movie_id}/reviews",
            headers={"Authorization": f"Bearer {token}"},
            json={"review_text": "Aggregate test", "user_rating": 8.5},
        )

    summary = client.get(f"/api/movies/{movie_id}/summary").json()
    assert summary["average_predicted_rating"] == 8.4
    assert summary["sentiment_distribution"]["positive"] == 1
    assert summary["aspect_scores"]["сюжет"] == 0.82
    assert summary["aspect_frequency"]["сюжет"] == 1
