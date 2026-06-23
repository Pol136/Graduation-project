"""Movie recommendations using trained model and review analysis signals."""

from pathlib import Path


class MovieRecommender:
    """Loads recommender checkpoint and produces ranked movie suggestions."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        # Artifact directory validated by model_loader.
        # TODO: load recommender from self.model_path
        pass

    def recommend(
        self,
        user_id: int,
        limit: int = 10,
        *,
        review_features: list[dict] | None = None,
    ) -> list[dict]:
        """
        Return ranked recommendations.

        review_features: optional analysis outputs (sentiment, aspects) from user history.
        """
        if self._model is None:
            raise NotImplementedError(
                f"Recommendation inference not implemented. "
                f"Artifacts are present at {self.model_path}. "
                "Implement MovieRecommender._load_model() and recommend()."
            )
        _ = user_id, limit, review_features
        raise NotImplementedError("MovieRecommender.recommend() is not implemented.")
