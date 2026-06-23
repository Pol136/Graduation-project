import { FormEvent, useCallback, useEffect, useState } from "react";
import { moviesApi } from "../api/moviesApi";
import { ApiError } from "../api/client";
import MovieList from "../components/movies/MovieList";
import ErrorMessage from "../components/ui/ErrorMessage";
import Loading from "../components/ui/Loading";
import type { Movie } from "../types/movie";

const PAGE_SIZE = 20;

export default function MoviesPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const loadMovies = useCallback(
    async (query: string, nextOffset: number, append: boolean) => {
      const data = query.trim()
        ? await moviesApi.searchMovies(query.trim(), PAGE_SIZE, nextOffset)
        : await moviesApi.getMovies(PAGE_SIZE, nextOffset);
      setHasMore(data.length === PAGE_SIZE);
      setMovies((prev) => (append ? [...prev, ...data] : data));
    },
    []
  );

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    loadMovies(activeQuery, 0, false)
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
  }, [activeQuery, loadMovies]);

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    setOffset(0);
    setActiveQuery(searchQuery);
  }

  function handleClearSearch() {
    setSearchQuery("");
    setActiveQuery("");
    setOffset(0);
  }

  async function handleLoadMore() {
    const nextOffset = offset + PAGE_SIZE;
    setLoadingMore(true);
    try {
      await loadMovies(activeQuery, nextOffset, true);
      setOffset(nextOffset);
    } catch {
      setError("Не удалось загрузить данные.");
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <>
      <h1 className="page-title">Фильмы</h1>
      <form className="search-bar" onSubmit={handleSearch}>
        <input
          type="search"
          placeholder="Поиск по названию..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit" className="btn btn-primary">
          Найти
        </button>
        {activeQuery && (
          <button type="button" className="btn" onClick={handleClearSearch}>
            Сбросить
          </button>
        )}
      </form>
      {error && <ErrorMessage message={error} />}
      {loading ? (
        <Loading />
      ) : (
        <>
          <MovieList
            movies={movies}
            emptyMessage={
              activeQuery
                ? `По запросу «${activeQuery}» ничего не найдено.`
                : "В каталоге пока нет фильмов."
            }
          />
          {hasMore && (
            <p style={{ marginTop: "1rem", textAlign: "center" }}>
              <button
                type="button"
                className="btn"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? "Загрузка..." : "Загрузить ещё"}
              </button>
            </p>
          )}
        </>
      )}
    </>
  );
}
