"""
Lazy loader for trained rating regression artifacts (experimental / future work).

Not used by the active /ml/analyze-review pipeline, which uses the improved
interpretable baseline in app.rating_predictor.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.config import settings

_rating_model: Any = None
_rating_feature_columns: list[str] | None = None
_rating_metadata: dict[str, Any] | None = None
_rating_lock = threading.Lock()


def _artifact_path(configured: Path) -> Path:
    p = Path(configured)
    if p.is_absolute():
        return p.resolve()
    return (settings.model_dir / p).resolve()


def rating_model_file() -> Path:
    return _artifact_path(settings.rating_model_path)


def rating_feature_columns_file() -> Path:
    return _artifact_path(settings.rating_feature_columns_path)


def rating_metadata_file() -> Path:
    return _artifact_path(settings.rating_model_metadata_path)


def is_rating_model_available() -> bool:
    return rating_model_file().is_file() and rating_feature_columns_file().is_file()


def is_rating_model_loaded() -> bool:
    return _rating_model is not None


def get_rating_feature_columns() -> list[str]:
    global _rating_feature_columns
    if _rating_feature_columns is not None:
        return _rating_feature_columns
    path = rating_feature_columns_file()
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        _rating_feature_columns = [str(c) for c in data]
    else:
        _rating_feature_columns = []
    return _rating_feature_columns


def get_rating_model_metadata() -> dict[str, Any]:
    global _rating_metadata
    if _rating_metadata is not None:
        return _rating_metadata
    path = rating_metadata_file()
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        _rating_metadata = json.load(f)
    return _rating_metadata or {}


def get_rating_model() -> Any:
    """Load and return the trained regressor; raises FileNotFoundError if artifacts missing."""
    global _rating_model
    with _rating_lock:
        if _rating_model is not None:
            return _rating_model
    if not is_rating_model_available():
        raise FileNotFoundError(
            f"Rating model not found. Expected {rating_model_file()} and "
            f"{rating_feature_columns_file()}. Run training/prepare_rating_dataset.py and "
            "training/train_rating_model.py first."
        )
    with _rating_lock:
        if _rating_model is not None:
            return _rating_model
        import joblib

        _rating_model = joblib.load(rating_model_file())
        get_rating_feature_columns()
        get_rating_model_metadata()
        return _rating_model


def reset_rating_model_for_tests() -> None:
    """Clear cached rating model (unit tests only)."""
    global _rating_model, _rating_feature_columns, _rating_metadata
    with _rating_lock:
        _rating_model = None
        _rating_feature_columns = None
        _rating_metadata = None


def set_rating_model_for_tests(model: Any | None, columns: list[str] | None = None) -> None:
    """Inject mock rating model (unit tests only)."""
    global _rating_model, _rating_feature_columns
    with _rating_lock:
        _rating_model = model
        if columns is not None:
            _rating_feature_columns = columns
