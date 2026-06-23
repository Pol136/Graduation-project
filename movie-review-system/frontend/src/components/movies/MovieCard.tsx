import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Movie } from "../../types/movie";
import { formatGenres, formatRating } from "../../utils/labels";

interface MovieCardProps {
  movie: Movie;
  showDetailsLink?: boolean;
  children?: ReactNode;
}

export default function MovieCard({
  movie,
  showDetailsLink = true,
  children,
}: MovieCardProps) {
  return (
    <article className="card movie-card">
      {movie.poster_url ? (
        <img
          src={movie.poster_url}
          alt={movie.title}
          className="movie-card-poster"
        />
      ) : (
        <div className="movie-card-poster-placeholder">Нет постера</div>
      )}
      <h3>{movie.title}</h3>
      <p className="movie-card-meta">
        {movie.release_year ?? "—"} · {formatGenres(movie.genres)}
      </p>
      {movie.external_rating != null && (
        <p className="movie-card-meta">Рейтинг: {formatRating(movie.external_rating)}</p>
      )}
      {showDetailsLink && (
        <div className="movie-card-actions">
          <Link to={`/movies/${movie.movie_id}`} className="btn btn-primary">
            Подробнее
          </Link>
        </div>
      )}
      {children}
    </article>
  );
}
