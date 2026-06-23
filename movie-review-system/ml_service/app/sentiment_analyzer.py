"""Russian document-level sentiment via Hugging Face transformers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.model_loader import get_sentiment_pipeline
from app.preprocessing import chunk_text, validate_review_text

logger = logging.getLogger(__name__)

CANONICAL = ("positive", "neutral", "negative")


@dataclass
class SentimentResult:
    sentiment: str
    score: float
    probabilities: dict[str, float]


def _normalize_class_label(raw: str, id2label: dict[int, str] | dict[str, str] | None) -> str | None:
    """Map HF / id2label strings to positive | neutral | negative."""
    label = raw.strip()
    low = label.lower()

    if "positive" in low:
        return "positive"
    if "neutral" in low:
        return "neutral"
    if "negative" in low:
        return "negative"

    if label.upper().startswith("LABEL_"):
        try:
            idx = int(label.split("_")[-1])
        except ValueError:
            return None
        if id2label is not None:
            mapped = id2label.get(idx) if isinstance(id2label, dict) else None
            if mapped is None and isinstance(id2label, dict):
                mapped = id2label.get(str(idx))  # type: ignore[arg-type]
            if mapped is not None:
                return _normalize_class_label(str(mapped), None)
        # WARNING: without id2label, numeric id order is model-specific; this matches many 3-class setups.
        fallback_by_id = {0: "negative", 1: "neutral", 2: "positive"}
        return fallback_by_id.get(idx)

    return None


def _id2label_from_model(model: Any) -> dict[int, str] | None:
    cfg = getattr(model, "config", None)
    if cfg is None:
        return None
    raw = getattr(cfg, "id2label", None)
    if not raw:
        return None
    out: dict[int, str] = {}
    for k, v in raw.items():
        try:
            out[int(k)] = str(v)
        except (TypeError, ValueError):
            continue
    return out or None


def _scores_for_chunk(pipe: Any, chunk: str) -> list[dict[str, Any]]:
    call_kw: dict[str, Any] = {
        "truncation": True,
        "max_length": settings.sentiment_max_length,
    }
    try:
        raw = pipe(chunk, **call_kw, top_k=None)
    except TypeError:
        raw = pipe(chunk, **call_kw, return_all_scores=True)

    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        return raw  # type: ignore[return-value]
    if isinstance(raw, list) and raw and isinstance(raw[0], list):
        return raw[0]  # type: ignore[return-value]
    return []


def _chunk_label_scores(
    pipe: Any,
    chunk: str,
    id2label: dict[int, str] | None,
) -> dict[str, float]:
    rows = _scores_for_chunk(pipe, chunk)
    bucket = {k: 0.0 for k in CANONICAL}
    for row in rows:
        label_raw = str(row.get("label", ""))
        score = float(row.get("score", 0.0))
        key = _normalize_class_label(label_raw, id2label)
        if key is None:
            logger.warning(
                "Unrecognized sentiment label %r; assigning score to neutral as fallback.",
                label_raw,
            )
            key = "neutral"
        bucket[key] += score
    return bucket


class SentimentAnalyzer:
    """Runs the rubert-tiny sentiment classifier with optional chunking."""

    def analyze_text(self, text: str) -> SentimentResult:
        normalized = validate_review_text(text)
        chunks = chunk_text(normalized, settings.sentiment_chunk_max_chars)
        if not chunks:
            raise ValueError("No text to analyze after chunking.")
        return self.analyze_chunks(chunks)

    def analyze_chunks(self, chunks: list[str]) -> SentimentResult:
        clean = [c.strip() for c in chunks if c.strip()]
        if not clean:
            raise ValueError("chunks must be non-empty.")
        pipe = get_sentiment_pipeline()
        model = getattr(pipe, "model", None)
        id2label = _id2label_from_model(model) if model is not None else None

        acc = {k: 0.0 for k in CANONICAL}
        for chunk in clean:
            part = _chunk_label_scores(pipe, chunk, id2label)
            for k in CANONICAL:
                acc[k] += part[k]
        n = len(clean)
        probs = {k: round(acc[k] / n, 6) for k in CANONICAL}

        winner = max(probs, key=probs.get)  # type: ignore[arg-type]
        score = float(probs[winner])
        return SentimentResult(sentiment=winner, score=score, probabilities=probs)
