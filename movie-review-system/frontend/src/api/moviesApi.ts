import { apiRequest, buildQuery } from "./client";
import type { Movie, MovieSummary } from "../types/movie";

export const moviesApi = {
  getMovies: (limit = 20, offset = 0) =>
    apiRequest<Movie[]>(
      `/movies${buildQuery({ limit, offset })}`
    ),

  searchMovies: (q: string, limit = 20, offset = 0) =>
    apiRequest<Movie[]>(
      `/movies/search${buildQuery({ q, limit, offset })}`
    ),

  getMovieById: (movieId: number) =>
    apiRequest<Movie>(`/movies/${movieId}`),

  getMovieSummary: (movieId: number, refresh = false) =>
    apiRequest<MovieSummary>(
      `/movies/${movieId}/summary${buildQuery({ refresh })}`
    ),
};
