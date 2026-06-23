"""Prepare aspect-based sentiment analysis (ABSA) training splits."""

import argparse
from pathlib import Path

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "processed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare ABSA train/val/test splits")
    parser.add_argument("--source", type=str, default="semeval_absa", help="Source dataset name")
    parser.add_argument("--output", type=Path, default=PROCESSED_DIR / "absa", help="Output directory")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    print("ABSA data preparation not implemented yet.")
    print(f"  source: {args.source}")
    print(f"  output: {args.output}")


if __name__ == "__main__":
    main()
