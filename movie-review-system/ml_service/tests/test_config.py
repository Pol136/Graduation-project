"""Settings defaults for threshold and combined pipeline model version."""

from app.config import settings


def test_default_aspect_confidence_threshold() -> None:
    assert settings.aspect_confidence_threshold == 0.55


def test_default_analysis_model_version() -> None:
    assert settings.analysis_model_version == "sentiment-rubert-tiny-v1+aspect-zero-shot-mdeberta-v1"


def test_component_model_versions_unchanged() -> None:
    assert settings.model_version_label == "sentiment-rubert-tiny-v1"
    assert settings.aspect_model_version == "aspect-zero-shot-mdeberta-v1"


def test_analysis_model_version_uses_improved_baseline() -> None:
    base = settings.analysis_model_version
    assert settings.analysis_model_version_for_rating() == (
        f"{base}+rating-improved-baseline-v1"
    )
    assert settings.analysis_model_version_for_rating("improved_baseline") == (
        f"{base}+rating-improved-baseline-v1"
    )
