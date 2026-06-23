import { useEffect, useState } from "react";
import { reviewsApi } from "../../api/reviewsApi";
import type { Review, ReviewAnalysis } from "../../types/review";
import { formatDate, formatRating, sentimentLabel } from "../../utils/labels";
import Loading from "../ui/Loading";

interface ReviewCardProps {
  review: Review;
}

function AspectList({ aspects }: { aspects: ReviewAnalysis["aspects"] }) {
  if (!aspects?.length) return null;
  return (
    <div>
      <strong>Аспекты:</strong>
      <ul>
        {aspects.map((a, i) => (
          <li key={`${a.aspect}-${i}`}>
            {a.aspect} — {sentimentLabel(a.sentiment)}
            {a.score != null && ` (${a.score.toFixed(2)})`}
          </li>
        ))}
      </ul>
    </div>
  );
}

function AnalysisBlock({ analysis }: { analysis: ReviewAnalysis }) {
  return (
    <div className="review-analysis">
      <p>
        <strong>Тональность:</strong> {sentimentLabel(analysis.overall_sentiment)}
      </p>
      {analysis.predicted_rating != null && (
        <p>
          <strong>Предсказанная оценка:</strong>{" "}
          {formatRating(analysis.predicted_rating)}
        </p>
      )}
      <AspectList aspects={analysis.aspects} />
    </div>
  );
}

export default function ReviewCard({ review }: ReviewCardProps) {
  const [analysis, setAnalysis] = useState<ReviewAnalysis | null | undefined>(
    review.analysis ?? undefined
  );
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  useEffect(() => {
    setAnalysis(review.analysis);
  }, [review.analysis]);

  useEffect(() => {
    if (analysis !== undefined) return;
    let cancelled = false;
    setLoadingAnalysis(true);
    reviewsApi
      .getReviewAnalysis(review.review_id)
      .then((data) => {
        if (!cancelled) setAnalysis(data);
      })
      .catch(() => {
        if (!cancelled) setAnalysis(null);
      })
      .finally(() => {
        if (!cancelled) setLoadingAnalysis(false);
      });
    return () => {
      cancelled = true;
    };
  }, [review.review_id, analysis]);

  return (
    <article className="card review-card">
      <div className="review-card-header">
        <strong>{review.username ?? `Пользователь #${review.user_id}`}</strong>
        <span>
          Оценка: {formatRating(review.user_rating)} · {formatDate(review.created_at)}
        </span>
      </div>
      <p>{review.review_text}</p>
      {loadingAnalysis && <Loading text="Загрузка анализа..." />}
      {analysis && <AnalysisBlock analysis={analysis} />}
    </article>
  );
}
