from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ML_SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ML_SERVICE_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    ml_service_version: str = Field(default="0.1.0", validation_alias="ML_SERVICE_VERSION")
    model_version_label: str = Field(
        default="sentiment-rubert-tiny-v1",
        validation_alias="MODEL_VERSION",
    )
    model_path: Path = Field(
        default=Path("./models"),
        validation_alias=AliasChoices("MODEL_PATH", "MODEL_DIR"),
    )

    sentiment_model_name: str = Field(
        default="cointegrated/rubert-tiny-sentiment-balanced",
        validation_alias="SENTIMENT_MODEL_NAME",
    )
    sentiment_max_length: int = Field(default=512, validation_alias="SENTIMENT_MAX_LENGTH")
    sentiment_chunk_max_chars: int = Field(
        default=900,
        validation_alias="SENTIMENT_CHUNK_MAX_CHARS",
    )

    aspect_model_name: str = Field(
        default="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
        validation_alias="ASPECT_MODEL_NAME",
    )
    aspect_confidence_threshold: float = Field(
        default=0.55,
        validation_alias="ASPECT_CONFIDENCE_THRESHOLD",
    )
    aspect_max_sentences: int = Field(default=30, validation_alias="ASPECT_MAX_SENTENCES")
    aspect_multi_label: bool = Field(default=True, validation_alias="ASPECT_MULTI_LABEL")
    aspect_model_version: str = Field(
        default="aspect-zero-shot-mdeberta-v1",
        validation_alias="ASPECT_MODEL_VERSION",
    )
    analysis_model_version: str = Field(
        default="sentiment-rubert-tiny-v1+aspect-zero-shot-mdeberta-v1",
        validation_alias="ANALYSIS_MODEL_VERSION",
    )

    rating_model_path: Path = Field(
        default=Path("rating_regressor.joblib"),
        validation_alias="RATING_MODEL_PATH",
    )
    rating_feature_columns_path: Path = Field(
        default=Path("rating_feature_columns.json"),
        validation_alias="RATING_FEATURE_COLUMNS_PATH",
    )
    rating_model_metadata_path: Path = Field(
        default=Path("rating_model_metadata.json"),
        validation_alias="RATING_MODEL_METADATA_PATH",
    )
    rating_model_version: str = Field(
        default="rating-regressor-hgb-kinopoisk-v1",
        validation_alias="RATING_MODEL_VERSION",
    )
    rating_baseline_version: str = Field(
        default="rating-improved-baseline-v1",
        validation_alias=AliasChoices("RATING_BASELINE_VERSION", "RATING_IMPROVED_BASELINE_VERSION"),
    )

    datasets_dir: Path = REPO_ROOT / "datasets"
    processed_data_dir: Path = REPO_ROOT / "datasets" / "processed"

    sentiment_model_path: Path | None = None
    absa_model_path: Path | None = None
    recommender_model_path: Path | None = None

    manifest_filename: str = "manifest.json"

    host: str = "0.0.0.0"
    port: int = 8001

    @property
    def model_dir(self) -> Path:
        p = Path(self.model_path)
        if p.is_absolute():
            return p.resolve()
        return (ML_SERVICE_ROOT / p).resolve()

    @property
    def sentiment_dir(self) -> Path:
        if self.sentiment_model_path:
            return Path(self.sentiment_model_path)
        return self.model_dir / "sentiment"

    @property
    def absa_dir(self) -> Path:
        if self.absa_model_path:
            return Path(self.absa_model_path)
        return self.model_dir / "absa"

    @property
    def recommender_dir(self) -> Path:
        if self.recommender_model_path:
            return Path(self.recommender_model_path)
        return self.model_dir / "recommender"

    @property
    def ML_SERVICE_VERSION(self) -> str:  # noqa: N802
        """Same as ``ml_service_version`` (env ``ML_SERVICE_VERSION``); alias for API docs."""
        return self.ml_service_version

    def analysis_model_version_for_rating(self, rating_source: str = "improved_baseline") -> str:
        """Full pipeline version string including active rating component."""
        _ = rating_source
        return f"{self.analysis_model_version}+{self.rating_baseline_version}"


settings = Settings()
