from fastapi import APIRouter, FastAPI, HTTPException

from app.analyzer import analyze_review
from app.config import settings
from app.model_loader import (
    AspectModelLoadError,
    SentimentModelLoadError,
    is_aspect_model_loaded,
    is_sentiment_model_loaded,
)
from app.rating_model_loader import is_rating_model_available, is_rating_model_loaded
from app.schemas import AnalyzeReviewRequest, AnalyzeReviewResponse

app = FastAPI(
    title="Movie Review ML Service",
    description="Review sentiment (Hugging Face), aspects, and rating analysis",
    version=settings.ML_SERVICE_VERSION,
)

ml_router = APIRouter(prefix="/ml", tags=["ml"])

RATING_METHOD_ACTIVE = "improved_baseline"


@ml_router.get("/health")
def ml_health() -> dict[str, str | bool]:
    sentiment_loaded = is_sentiment_model_loaded()
    return {
        "status": "ok",
        "service": "ml_service",
        "sentiment_model_loaded": sentiment_loaded,
        "aspect_model_loaded": is_aspect_model_loaded(),
        "rating_method": RATING_METHOD_ACTIVE,
        "rating_model_available": is_rating_model_available(),
        "rating_model_loaded": is_rating_model_loaded(),
        "model_loaded": sentiment_loaded,
        "version": settings.ML_SERVICE_VERSION,
    }


@ml_router.post("/analyze-review", response_model=AnalyzeReviewResponse)
def analyze_review_endpoint(payload: AnalyzeReviewRequest) -> AnalyzeReviewResponse:
    try:
        return analyze_review(payload.review_text, payload.user_rating)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (SentimentModelLoadError, AspectModelLoadError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc


app.include_router(ml_router)
