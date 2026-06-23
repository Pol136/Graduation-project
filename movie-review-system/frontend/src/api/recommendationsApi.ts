import { apiRequest, buildQuery } from "./client";
import type {
  Recommendation,
  RecommendationRun,
  RecommendationRunDetail,
} from "../types/recommendation";

export const recommendationsApi = {
  getRecommendations: (limit = 10, refresh = false) =>
    apiRequest<Recommendation[]>(
      `/recommendations${buildQuery({ limit, refresh })}`
    ),

  refreshRecommendations: (limit = 10) =>
    apiRequest<Recommendation[]>(
      `/recommendations${buildQuery({ limit, refresh: true })}`
    ),

  getRecommendationRuns: () =>
    apiRequest<RecommendationRun[]>("/recommendations/runs"),

  getRecommendationRunById: (runId: number) =>
    apiRequest<RecommendationRunDetail>(`/recommendations/runs/${runId}`),
};
