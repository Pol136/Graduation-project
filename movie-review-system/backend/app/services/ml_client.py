"""HTTP client for the ML microservice (review analysis)."""

from typing import Any

import httpx

from app.core.config import settings

_REQUIRED_RESPONSE_FIELDS = ("overall_sentiment", "predicted_rating", "aspects", "model_version")


class MLServiceError(Exception):
    """ML service returned a client error (4xx) or other analysis failure."""


class MLServiceUnavailableError(Exception):
    """ML service is unreachable, timed out, or returned a server error (5xx)."""


class MLServiceInvalidResponseError(Exception):
    """ML service returned invalid JSON or a response missing required fields."""


def _validate_ml_response(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise MLServiceInvalidResponseError("ML response is not a JSON object")
    missing = [field for field in _REQUIRED_RESPONSE_FIELDS if field not in data]
    if missing:
        raise MLServiceInvalidResponseError(
            f"ML response missing required fields: {', '.join(missing)}"
        )
    return data


def analyze_review_with_ml(review_text: str, user_rating: float | None = None) -> dict[str, Any]:
    url = f"{settings.ml_service_url.rstrip('/')}/ml/analyze-review"
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                url,
                json={"review_text": review_text, "user_rating": user_rating},
            )
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        raise MLServiceUnavailableError("ML service is unreachable") from exc

    if response.status_code >= 500:
        raise MLServiceUnavailableError(
            f"ML service returned status {response.status_code}"
        )
    if 400 <= response.status_code < 500:
        detail = response.text.strip() or f"status {response.status_code}"
        raise MLServiceError(f"ML service analysis failed: {detail}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise MLServiceInvalidResponseError("ML response is not valid JSON") from exc

    return _validate_ml_response(payload)


def check_ml_health() -> dict[str, Any]:
    url = f"{settings.ml_service_url.rstrip('/')}/ml/health"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
    except (httpx.RequestError, httpx.TimeoutException) as exc:
        raise MLServiceUnavailableError("ML service is unreachable") from exc

    if response.status_code >= 500:
        raise MLServiceUnavailableError(
            f"ML service returned status {response.status_code}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise MLServiceInvalidResponseError("ML health response is not valid JSON") from exc
