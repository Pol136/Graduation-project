import pytest

from app.rating_comparator import compare_user_and_predicted_rating
from app.rating_predictor import predict_rating_from_sentiment


def test_predict_rating_positive_high_score() -> None:
    r = predict_rating_from_sentiment("positive", 0.9)
    assert r == pytest.approx(9.7, abs=0.01)
    assert 7.0 <= r <= 10.0
    assert r == round(r, 1)


def test_predict_rating_neutral() -> None:
    r = predict_rating_from_sentiment("neutral", 0.8)
    assert r == pytest.approx(6.4, abs=0.01)
    assert 4.0 <= r <= 7.0


def test_predict_rating_negative() -> None:
    r = predict_rating_from_sentiment("negative", 0.9)
    assert r == pytest.approx(1.3, abs=0.01)
    assert 1.0 <= r <= 4.0


def test_compare_no_user_rating() -> None:
    d = compare_user_and_predicted_rating(None, 6.5)
    assert d["user_rating"] is None
    assert d["difference"] is None
    assert d["consistency"] == "not_available"


def test_compare_consistent() -> None:
    d = compare_user_and_predicted_rating(8.0, 8.5)
    assert d["consistency"] == "consistent"
    assert d["difference"] == 0.5


def test_compare_slightly_different() -> None:
    d = compare_user_and_predicted_rating(8.0, 6.5)
    assert d["difference"] == 1.5
    assert d["consistency"] == "slightly_different"


def test_compare_user_higher() -> None:
    d = compare_user_and_predicted_rating(9.0, 5.0)
    assert d["consistency"] == "user_rating_higher"


def test_compare_user_lower() -> None:
    d = compare_user_and_predicted_rating(3.0, 8.0)
    assert d["consistency"] == "user_rating_lower"
