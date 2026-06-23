# Datasets

All training data lives under **`datasets/`**. Trained model weights live under **`ml_service/models/`** — never commit either to Git.

## Separation of concerns

| Location | Contents |
|----------|----------|
| `datasets/raw/` | Downloaded archives and source files |
| `datasets/processed/` | Train/val/test splits, feature files |
| `datasets/processed/eval/` | Evaluation metrics and reports |
| `datasets/external/` | Licenses, citations, manual references |
| `datasets/scripts/` | Download and preprocessing code |
| `datasets/notebooks/` | EDA (clear large outputs before commit) |
| `ml_service/models/` | Inference checkpoints (see `models/README.md`) |

## Planned sources

### IMDb Movie Reviews

- **Path:** `datasets/raw/imdb/`
- **Use:** Document-level sentiment classification

### SemEval ABSA

- **Path:** `datasets/raw/semeval_absa/`
- **Use:** Aspect-based sentiment analysis

### MAMS

- **Path:** `datasets/raw/mams/`
- **Use:** Multi-aspect, multi-sentiment reviews

### MovieLens

- **Path:** `datasets/raw/movielens/`
- **Use:** Collaborative filtering for recommender training

### Application exports (future)

- **Path:** `datasets/processed/app_reviews/`
- **Use:** Fine-tuning from production reviews

## Local workflow

```bash
cd datasets/scripts
python download_datasets.py --list
python preprocess_reviews.py
python prepare_absa_data.py
```

```bash
cd ml_service
python training/train_sentiment_model.py
python training/train_absa_model.py
python training/evaluate_model.py --component sentiment
```

## Git policy

- **Do not commit** raw downloads, processed splits, notebooks with embedded data, or model checkpoints.
- Tracked: `scripts/*.py`, `README.md`, `.gitkeep` markers.
- Enforced by root `.gitignore` and common data-file patterns.

Download or generate all data **locally** before running Docker or the ML service.
