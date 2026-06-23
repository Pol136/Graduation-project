"""
Train HistGradientBoostingRegressor on Kinopoisk-derived rating features.

EXPERIMENTAL / FUTURE WORK — not used by the active /ml/analyze-review API.
Active rating prediction uses the improved baseline in app.rating_predictor.

Usage (from ml_service/):
  python training/train_rating_model.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

ML_SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_SERVICE_ROOT))

from app.config import settings  # noqa: E402
from app.feature_extractor import rating_feature_column_names  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_VERSION = "rating-regressor-hgb-kinopoisk-v1"
DEFAULT_FEATURES_FILE = "kinopoisk_rating_features_4000.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Train rating regression model")
    parser.add_argument(
        "--features-file",
        type=str,
        default=DEFAULT_FEATURES_FILE,
        help="CSV under datasets/processed/",
    )
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    features_path = settings.processed_data_dir / args.features_file
    if not features_path.is_file():
        raise SystemExit(f"Features file not found: {features_path}. Run prepare_rating_dataset.py first.")

    df = pd.read_csv(features_path)
    if "rating" not in df.columns:
        raise SystemExit("CSV must contain a 'rating' target column.")

    expected_cols = rating_feature_column_names()
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing feature columns in CSV: {missing[:5]}...")

    X = df[expected_cols].astype(np.float64)
    y = df["rating"].astype(np.float64)

    x_train, x_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    model = HistGradientBoostingRegressor(
        random_state=args.random_state,
        max_iter=300,
        learning_rate=0.05,
    )
    logger.info("Training HistGradientBoostingRegressor on %d samples...", len(x_train))
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    print("\n=== Rating model evaluation (hold-out 20%) ===")
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R2:   {r2:.4f}")

    model_dir = settings.model_dir
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / settings.rating_model_path.name
    columns_path = model_dir / settings.rating_feature_columns_path.name
    metadata_path = model_dir / settings.rating_model_metadata_path.name

    joblib.dump(model, model_path)
    with columns_path.open("w", encoding="utf-8") as f:
        json.dump(expected_cols, f, indent=2, ensure_ascii=False)

    metadata = {
        "dataset_name": "blinoff/kinopoisk",
        "sample_size": int(len(df)),
        "target": "grade10",
        "model_type": "HistGradientBoostingRegressor",
        "metrics": {"MAE": mae, "RMSE": rmse, "R2": r2},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(expected_cols),
        "model_version": MODEL_VERSION,
        "features_file": str(features_path.name),
        "random_state": args.random_state,
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info("Saved model to %s", model_path)
    logger.info("Saved feature columns to %s", columns_path)
    logger.info("Saved metadata to %s", metadata_path)


if __name__ == "__main__":
    main()
