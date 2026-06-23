import { useState } from "react";
import { Link } from "react-router-dom";
import { watchlistApi } from "../../api/watchlistApi";
import { ApiError } from "../../api/client";
import type { Recommendation } from "../../types/recommendation";
import { formatGenres, formatRating } from "../../utils/labels";
import { isAuthenticated } from "../../utils/auth";

interface RecommendationCardProps {
  item: Recommendation;
}

export default function RecommendationCard({ item }: RecommendationCardProps) {
  const movie = item.movie;
  const [watchlistMsg, setWatchlistMsg] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  if (!movie) return null;

  async function handleAddWatchlist() {
    if (!isAuthenticated()) return;
    setAdding(true);
    setWatchlistMsg(null);
    try {
      await watchlistApi.addToWatchlist(movie!.movie_id);
      setWatchlistMsg("Фильм добавлен в список «Смотреть позже».");
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setWatchlistMsg("Фильм уже в списке «Смотреть позже».");
      } else {
        setWatchlistMsg("Не удалось добавить в список.");
      }
    } finally {
      setAdding(false);
    }
  }

  return (
    <article className="card recommendation-card">
      <span className="recommendation-rank">#{item.rank_position}</span>
      {movie.poster_url ? (
        <img
          src={movie.poster_url}
          alt={movie.title}
          style={{ width: 80, borderRadius: 4 }}
        />
      ) : (
        <div
          className="movie-card-poster-placeholder"
          style={{ width: 80, aspectRatio: "2/3" }}
        >
          Нет
        </div>
      )}
      <div style={{ flex: 1 }}>
        <h3 style={{ margin: "0 0 0.25rem" }}>
          <Link to={`/movies/${movie.movie_id}`}>{movie.title}</Link>
        </h3>
        <p className="movie-card-meta">
          {movie.release_year ?? "—"} · {formatGenres(movie.genres)}
        </p>
        <p className="movie-card-meta">
          Вероятность рекомендации:{" "}
          {Math.round(item.recommendation_score * 100)}%
          {movie.external_rating != null &&
            ` · TMDB: ${formatRating(movie.external_rating)}`}
        </p>
        {isAuthenticated() && (
          <button
            type="button"
            className="btn"
            onClick={handleAddWatchlist}
            disabled={adding}
            style={{ marginTop: "0.5rem" }}
          >
            Добавить в Смотреть позже
          </button>
        )}
        {watchlistMsg && (
          <p className="alert alert-info" style={{ marginTop: "0.5rem" }}>
            {watchlistMsg}
          </p>
        )}
      </div>
    </article>
  );
}
