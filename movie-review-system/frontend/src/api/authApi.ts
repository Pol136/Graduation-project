import { apiRequest } from "./client";
import type { LoginPayload, RegisterPayload, TokenResponse, User } from "../types/auth";

export const authApi = {
  login: (payload: LoginPayload) =>
    apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  register: (payload: RegisterPayload) =>
    apiRequest<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getMe: () => apiRequest<User>("/users/me"),
};
