# ML Pipeline

End-to-end workflow: **datasets** (data) → **training** (fit models) → **ml_service** (inference).

## Overview

```
┌──────────────────────────────────────────────────────────────────┐
│ datasets/                                                        │
│   raw/  →  scripts/  →  processed/  →  processed/eval/           │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ ml_service/training/                                             │
│   train_sentiment_model.py  →  models/sentiment/                 │
│   train_absa_model.py       →  models/absa/                      │
│   evaluate_model.py         →  datasets/processed/eval/            │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ ml_service/app/                                                  │
│   model_loader.py → analyzer.py, recommender.py                  │
│   POST /analyze, POST /recommend                                 │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│ backend/  ml_client.py → persist analysis, drive recommendations │
└──────────────────────────────────────────────────────────────────┘
```

## Phase 1 — Data preparation (`datasets/`)

1. `download_datasets.py` — fetch IMDb, SemEval ABSA, MAMS, MovieLens into `raw/`
2. `preprocess_reviews.py` — clean, tokenize, split → `processed/`
3. `prepare_absa_data.py` — ABSA-specific train/val/test exports

## Phase 2 — Training (`ml_service/training/`)

| Script | Output |
|--------|--------|
| `train_sentiment_model.py` | `models/sentiment/` |
| `train_absa_model.py` | `models/absa/` |
| (future recommender trainer) | `models/recommender/` |

Configuration: `training/config.yaml`

Training scripts must write `models/manifest.json` listing component paths.

## Phase 3 — Evaluation

`evaluate_model.py --component {sentiment|absa|recommender}`

Metrics saved under `datasets/processed/eval/` (gitignored).

## Phase 4 — Inference

1. Artifacts present under `ml_service/models/` per `manifest.json`
2. `model_loader.py` validates directories at startup
3. `analyzer.py` runs sentiment + ABSA on review text
4. `recommender.py` uses user history and **analysis results** (`review_features`) for ranking

If artifacts are missing, the service **does not start** (clear `ModelArtifactError`).

## Phase 5 — Application integration

- Backend creates review → calls `/analyze` → stores `review_analyses`
- Backend requests recommendations → `/recommend` with optional `review_features` from past analyses

## Docker

`docker-compose.yml` mounts:

- `./datasets` → `/datasets` (read/write for training in container)
- `./ml_service/models` → `/app/models`

Run training inside the ML container or on the host before starting inference.
