import { apiRequest, buildQuery } from "./client";
import type { Review, ReviewAnalysis, ReviewCreate, ReviewUpdate } from "../types/review";

export const reviewsApi = {
  getMovieReviews: (movieId: number, limit = 50, offset = 0) =>
    apiRequest<Review[]>(
      `/movies/${movieId}/reviews${buildQuery({ limit, offset })}`
    ),

  createReview: (movieId: number, payload: ReviewCreate) =>
    apiRequest<Review>(`/movies/${movieId}/reviews`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateReview: (reviewId: number, payload: ReviewUpdate) =>
    apiRequest<Review>(`/reviews/${reviewId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteReview: (reviewId: number) =>
    apiRequest<void>(`/reviews/${reviewId}`, { method: "DELETE" }),

  getReviewAnalysis: (reviewId: number) =>
    apiRequest<ReviewAnalysis>(`/reviews/${reviewId}/analysis`),
};
