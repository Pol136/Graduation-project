import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { watchlistApi } from "../api/watchlistApi";
import { ApiError } from "../api/client";
import ErrorMessage from "../components/ui/ErrorMessage";
import Loading from "../components/ui/Loading";
import type { WatchlistItem } from "../types/watchlist";
import { formatGenres, formatRating } from "../utils/labels";

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<number | null>(null);

  const loadWatchlist = useCallback(async () => {
    const data = await watchlistApi.getWatchlist();
    setItems(data);
  }, []);

  useEffect(() => {
    let cancelled = false;
    loadWatchlist()
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Не удалось загрузить данные."
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [loadWatchlist]);

  async function handleRemove(movieId: number) {
    setRemovingId(movieId);
    try {
      await watchlistApi.removeFromWatchlist(movieId);
      setItems((prev) => prev.filter((i) => i.movie_id !== movieId));
    } catch {
      setError("Не удалось удалить фильм из списка.");
    } finally {
      setRemovingId(null);
    }
  }

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <>
      <h1 className="page-title">Смотреть позже</h1>
      {items.length === 0 ? (
        <p className="empty-state">Список «Смотреть позже» пока пуст.</p>
      ) : (
        <div className="card-grid">
          {items.map((item) => (
            <article key={item.watchlist_id} className="card movie-card">
              {item.movie.poster_url ? (
                <img
                  src={item.movie.poster_url}
                  alt={item.movie.title}
                  className="movie-card-poster"
                />
              ) : (
                <div className="movie-card-poster-placeholder">Нет постера</div>
              )}
              <h3>
                <Link to={`/movies/${item.movie.movie_id}`}>{item.movie.title}</Link>
              </h3>
              <p className="movie-card-meta">
                {item.movie.release_year ?? "—"} · {formatGenres(item.movie.genres)}
              </p>
              {item.movie.external_rating != null && (
                <p className="movie-card-meta">
                  Рейтинг: {formatRating(item.movie.external_rating)}
                </p>
              )}
              <div className="movie-card-actions">
                <Link
                  to={`/movies/${item.movie.movie_id}`}
                  className="btn btn-primary"
                >
                  Подробнее
                </Link>
                <button
                  type="button"
                  className="btn"
                  style={{ marginLeft: "0.5rem" }}
                  onClick={() => handleRemove(item.movie_id)}
                  disabled={removingId === item.movie_id}
                >
                  Удалить
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
