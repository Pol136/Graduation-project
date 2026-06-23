"""
Build rating regression features from blinoff/kinopoisk reviews.

EXPERIMENTAL / FUTURE WORK — not used by the active /ml/analyze-review API.
Active rating prediction uses the improved baseline in app.rating_predictor.

Usage (from ml_service/):
  python training/prepare_rating_dataset.py --sample-size 4000
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

ML_SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ML_SERVICE_ROOT.parent
sys.path.insert(0, str(ML_SERVICE_ROOT))

from app.aspect_extractor import extract_aspects  # noqa: E402
from app.config import settings  # noqa: E402
from app.feature_extractor import build_rating_features, rating_feature_column_names  # noqa: E402
from app.preprocessing import validate_review_text  # noqa: E402
from app.sentiment_analyzer import SentimentAnalyzer  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

FEATURES_NAME = "kinopoisk_rating_features_{n}.csv"
SAMPLE_NAME = "kinopoisk_rating_sample_{n}.csv"
FAILED_NAME = "kinopoisk_rating_failed_rows.csv"


def _paths(sample_size: int) -> tuple[Path, Path, Path]:
    processed = settings.processed_data_dir
    processed.mkdir(parents=True, exist_ok=True)
    features = processed / FEATURES_NAME.format(n=sample_size)
    sample = processed / SAMPLE_NAME.format(n=sample_size)
    failed = processed / FAILED_NAME
    return features, sample, failed


def _load_and_filter_kinopoisk() -> pd.DataFrame:
    from datasets import load_dataset

    logger.info("Loading blinoff/kinopoisk from Hugging Face Hub...")
    ds = load_dataset("blinoff/kinopoisk", split="train")
    df = ds.to_pandas()
    df.columns = [str(c).lower() for c in df.columns]
    if "content" not in df.columns and "text" in df.columns:
        df = df.rename(columns={"text": "content"})
    df["content"] = df["content"].astype(str).str.strip()
    df["grade10"] = pd.to_numeric(df["grade10"], errors="coerce")
    mask = (
        df["content"].str.len() > 0
        & df["grade10"].notna()
        & (df["grade10"] != 0)
        & (df["grade10"] >= 1)
        & (df["grade10"] <= 10)
    )
    filtered = df.loc[mask, ["content", "grade10"]].reset_index(drop=True)
    logger.info("Valid rows after filtering: %d", len(filtered))
    return filtered


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Kinopoisk rating feature dataset")
    parser.add_argument("--sample-size", type=int, default=4000)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--force", action="store_true", help="Recompute even if output exists")
    args = parser.parse_args()

    features_path, sample_path, failed_path = _paths(args.sample_size)
    if features_path.is_file() and not args.force:
        logger.info("Features file already exists: %s (use --force to recompute)", features_path)
        return

    filtered = _load_and_filter_kinopoisk()
    if len(filtered) < args.sample_size:
        raise SystemExit(
            f"Not enough valid rows ({len(filtered)}) for sample_size={args.sample_size}"
        )
    sampled = filtered.sample(n=args.sample_size, random_state=args.random_state).reset_index(drop=True)
    sampled.to_csv(sample_path, index=False, encoding="utf-8")
    logger.info("Saved raw sample to %s", sample_path)

    sentiment_analyzer = SentimentAnalyzer()
    feature_cols = rating_feature_column_names()
    rows: list[dict] = []
    failed: list[dict] = []

    for idx, row in tqdm(sampled.iterrows(), total=len(sampled), desc="Extracting features"):
        content = str(row["content"])
        grade10 = float(row["grade10"])
        try:
            text = validate_review_text(content)
            sentiment = sentiment_analyzer.analyze_text(text)
            aspects = extract_aspects(text, sentiment_analyzer=sentiment_analyzer)
            feats = build_rating_features(text, sentiment, aspects)
            record = {c: feats[c] for c in feature_cols}
            record["rating"] = grade10
            rows.append(record)
        except Exception as exc:
            logger.warning("Row %s failed: %s", idx, exc)
            failed.append({"index": idx, "content": content, "grade10": grade10, "error": str(exc)})

    if failed:
        pd.DataFrame(failed).to_csv(failed_path, index=False, encoding="utf-8")
        logger.info("Saved %d failed rows to %s", len(failed), failed_path)

    out = pd.DataFrame(rows)
    out.to_csv(features_path, index=False, encoding="utf-8")
    logger.info("Saved %d feature rows to %s", len(out), features_path)


if __name__ == "__main__":
    main()
