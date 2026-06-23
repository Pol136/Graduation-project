import type { Movie } from "../../types/movie";
import MovieCard from "./MovieCard";

interface MovieListProps {
  movies: Movie[];
  emptyMessage?: string;
}

export default function MovieList({
  movies,
  emptyMessage = "Фильмы не найдены.",
}: MovieListProps) {
  if (movies.length === 0) {
    return <p className="empty-state">{emptyMessage}</p>;
  }

  return (
    <div className="card-grid">
      {movies.map((movie) => (
        <MovieCard key={movie.movie_id} movie={movie} />
      ))}
    </div>
  );
}
