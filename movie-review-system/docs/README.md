# Documentation

| Document | Description |
|----------|-------------|
| [MVP_SCOPE.md](MVP_SCOPE.md) | Scope and service boundaries |
| [TASKS.md](TASKS.md) | Implementation backlog |
| [API_SPEC.md](API_SPEC.md) | REST API draft |
| [DB_SCHEMA.md](DB_SCHEMA.md) | Planned PostgreSQL schema |
| [DATASETS.md](DATASETS.md) | Data sources and local setup |
| [ML_PIPELINE.md](ML_PIPELINE.md) | Train → evaluate → deploy workflow |

## Before running the ML service

1. Download and preprocess data (`datasets/scripts/`)
2. Train models (`ml_service/training/`)
3. Ensure `ml_service/models/manifest.json` and artifact directories exist

The inference service will not start without trained model files.
