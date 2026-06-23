# Datasets

Training and evaluation data for the movie review ML pipeline. **Stored separately from `ml_service/`** — only processed splits and scripts live here; trained weights go to `ml_service/models/`.

## Local setup

Data and model files are **not in Git**. Generate them on your machine:

```bash
cd datasets/scripts
python download_datasets.py --list
python download_datasets.py --dataset imdb    # when implemented
python preprocess_reviews.py
python prepare_absa_data.py
```

Then train models (see `ml_service/training/` and [docs/ML_PIPELINE.md](../docs/ML_PIPELINE.md)).

## Directory layout

| Path | Purpose |
|------|---------|
| `raw/` | Downloaded, unmodified datasets |
| `processed/` | Cleaned splits for training and evaluation |
| `external/` | Licenses, manual downloads, references |
| `scripts/` | Download and preprocessing pipelines |
| `notebooks/` | Exploratory analysis |

## Git policy

Large files under `raw/`, `processed/`, and `external/` are excluded by the root `.gitignore`. Only `.gitkeep`, `README.md`, and `scripts/*.py` are tracked.

See [docs/DATASETS.md](../docs/DATASETS.md) for planned sources (IMDb, SemEval ABSA, MAMS, MovieLens).
