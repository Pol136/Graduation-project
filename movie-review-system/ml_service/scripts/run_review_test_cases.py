"""Run diploma review-analysis test cases against the real ML pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parents[1]
if str(ML_ROOT) not in sys.path:
    sys.path.insert(0, str(ML_ROOT))

from app.analyzer import analyze_review  # noqa: E402

TEST_CASES = [
    {
        "id": 1,
        "type": "явно положительный",
        "review_text": (
            "Потрясающий фильм! Сюжет захватывает с первых минут, актёры играют блестяще, "
            "музыка идеально подчёркивает каждую сцену. Один из лучших фильмов года."
        ),
        "user_rating": 9.0,
    },
    {
        "id": 2,
        "type": "явно отрицательный",
        "review_text": (
            "Разочарование полное. Сюжет предсказуемый и скучный, актёрская игра слабая, "
            "визуальные эффекты дешёвые. Время потрачено зря."
        ),
        "user_rating": 2.0,
    },
    {
        "id": 3,
        "type": "нейтральный",
        "review_text": (
            "Обычный фильм, ничего особенного. Сюжет стандартный, актёры играют нормально, "
            "смотреть можно, но вряд ли пересмотрю."
        ),
        "user_rating": 5.0,
    },
    {
        "id": 4,
        "type": "смешанный",
        "review_text": (
            "Сюжет держит в напряжении и финал неожиданный, но актёрская игра местами слабая, "
            "а музыка раздражает. В целом посмотреть можно."
        ),
        "user_rating": 6.0,
    },
    {
        "id": 5,
        "type": "короткий простой",
        "review_text": "Классный фильм, понравилось.",
        "user_rating": 8.0,
    },
    {
        "id": 6,
        "type": "несколько аспектов",
        "review_text": (
            "Сюжет интересный и непредсказуемый. Актёры играют убедительно. "
            "Музыка запоминающаяся. Визуальная составляющая на высоте — красивые кадры и эффекты. "
            "Атмосфера мрачная и напряжённая, полностью погружает в историю."
        ),
        "user_rating": 8.5,
    },
    {
        "id": 7,
        "type": "оценка не совпадает с текстом",
        "review_text": (
            "Фильм скучный, сюжет затянутый, актёры играют без эмоций, визуал посредственный. "
            "Едва досмотрел до конца."
        ),
        "user_rating": 9.0,
    },
]


def main() -> None:
    results = []
    for case in TEST_CASES:
        response = analyze_review(case["review_text"], case["user_rating"])
        results.append(
            {
                "id": case["id"],
                "type": case["type"],
                "review_text": case["review_text"],
                "user_rating": case["user_rating"],
                "overall_sentiment": response.overall_sentiment,
                "sentiment_score": response.sentiment_score,
                "predicted_rating": response.predicted_rating,
                "rating_comparison": response.rating_comparison.model_dump(),
                "aspects": [a.model_dump() for a in response.aspects],
                "model_version": response.model_version,
            }
        )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
