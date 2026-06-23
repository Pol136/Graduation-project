import { apiRequest } from "./client";
import type { WatchlistItem, WatchlistRemoveResponse } from "../types/watchlist";

export const watchlistApi = {
  getWatchlist: () => apiRequest<WatchlistItem[]>("/watchlist"),

  addToWatchlist: (movieId: number) =>
    apiRequest<WatchlistItem>(`/watchlist/${movieId}`, { method: "POST" }),

  removeFromWatchlist: (movieId: number) =>
    apiRequest<WatchlistRemoveResponse>(`/watchlist/${movieId}`, {
      method: "DELETE",
    }),
};
