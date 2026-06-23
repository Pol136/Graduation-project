import type { Movie } from "./movie";

export interface WatchlistItem {
  watchlist_id: number;
  movie_id: number;
  added_at: string;
  movie: Movie;
}

export interface WatchlistRemoveResponse {
  message: string;
}
