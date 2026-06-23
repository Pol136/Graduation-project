"""Helpers to compare user ratings with model-predicted ratings."""

from typing import Any


def compare_user_and_predicted_rating(
    user_rating: float | None,
    predicted_rating: float,
) -> dict[str, Any]:
    """Build a dict compatible with ``RatingComparison``."""
    if user_rating is None:
        return {
            "user_rating": None,
            "predicted_rating": predicted_rating,
            "difference": None,
            "consistency": "not_available",
            "message": "No user rating was provided; comparison is not available.",
        }

    diff = abs(float(user_rating) - float(predicted_rating))
    if diff <= 1.0:
        consistency = "consistent"
        message = "The user's rating is within one point of the model-predicted rating."
    elif diff <= 2.0:
        consistency = "slightly_different"
        message = "The user's rating differs moderately from the model-predicted rating."
    elif user_rating > predicted_rating:
        consistency = "user_rating_higher"
        message = "The user's rating is noticeably higher than the model-predicted rating."
    else:
        consistency = "user_rating_lower"
        message = "The user's rating is noticeably lower than the model-predicted rating."

    return {
        "user_rating": user_rating,
        "predicted_rating": predicted_rating,
        "difference": diff,
        "consistency": consistency,
        "message": message,
    }
