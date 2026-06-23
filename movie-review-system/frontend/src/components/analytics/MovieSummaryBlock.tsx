import type { MovieSummary } from "../../types/movie";
import { formatRating } from "../../utils/labels";
import AspectScoresChart from "./AspectScoresChart";
import SentimentChart from "./SentimentChart";

interface MovieSummaryBlockProps {
  summary: MovieSummary | null;
}

function hasAnalyticsData(summary: MovieSummary): boolean {
  if (summary.review_count > 0) return true;
  const sent = summary.sentiment_distribution;
  if (sent && Object.values(sent).some((v) => v > 0)) return true;
  if (summary.aspect_scores && Object.keys(summary.aspect_scores).length > 0) {
    return true;
  }
  return false;
}

export default function MovieSummaryBlock({ summary }: MovieSummaryBlockProps) {
  if (!summary || !hasAnalyticsData(summary)) {
    return (
      <p className="empty-state">Пока недостаточно данных для аналитики.</p>
    );
  }

  const sentiment = summary.sentiment_distribution ?? {};
  const aspectScores = summary.aspect_scores ?? {};
  const aspectFreq = summary.aspect_frequency ?? {};

  return (
    <div className="card section">
      <h2>Аналитика по отзывам</h2>
      <div className="summary-stats">
        <div className="stat-item">
          <strong>Средняя оценка пользователей</strong>
          {formatRating(summary.average_user_rating)}
        </div>
        <div className="stat-item">
          <strong>Средняя оценка по текстам отзывов</strong>
          {formatRating(summary.average_predicted_rating)}
        </div>
        <div className="stat-item">
          <strong>Количество отзывов</strong>
          {summary.review_count}
        </div>
      </div>

      {Object.keys(sentiment).length > 0 && (
        <div className="chart-block">
          <h4>Распределение тональности</h4>
          <SentimentChart distribution={sentiment} />
        </div>
      )}

      {Object.keys(aspectScores).length > 0 && (
        <div className="chart-block">
          <h4>Оценки по аспектам</h4>
          <AspectScoresChart aspectScores={aspectScores} />
        </div>
      )}

      {Object.keys(aspectFreq).length > 0 && (
        <div className="chart-block">
          <h4>Частота аспектов</h4>
          <table className="key-value-table">
            <thead>
              <tr>
                <th>Аспект</th>
                <th>Упоминаний</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(aspectFreq)
                .sort((a, b) => b[1] - a[1])
                .map(([aspect, count]) => (
                  <tr key={aspect}>
                    <td>{aspect}</td>
                    <td>{count}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
