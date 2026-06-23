"""Review analysis pipeline (sentiment, aspects, rating, comparison)."""

from pathlib import Path

from app.aspect_extractor import extract_aspects
from app.config import settings
from app.preprocessing import validate_review_text
from app.rating_comparator import compare_user_and_predicted_rating
from app.rating_predictor import predict_rating
from app.schemas import AnalyzeReviewResponse, RatingComparison
from app.sentiment_analyzer import SentimentAnalyzer

_sentiment_analyzer = SentimentAnalyzer()


def analyze_review(review_text: str, user_rating: float | None = None) -> AnalyzeReviewResponse:
    """End-to-end review analysis: validate, sentiment, aspects, rating, comparison."""
    text = validate_review_text(review_text)
    sentiment = _sentiment_analyzer.analyze_text(text)
    aspects = extract_aspects(text, sentiment_analyzer=_sentiment_analyzer)
    predicted, rating_source = predict_rating(text, sentiment, aspects)
    comparison = compare_user_and_predicted_rating(user_rating, predicted)
    return AnalyzeReviewResponse(
        overall_sentiment=sentiment.sentiment,  # type: ignore[arg-type]
        sentiment_score=sentiment.score,
        predicted_rating=predicted,
        rating_comparison=RatingComparison(**comparison),
        aspects=aspects,
        model_version=settings.analysis_model_version_for_rating(rating_source),
    )


class ReviewAnalyzer:
    """Loads local sentiment + ABSA checkpoints (training artifact layout)."""

    def __init__(self, sentiment_path: Path, absa_path: Path) -> None:
        self.sentiment_path = sentiment_path
        self.absa_path = absa_path
        self._sentiment_model = None
        self._absa_model = None
        self._load_models()

    def _load_models(self) -> None:
        # Artifacts are validated by model_loader before instantiation.
        # TODO: load checkpoints (e.g. transformers, onnx) from self.sentiment_path and self.absa_path
        pass

    def analyze(self, text: str) -> AnalyzeReviewResponse:
        normalized = validate_review_text(text)
        if self._sentiment_model is None or self._absa_model is None:
            raise NotImplementedError(
                f"Review analysis inference not implemented. "
                f"Artifacts are present at sentiment={self.sentiment_path}, absa={self.absa_path}. "
                "Implement ReviewAnalyzer._load_models() and analyze()."
            )
        _ = normalized
        raise NotImplementedError("ReviewAnalyzer.analyze() is not implemented.")
