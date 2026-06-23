# Model Artifacts

Trained checkpoints for inference. **Not committed to Git** — generate locally via training scripts.

## Generate artifacts

```bash
# 1. Prepare data
cd datasets/scripts
python download_datasets.py --list
python preprocess_reviews.py
python prepare_absa_data.py

# 2. Train models
cd ../../ml_service
python training/train_sentiment_model.py
python training/train_absa_model.py

# 3. Evaluate (optional)
python training/evaluate_model.py --component sentiment
```

## Expected layout

```
models/
  manifest.json                  # Created by training scripts (optional legacy layout)
  sentiment/                     # Document-level sentiment model
  absa/                          # Aspect-based sentiment model
  recommender/                   # Recommendation model
  rating_regressor.joblib        # Kinopoisk-trained rating model (HistGradientBoosting)
  rating_feature_columns.json    # Feature names for inference alignment
  rating_model_metadata.json     # MAE, RMSE, R2, training metadata
```

Generate rating artifacts with:

```bash
cd ml_service
python training/prepare_rating_dataset.py --sample-size 4000
python training/train_rating_model.py
```

Copy [manifest.json.example](manifest.json.example) as a reference. Training scripts should write `manifest.json` when saving checkpoints.

## Inference

The ML service loads these artifacts at startup via `app/model_loader.py`. If directories are missing or empty, the service **will not start** and returns a clear error.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_DIR` | `./models` | Root directory for checkpoints |
| `DATASETS_DIR` | `../datasets` | Training data location |
| `PROCESSED_DATA_DIR` | `../datasets/processed` | Processed splits |
