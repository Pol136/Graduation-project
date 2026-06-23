import { apiRequest } from "./client";
import type { PreferenceProfile } from "../types/profile";

export const profileApi = {
  getPreferenceProfile: () =>
    apiRequest<PreferenceProfile>("/users/me/preference-profile"),
};
