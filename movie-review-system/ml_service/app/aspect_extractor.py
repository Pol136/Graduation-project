"""
Aspect category detection via zero-shot classification (replaceable with trained ABSA later).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.config import settings
from app.model_loader import get_aspect_pipeline
from app.preprocessing import split_into_sentences, validate_review_text
from app.schemas import AspectSentiment

if TYPE_CHECKING:
    from app.sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

ASPECT_LABELS: list[str] = [
    "сюжет",
    "актерская игра",
    "персонажи",
    "визуальная составляющая",
    "музыка",
    "атмосфера",
    "режиссура",
    "темп повествования",
    "эмоциональное впечатление",
]

ASPECT_KEYWORDS: dict[str, list[str]] = {
    "сюжет": ["сюжет", "сценарий", "история", "повествование", "развитие событий", "финал", "развязка"],
    "актерская игра": ["актер", "актёр", "актриса", "игра актеров", "игра актёров", "исполнение роли"],
    "персонажи": ["персонаж", "герой", "героиня", "характер", "мотивация"],
    "визуальная составляющая": [
        "визуал",
        "картинка",
        "съемка",
        "съёмка",
        "эффекты",
        "графика",
        "операторская работа",
    ],
    "музыка": ["музыка", "саундтрек", "звук", "звуковое сопровождение"],
    "атмосфера": ["атмосфера", "настроение", "погружение", "напряжение"],
    "режиссура": ["режиссура", "режиссер", "режиссёр", "постановка"],
    "темп повествования": ["темп", "динамика", "затянуто", "затянутый", "скучно", "медленно"],
    "эмоциональное впечатление": ["эмоции", "впечатление", "трогательно", "захватывающе", "разочарование"],
}

_KEYWORD_FALLBACK_SCORE = 0.5
_NON_NEUTRAL_TIE_DELTA = 0.05


@dataclass
class _AspectCandidate:
    aspect: str
    sentence: str
    sentiment: str
    sentiment_score: float


def _keyword_aspects_for_sentence(sentence: str) -> dict[str, float]:
    """Return aspects matched by keywords with at least the fallback detection score."""
    low = sentence.lower()
    found: dict[str, float] = {}
    for aspect, keywords in ASPECT_KEYWORDS.items():
        if any(kw.lower() in low for kw in keywords):
            found[aspect] = max(found.get(aspect, 0.0), _KEYWORD_FALLBACK_SCORE)
    return found


def _zero_shot_aspects_for_sentence(pipe: object, sentence: str) -> dict[str, float]:
    """Run zero-shot classification; return label -> score for labels above threshold."""
    try:
        raw = pipe(
            sentence,
            candidate_labels=ASPECT_LABELS,
            multi_label=settings.aspect_multi_label,
        )
    except Exception as exc:
        logger.warning("Zero-shot aspect classification failed for sentence: %s", exc)
        return {}

    labels = raw.get("labels") if isinstance(raw, dict) else None
    scores = raw.get("scores") if isinstance(raw, dict) else None
    if not labels or not scores:
        return {}

    threshold = settings.aspect_confidence_threshold
    out: dict[str, float] = {}
    for label, score in zip(labels, scores, strict=False):
        s = float(score)
        if s >= threshold:
            out[str(label)] = max(out.get(str(label), 0.0), s)
    return out


def _detection_scores_for_sentence(pipe: object, sentence: str) -> dict[str, float]:
    """Merge zero-shot and keyword detections for one sentence."""
    detected = _zero_shot_aspects_for_sentence(pipe, sentence)
    for aspect, score in _keyword_aspects_for_sentence(sentence).items():
        detected[aspect] = max(detected.get(aspect, 0.0), score)
    return detected


def _merge_aspect_candidates(candidates: list[_AspectCandidate]) -> list[_AspectCandidate]:
    """Keep one candidate per aspect (highest sentiment confidence; prefer non-neutral on ties)."""
    by_aspect: dict[str, _AspectCandidate] = {}
    for cand in candidates:
        prev = by_aspect.get(cand.aspect)
        if prev is None:
            by_aspect[cand.aspect] = cand
            continue
        if cand.sentiment_score > prev.sentiment_score + _NON_NEUTRAL_TIE_DELTA:
            by_aspect[cand.aspect] = cand
            continue
        if prev.sentiment_score > cand.sentiment_score + _NON_NEUTRAL_TIE_DELTA:
            continue
        if cand.sentiment != "neutral" and prev.sentiment == "neutral":
            by_aspect[cand.aspect] = cand
        elif cand.sentiment == prev.sentiment and cand.sentiment_score > prev.sentiment_score:
            by_aspect[cand.aspect] = cand
    return list(by_aspect.values())


def extract_aspects(
    text: str,
    sentiment_analyzer: SentimentAnalyzer | None = None,
) -> list[AspectSentiment]:
    """
    Detect movie aspects per sentence (zero-shot + keywords) and assign sentence-level sentiment.
    """
    from app.sentiment_analyzer import SentimentAnalyzer

    normalized = validate_review_text(text)
    sentences = split_into_sentences(normalized)[: settings.aspect_max_sentences]
    if not sentences:
        return []

    if sentiment_analyzer is None:
        sentiment_analyzer = SentimentAnalyzer()

    pipe = get_aspect_pipeline()
    candidates: list[_AspectCandidate] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        detected = _detection_scores_for_sentence(pipe, sentence)
        if not detected:
            continue
        try:
            sent = sentiment_analyzer.analyze_text(sentence)
        except Exception as exc:
            logger.warning("Sentence sentiment failed for aspect extraction: %s", exc)
            continue
        for aspect in detected:
            candidates.append(
                _AspectCandidate(
                    aspect=aspect,
                    sentence=sentence,
                    sentiment=sent.sentiment,
                    sentiment_score=sent.score,
                )
            )

    merged = _merge_aspect_candidates(candidates)
    return [
        AspectSentiment(
            aspect=c.aspect,
            sentiment=c.sentiment,  # type: ignore[arg-type]
            score=round(max(0.0, min(1.0, c.sentiment_score)), 4),
            evidence=c.sentence,
        )
        for c in merged
    ]


def extract_aspects_placeholder(text: str) -> list:
    """Deprecated alias; use :func:`extract_aspects`."""
    return extract_aspects(text)
