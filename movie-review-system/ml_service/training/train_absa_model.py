"""Train aspect-based sentiment (ABSA) model — saves artifacts to ml_service/models/absa/."""

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
    parser = argparse.ArgumentParser(description="Train ABSA model")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = (ML_SERVICE_ROOT / "models" / config["absa"]["output_dir"]).resolve()

    print("ABSA model training not implemented yet.")
    print(f"  config: {args.config}")
    print(f"  output: {output_dir}")
    print("\nRequires prepared data from datasets/scripts/prepare_absa_data.py")


if __name__ == "__main__":
    main()
