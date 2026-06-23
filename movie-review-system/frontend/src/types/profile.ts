export interface PreferenceProfile {
  profile_id: number;
  user_id: number;
  positive_preferences: Record<string, number> | null;
  negative_preferences: Record<string, number> | null;
  aspect_weights: Record<string, number> | null;
  updated_at: string;
}
