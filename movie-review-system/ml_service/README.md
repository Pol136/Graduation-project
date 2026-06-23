# ML service (inference)

The service exposes JSON endpoints under `/ml` for movie **review analysis**.

## Current behavior

### Overall sentiment

Uses [`cointegrated/rubert-tiny-sentiment-balanced`](https://huggingface.co/cointegrated/rubert-tiny-sentiment-balanced) (`text-classification`, CPU). Lazy-loaded on the first `POST /ml/analyze-review` call, not during `GET /ml/health`.

### Preprocessing

`app/preprocessing.py` normalizes whitespace and line breaks, validates non-empty input, splits sentences (`.`, `!`, `?`), and chunks long reviews (`SENTIMENT_CHUNK_MAX_CHARS`) for the sentiment model (`SENTIMENT_MAX_LENGTH`).

### Aspect extraction (category detection)

Implemented in `app/aspect_extractor.py` as **sentence-level aspect category detection** (intermediate step before trained ABSA).

| Piece | Detail |
|--------|--------|
| Model | [`MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`](https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-mnli-xnli) via `zero-shot-classification` |
| Approach | For each sentence (up to `ASPECT_MAX_SENTENCES`), classify against predefined Russian aspect labels |
| Threshold | `ASPECT_CONFIDENCE_THRESHOLD` (default `0.55`), `ASPECT_MULTI_LABEL=true` |
| Fallback | `ASPECT_KEYWORDS` dictionary for stability |
| Aspect sentiment | `SentimentAnalyzer` on the sentence where the aspect was detected |

### Rating prediction (improved interpretable baseline — active)

`app/rating_predictor.py` computes `predicted_rating` with **`predict_rating_baseline()`**:

1. **Overall sentiment rating** from document sentiment + confidence (positive / neutral / negative formulas).
2. **Aspect rating** — average per-aspect contribution from aspect-level sentiment scores (or overall rating if no aspects).
3. **Balance adjustment** — bonus from positive aspect share, penalty from negative aspect share.
4. **Blend** — `0.55 × overall + 0.45 × aspect + bonus − penalty`, clipped to 1–10.

The active API **always** uses this baseline (`predict_rating()` returns source `improved_baseline`). It does **not** load `rating_regressor.joblib`, even if the file exists on disk.

### Rating regressor training (experimental / future work)

Scripts under `training/` and `app/feature_extractor.py` / `app/rating_model_loader.py` can build a Kinopoisk-trained `HistGradientBoostingRegressor`. That pipeline is kept for experiments and diploma follow-up; it is **not** wired into `/ml/analyze-review` in the current version.

Pipeline at inference: preprocess → sentiment → aspects → **improved baseline rating** → comparison.

### Rating comparison

`compare_user_and_predicted_rating` compares optional user 1–10 rating with the predicted rating.

## Endpoints

| Method | Path | Purpose |
|--------|------|--------|
| `GET` | `/ml/health` | Liveness; `sentiment_model_loaded`, `aspect_model_loaded`, `rating_method` (`improved_baseline`), optional `rating_model_*` flags for legacy monitoring. **Does not load** any model. |
| `POST` | `/ml/analyze-review` | Full pipeline. Lazy-loads sentiment and aspect HF models on first call; rating uses the interpretable baseline only. |

## `model_version` in responses

Identifies the **full analysis pipeline** (sentiment + aspects + rating method):

`sentiment-rubert-tiny-v1+aspect-zero-shot-mdeberta-v1+rating-improved-baseline-v1`

`GET /ml/health` reports service release via `version` (`ML_SERVICE_VERSION`), not this pipeline string.

## Train the rating regressor (optional experiment)

From `ml_service/` (requires network for dataset + HF models during feature prep):

```bash
pip install -r requirements.txt
python training/prepare_rating_dataset.py --sample-size 4000
python training/train_rating_model.py
```

Outputs:

- `../datasets/processed/kinopoisk_rating_features_4000.csv` — feature matrix + `rating` target
- `../datasets/processed/kinopoisk_rating_sample_4000.csv` — sampled raw reviews
- `models/rating_regressor.joblib` — trained regressor
- `models/rating_feature_columns.json` — column order for inference
- `models/rating_model_metadata.json` — MAE, RMSE, R², timestamps

`prepare_rating_dataset.py` supports `--force` to recompute, `--random-state`, and skips work if the features CSV already exists.

## Dependencies

`requirements.txt` pins **NumPy 1.26.x** with **SciPy** and **scikit-learn**. **NumPy must stay below 2** for compatibility with current SciPy/sklearn wheels used by transformers pipelines.

```bash
pip install -r requirements.txt --force-reinstall
```

## Run locally

```bash
cd ml_service
python -m uvicorn app.main:app --reload --port 8001
```

### Validation

`POST http://127.0.0.1:8001/ml/analyze-review`:

```json
{
  "review_text": "Фильм очень понравился. Сюжет держит в напряжении, музыка отлично поддерживает атмосферу, но актерская игра местами слабая.",
  "user_rating": 8.0
}
```

Expected: sentiment, non-empty `aspects` when relevant, `predicted_rating` from regressor if artifacts exist, `rating_comparison` filled, `model_version` including the rating suffix.

## Tests

```bash
python -m pytest tests/ -m "not integration"
```

Optional (downloads real HF models / dataset):

```bash
RUN_ML_INTEGRATION=1 python -m pytest tests/ -m integration -v
```
