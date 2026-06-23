"""Train document-level sentiment model — saves artifacts to ml_service/models/sentiment/."""

import argparse
from pathlib import Path

import yaml

TRAINING_ROOT = Path(__file__).resolve().parent
ML_SERVICE_ROOT = TRAINING_ROOT.parent
DEFAULT_CONFIG = TRAINING_ROOT / "config.yaml"


def load_config(config_path: Path) -> dict:
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train sentiment classification model")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = (ML_SERVICE_ROOT / "models" / config["sentiment"]["output_dir"]).resolve()
    processed = (ML_SERVICE_ROOT / config["paths"]["processed_dir"]).resolve()

    print("Sentiment model training not implemented yet.")
    print(f"  config: {args.config}")
    print(f"  processed data: {processed}")
    print(f"  output: {output_dir}")
    print("\nAfter implementation, artifacts will be written to ml_service/models/sentiment/")
    print("and registered in ml_service/models/manifest.json.")


if __name__ == "__main__":
    main()
