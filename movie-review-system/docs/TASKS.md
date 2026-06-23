# Implementation Tasks

## Datasets

- [ ] Implement `download_datasets.py` for IMDb, SemEval, MAMS, MovieLens
- [ ] Implement `preprocess_reviews.py` → `processed/sentiment/`
- [ ] Implement `prepare_absa_data.py` → `processed/absa/`

## ML training (`ml_service/training/`)

- [ ] Implement `train_sentiment_model.py`
- [ ] Implement `train_absa_model.py`
- [ ] Add recommender training script
- [ ] Implement `evaluate_model.py` → `datasets/processed/eval/`
- [ ] Write `models/manifest.json` from training scripts

## ML inference (`ml_service/app/`)

- [ ] Implement `ReviewAnalyzer._load_models()` and `analyze()`
- [ ] Implement `MovieRecommender._load_model()` and `recommend()`
- [ ] Wire `review_features` from backend into recommendations

## Backend

- [ ] ORM models and Alembic migrations
- [ ] Auth, movies, reviews, watchlist
- [ ] `review_service` → ML `/analyze`, persist analysis
- [ ] `recommendation_service` → ML `/recommend` with user analysis history

## Frontend

- [ ] Auth, movie pages, review form with analysis display
- [ ] Recommendations and watchlist UI

## DevOps

- [ ] CI: lint, test, verify model_loader errors without artifacts
- [ ] Document full local setup in README
