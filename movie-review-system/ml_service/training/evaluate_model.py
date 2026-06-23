"""Evaluate trained models — writes metrics to datasets/processed/eval/."""

import argparse
from pathlib import Path

import yaml

TRAINING_ROOT = Path(__file__).resolve().parent
ML_SERVICE_ROOT = TRAINING_ROOT.parent
DEFAULT_CONFIG = TRAINING_ROOT / "config.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate trained ML models")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--component",
        choices=["sentiment", "absa", "recommender"],
        required=True,
    )
    args = parser.parse_args()

    with args.config.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    metrics_dir = (ML_SERVICE_ROOT.parent / "datasets" / "processed" / "eval").resolve()
    model_dir = ML_SERVICE_ROOT / "models" / config[args.component]["output_dir"]

    print("Model evaluation not implemented yet.")
    print(f"  component: {args.component}")
    print(f"  model: {model_dir}")
    print(f"  metrics output: {metrics_dir}")


if __name__ == "__main__":
    main()
