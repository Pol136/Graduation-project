import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { moviesApi } from "../api/moviesApi";
import { reviewsApi } from "../api/reviewsApi";
import { watchlistApi } from "../api/watchlistApi";
import { ApiError } from "../api/client";
import MovieSummaryBlock from "../components/analytics/MovieSummaryBlock";
import ReviewCard from "../components/reviews/ReviewCard";
import ReviewForm from "../components/reviews/ReviewForm";
import ErrorMessage from "../components/ui/ErrorMessage";
import Loading from "../components/ui/Loading";
import type { Movie, MovieSummary } from "../types/movie";
import type { Review } from "../types/review";
import { formatGenres, formatRating } from "../utils/labels";
import { isAuthenticated } from "../utils/auth";

export default function MovieDetailsPage() {
  const { movieId } = useParams<{ movieId: string }>();
  const id = Number(movieId);

  const [movie, setMovie] = useState<Movie | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [summary, setSummary] = useState<MovieSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [watchlistMsg, setWatchlistMsg] = useState<string | null>(null);
  const [addingWatchlist, setAddingWatchlist] = useState(false);

  const loadData = useCallback(async () => {
    if (!id || Number.isNaN(id)) {
      setError("Некорректный идентификатор фильма.");
      setLoading(false);
      return;
    }
    const [movieData, reviewsData, summaryData] = await Promise.all([
      moviesApi.getMovieById(id),
      reviewsApi.getMovieReviews(id),
      moviesApi.getMovieSummary(id, false),
    ]);
    setMovie(movieData);
    setReviews(reviewsData);
    setSummary(summaryData);
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    loadData()
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.detail ?? err.message
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
  }, [loadData]);

  async function handleSubmitReview(reviewText: string, userRating: number) {
    if (!id) return;
    setReviewError(null);
    setSubmittingReview(true);
    try {
      await reviewsApi.createReview(id, { review_text: reviewText, user_rating: userRating });
      const [reviewsData, summaryData] = await Promise.all([
        reviewsApi.getMovieReviews(id),
        moviesApi.getMovieSummary(id, true),
      ]);
      setReviews(reviewsData);
      setSummary(summaryData);
    } catch (err) {
      if (err instanceof ApiError) {
        setReviewError(err.detail ?? err.message);
      } else {
        setReviewError("Не удалось отправить отзыв.");
      }
    } finally {
      setSubmittingReview(false);
    }
  }

  async function handleAddWatchlist() {
    if (!id || !isAuthenticated()) return;
    setAddingWatchlist(true);
    setWatchlistMsg(null);
    try {
      await watchlistApi.addToWatchlist(id);
      setWatchlistMsg("Фильм добавлен в список «Смотреть позже».");
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setWatchlistMsg("Фильм уже в списке «Смотреть позже».");
      } else {
        setWatchlistMsg("Не удалось добавить в список.");
      }
    } finally {
      setAddingWatchlist(false);
    }
  }

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} />;
  if (!movie) return <ErrorMessage message="Фильм не найден." />;

  return (
    <>
      <div className="movie-details card">
        {movie.poster_url ? (
          <img
            src={movie.poster_url}
            alt={movie.title}
            className="movie-details-poster"
          />
        ) : (
          <div
            className="movie-card-poster-placeholder movie-details-poster"
            style={{ width: 180 }}
          >
            Нет постера
          </div>
        )}
        <div>
          <h1 className="page-title" style={{ marginTop: 0 }}>
            {movie.title}
          </h1>
          {movie.original_title && movie.original_title !== movie.title && (
            <p className="movie-card-meta">Оригинал: {movie.original_title}</p>
          )}
          <p>
            {movie.release_year ?? "—"} · {formatGenres(movie.genres)}
            {movie.external_rating != null &&
              ` · Рейтинг: ${formatRating(movie.external_rating)}`}
          </p>
          {movie.description && <p>{movie.description}</p>}
          {isAuthenticated() && (
            <button
              type="button"
              className="btn"
              onClick={handleAddWatchlist}
              disabled={addingWatchlist}
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
      </div>

      <section className="section">
        <MovieSummaryBlock summary={summary} />
      </section>

      <section className="section">
        <h2>Отзывы ({reviews.length})</h2>
        {reviewError && <ErrorMessage message={reviewError} />}
        <ReviewForm onSubmit={handleSubmitReview} submitting={submittingReview} />
        {reviews.length === 0 ? (
          <p className="empty-state" style={{ marginTop: "1rem" }}>
            Пока нет отзывов. Будьте первым!
          </p>
        ) : (
          <div style={{ marginTop: "1rem" }}>
            {reviews.map((r) => (
              <ReviewCard key={r.review_id} review={r} />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
