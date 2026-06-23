"""Download public movie review datasets into datasets/raw/."""

import argparse
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "raw"

PLANNED_DATASETS = {
    "imdb": ("IMDb movie reviews (sentiment classification)", "imdb"),
    "semeval_absa": ("SemEval aspect-based sentiment analysis tasks", "semeval_absa"),
    "mams": ("Multi-Aspect Multi-Sentiment (MAMS) dataset", "mams"),
    "movielens": ("MovieLens ratings for collaborative filtering", "movielens"),
}


def list_datasets() -> None:
    print("Planned datasets:\n")
    for key, (description, subdir) in PLANNED_DATASETS.items():
        print(f"  {key:16} — {description}")
        print(f"  {'':16}   → {RAW_DIR / subdir}")
    print(f"\nBase directory: {RAW_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download datasets for ML training")
    parser.add_argument("--list", action="store_true", help="List planned datasets")
    parser.add_argument("--dataset", choices=list(PLANNED_DATASETS.keys()), help="Dataset to download")
    args = parser.parse_args()

    if args.list or not args.dataset:
        list_datasets()
        return

    _, subdir = PLANNED_DATASETS[args.dataset]
    target = RAW_DIR / subdir
    target.mkdir(parents=True, exist_ok=True)
    print(f"Download for '{args.dataset}' not implemented yet.")
    print(f"Place files under: {target}")


if __name__ == "__main__":
    main()
