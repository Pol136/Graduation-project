import pytest

from app.model_loader import ModelArtifactError, get_analyzer, get_recommender


def test_get_analyzer_fails_without_artifacts() -> None:
    with pytest.raises(ModelArtifactError) as exc_info:
        get_analyzer()
    assert "artifacts not found" in str(exc_info.value).lower() or "manifest" in str(exc_info.value).lower()


def test_get_recommender_fails_without_artifacts() -> None:
    with pytest.raises(ModelArtifactError) as exc_info:
        get_recommender()
    assert "artifacts not found" in str(exc_info.value).lower() or "manifest" in str(exc_info.value).lower()
