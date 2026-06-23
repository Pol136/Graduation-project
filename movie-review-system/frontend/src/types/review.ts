export interface ReviewAspect {
  aspect: string;
  sentiment: string;
  score?: number;
  evidence?: string;
}

export interface ReviewAnalysis {
  analysis_id: number;
  review_id: number;
  overall_sentiment: string;
  predicted_rating: number | null;
  aspects: ReviewAspect[] | null;
  analyzed_at: string;
  model_version: string | null;
}

export interface Review {
  review_id: number;
  movie_id: number;
  user_id: number;
  username?: string;
  review_text: string;
  user_rating: number;
  created_at: string;
  updated_at: string;
  analysis?: ReviewAnalysis | null;
}

export interface ReviewCreate {
  review_text: string;
  user_rating: number;
}

export interface ReviewUpdate {
  review_text?: string;
  user_rating?: number;
}
