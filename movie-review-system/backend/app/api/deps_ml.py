from fastapi import HTTPException, status

from app.services.ml_client import (
    MLServiceError,
    MLServiceInvalidResponseError,
    MLServiceUnavailableError,
)


def raise_http_for_ml_error(exc: Exception) -> None:
    if isinstance(exc, MLServiceUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML service is unavailable. Review analysis could not be completed.",
        ) from exc
    if isinstance(exc, MLServiceInvalidResponseError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ML service returned an invalid response.",
        ) from exc
    if isinstance(exc, MLServiceError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ML service analysis failed.",
        ) from exc
    raise exc
