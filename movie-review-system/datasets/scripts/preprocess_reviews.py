"""Preprocess raw review files into datasets/processed/."""

import argparse
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[1] / "processed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess review datasets")
    parser.add_argument("--input", type=Path, default=RAW_DIR, help="Raw data directory")
    parser.add_argument("--output", type=Path, default=PROCESSED_DIR, help="Output directory")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    print("Preprocessing pipeline not implemented yet.")
    print(f"  input:  {args.input}")
    print(f"  output: {args.output}")


if __name__ == "__main__":
    main()
