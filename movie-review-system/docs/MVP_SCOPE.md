# MVP Scope

## ML-first approach

The system is built for **real model training and inference**. The ML service requires trained artifacts in `ml_service/models/` and prepared data in `datasets/` before it will start.

## In scope

- [ ] Dataset download and preprocessing pipelines
- [ ] Sentiment and ABSA model training
- [ ] Model evaluation and metrics export
- [ ] Inference via `analyzer.py` and `recommender.py`
- [ ] User registration and JWT login
- [ ] Movie catalog
- [ ] Reviews with ML analysis persisted
- [ ] Recommendations informed by analysis results
- [ ] User watchlist
- [ ] React frontend for core flows

## Out of scope (initial release)

- Social features, notifications, admin dashboard
- External movie API sync (TMDB/OMDb)
- Multi-language reviews

## Service boundaries

| Component | Responsibility |
|-----------|----------------|
| `datasets/` | Data storage, download, preprocessing |
| `ml_service/training/` | Train and evaluate models |
| `ml_service/app/` | Load models, `/analyze`, `/recommend` |
| `backend/` | Persistence, orchestration, `ml_client` |
| `frontend/` | UI |

## Success criteria

- Datasets downloadable and preprocessable via scripts
- Training scripts produce artifacts under `ml_service/models/`
- ML service loads models and serves analysis/recommendations
- Backend integrates ML results into reviews and recommendations
- Full stack runs via Docker with volumes for `datasets/` and `models/`
