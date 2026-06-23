export interface Movie {
  movie_id: number;
  tmdb_id: number | null;
  title: string;
  original_title: string | null;
  description: string | null;
  genres: string[] | null;
  release_year: number | null;
  poster_url: string | null;
  external_rating: number | null;
}

export interface MovieSummary {
  summary_id: number | null;
  movie_id: number;
  average_user_rating: number | null;
  average_predicted_rating: number | null;
  review_count: number;
  sentiment_distribution: Record<string, number> | null;
  aspect_scores: Record<string, number> | null;
  aspect_frequency: Record<string, number> | null;
  updated_at: string | null;
}
