from fastapi import APIRouter, HTTPException, status

from app.api.deps_ml import raise_http_for_ml_error
from app.services.ml_client import MLServiceUnavailableError, check_ml_health

router = APIRouter()


@router.get("/health")
def ml_health() -> dict:
    try:
        return check_ml_health()
    except MLServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML service is unavailable.",
        ) from exc
    except Exception as exc:
        raise_http_for_ml_error(exc)
