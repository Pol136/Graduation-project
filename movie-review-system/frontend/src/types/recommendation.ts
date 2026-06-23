import type { Movie } from "./movie";

export interface Recommendation {
  recommendation_id: number;
  run_id: number;
  user_id: number;
  movie_id: number;
  recommendation_score: number;
  rank_position: number;
  created_at: string;
  movie: Movie | null;
}

export interface RecommendationRun {
  run_id: number;
  user_id: number;
  created_at: string;
  algorithm_version: string | null;
}

export interface RecommendationRunDetail extends RecommendationRun {
  recommendations: Recommendation[];
}
