# Movie Review Analysis & Recommendation System

Monorepo for a full-stack movie review analysis and recommendation platform with **real ML training and inference**.

## Project structure

| Component | Description |
|-----------|-------------|
| `backend/` | FastAPI REST API — auth, movies, reviews, recommendations, watchlist |
| `frontend/` | React + Vite + TypeScript SPA |
| `ml_service/` | Inference API + `training/` scripts; loads artifacts from `models/` |
| `datasets/` | Raw/processed data and preprocessing scripts (not in Git) |
| `database/` | PostgreSQL init scripts |
| `docs/` | Specifications and ML pipeline documentation |

## Prerequisites

Before running the ML service you must:

1. **Download datasets** into `datasets/raw/` (see `datasets/scripts/`)
2. **Preprocess** into `datasets/processed/`
3. **Train models** via `ml_service/training/` → artifacts in `ml_service/models/`

The ML service **fails at startup** if trained artifacts are missing — no mock fallback.

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env
cp ml_service/.env.example ml_service/.env
cp frontend/.env.example frontend/.env

# Prepare data and train models first (on host), then:
docker compose up --build
```

Docker mounts `./datasets` and `./ml_service/models` into the ML container.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000/docs |
| ML service | http://localhost:8001/docs |
| PostgreSQL | localhost:5432 |

## ML workflow

```
datasets/raw  →  scripts/  →  datasets/processed
                                    ↓
                         ml_service/training/
                                    ↓
                         ml_service/models/  →  inference API
```

Details: [docs/ML_PIPELINE.md](docs/ML_PIPELINE.md), [docs/DATASETS.md](docs/DATASETS.md).

## Local development

### Datasets & training

```bash
cd datasets/scripts && python download_datasets.py --list
cd ../../ml_service && python training/train_sentiment_model.py
```

### ML service (requires trained models)

```bash
cd ml_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### Backend & frontend

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│  Frontend   │────▶│   Backend   │────▶│     ML Service      │
└─────────────┘     └──────┬──────┘     │  analyzer.py        │
                           │            │  recommender.py     │
                    ┌──────▼──────┐     └──────────▲──────────┘
                    │ PostgreSQL  │                │
                    └─────────────┘         models/ │ datasets/
                                              (train) (prepare)
```

See [docs/MVP_SCOPE.md](docs/MVP_SCOPE.md) and [docs/TASKS.md](docs/TASKS.md).
