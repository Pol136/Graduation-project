"""Model loading: Hugging Face sentiment pipeline (lazy) and local artifact validators."""

import json
import threading
from pathlib import Path
from typing import Any

from app.config import settings


class ModelArtifactError(Exception):
    """Raised when required trained model files are not present."""


class SentimentModelLoadError(Exception):
    """Raised when the Hugging Face sentiment model or tokenizer cannot be loaded."""


class AspectModelLoadError(Exception):
    """Raised when the Hugging Face zero-shot aspect model cannot be loaded."""


_sentiment_pipeline: Any = None
_sentiment_pipeline_lock = threading.Lock()

_aspect_pipeline: Any = None
_aspect_pipeline_lock = threading.Lock()


def is_sentiment_model_loaded() -> bool:
    return _sentiment_pipeline is not None


def get_sentiment_pipeline() -> Any:
    """Load and return a singleton text-classification pipeline (CPU); first call downloads weights."""
    global _sentiment_pipeline
    with _sentiment_pipeline_lock:
        if _sentiment_pipeline is not None:
            return _sentiment_pipeline
        try:
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
                pipeline,
            )
        except ImportError as exc:  # pragma: no cover - env guard
            raise SentimentModelLoadError(
                "transformers is not installed. Install ml_service/requirements.txt dependencies."
            ) from exc

        model_name = settings.sentiment_model_name
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
        except Exception as exc:
            raise SentimentModelLoadError(
                f"Failed to load sentiment model '{model_name}' from Hugging Face Hub "
                f"(network or cache issue): {exc}"
            ) from exc

        try:
            _sentiment_pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                device=-1,
            )
        except Exception as exc:
            raise SentimentModelLoadError(f"Failed to build sentiment pipeline: {exc}") from exc
        return _sentiment_pipeline


def reset_sentiment_pipeline_for_tests() -> None:
    """Clear cached pipeline (unit tests only)."""
    global _sentiment_pipeline
    with _sentiment_pipeline_lock:
        _sentiment_pipeline = None


def set_sentiment_pipeline_for_tests(pipeline: Any | None) -> None:
    """Unit tests only: assign the cached pipeline (use ``None`` to clear)."""
    global _sentiment_pipeline
    with _sentiment_pipeline_lock:
        _sentiment_pipeline = pipeline


def is_aspect_model_loaded() -> bool:
    return _aspect_pipeline is not None


def get_aspect_pipeline() -> Any:
    """Load and return a singleton zero-shot classification pipeline (CPU)."""
    global _aspect_pipeline
    with _aspect_pipeline_lock:
        if _aspect_pipeline is not None:
            return _aspect_pipeline
        try:
            from transformers import pipeline
        except ImportError as exc:  # pragma: no cover
            raise AspectModelLoadError(
                "transformers is not installed. Install ml_service/requirements.txt dependencies."
            ) from exc

        model_name = settings.aspect_model_name
        try:
            _aspect_pipeline = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=-1,
            )
        except Exception as exc:
            raise AspectModelLoadError(
                f"Failed to load aspect zero-shot model '{model_name}' from Hugging Face Hub "
                f"(network or cache issue): {exc}"
            ) from exc
        return _aspect_pipeline


def reset_aspect_pipeline_for_tests() -> None:
    """Clear cached aspect pipeline (unit tests only)."""
    global _aspect_pipeline
    with _aspect_pipeline_lock:
        _aspect_pipeline = None


def set_aspect_pipeline_for_tests(pipeline: Any | None) -> None:
    """Unit tests only: assign the cached aspect pipeline (use ``None`` to clear)."""
    global _aspect_pipeline
    with _aspect_pipeline_lock:
        _aspect_pipeline = pipeline


def _directory_has_artifacts(path: Path) -> bool:
    if not path.is_dir():
        return False
    for item in path.iterdir():
        if item.name in (".gitkeep", "README.md"):
            continue
        return True
    return False


def _validate_paths(required: dict[str, Path]) -> None:
    missing: list[str] = []
    for label, path in required.items():
        if not _directory_has_artifacts(path):
            missing.append(f"  - {label}: {path} (missing or empty)")

    if missing:
        raise ModelArtifactError(
            "Trained model artifacts not found. Download datasets and run training first.\n"
            + "\n".join(missing)
            + "\n\nSteps:\n"
            "  1. datasets/scripts/download_datasets.py\n"
            "  2. datasets/scripts/preprocess_reviews.py\n"
            "  3. ml_service/training/train_sentiment_model.py\n"
            "  4. ml_service/training/train_absa_model.py\n"
            "See docs/ML_PIPELINE.md and ml_service/models/README.md."
        )


def _resolve_paths_from_manifest(model_dir: Path) -> tuple[Path, Path, Path]:
    manifest_path = model_dir / settings.manifest_filename
    if not manifest_path.is_file():
        raise ModelArtifactError(
            f"Model manifest not found: {manifest_path}\n"
            "Train models via ml_service/training/ and ensure manifest.json exists."
        )

    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    try:
        sentiment = model_dir / manifest["sentiment"]["path"]
        absa = model_dir / manifest["absa"]["path"]
        recommender = model_dir / manifest["recommender"]["path"]
    except KeyError as exc:
        raise ModelArtifactError(
            f"Invalid manifest.json: missing key {exc!s}. "
            "Expected keys: sentiment, absa, recommender."
        ) from exc

    return sentiment, absa, recommender


def _resolve_all_paths() -> tuple[Path, Path, Path]:
    model_dir = settings.model_dir.resolve()
    if not model_dir.is_dir():
        raise ModelArtifactError(f"Model directory does not exist: {model_dir}")

    manifest_path = model_dir / settings.manifest_filename
    if manifest_path.is_file():
        return _resolve_paths_from_manifest(model_dir)

    return (
        settings.sentiment_dir.resolve(),
        settings.absa_dir.resolve(),
        settings.recommender_dir.resolve(),
    )


def get_analyzer():
    """Legacy local-artifact analyzer (training layout); lazy-import avoids HF loader cycles."""
    from app.analyzer import ReviewAnalyzer

    sentiment_dir, absa_dir, _ = _resolve_all_paths()
    _validate_paths({"sentiment": sentiment_dir, "absa": absa_dir})
    return ReviewAnalyzer(sentiment_path=sentiment_dir, absa_path=absa_dir)


def get_recommender():
    from app.recommender import MovieRecommender

    _, _, recommender_dir = _resolve_all_paths()
    _validate_paths({"recommender": recommender_dir})
    return MovieRecommender(model_path=recommender_dir)
