/**
 * Auth API module: login, register, logout, profile, password management.
 */

import apiClient, { setTokens, clearTokens } from "./client";

export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: "owner" | "admin" | "editor" | "viewer";
  avatar: string | null;
  job_title: string;
  phone: string;
  timezone: string;
  email_notifications: boolean;
  organization: string | null;
  organization_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
  organization_name?: string;
}

export interface AuthResponse {
  user: User;
  tokens: { access: string; refresh: string };
}

export const authApi = {
  login: async (data: LoginPayload): Promise<AuthResponse> => {
    const response = await apiClient.post("/auth/login/", data);
    const tokens = { access: response.data.access, refresh: response.data.refresh };
    const user = response.data.user;
    setTokens(tokens);
    localStorage.setItem("insightboard_user", JSON.stringify(user));
    return { user, tokens };
  },

  register: async (data: RegisterPayload): Promise<AuthResponse> => {
    const response = await apiClient.post("/auth/register/", data);
    const { user, tokens } = response.data;
    setTokens(tokens);
    localStorage.setItem("insightboard_user", JSON.stringify(user));
    return { user, tokens };
  },

  logout: async (): Promise<void> => {
    try {
      const tokensStr = localStorage.getItem("insightboard_tokens");
      if (tokensStr) {
        const tokens = JSON.parse(tokensStr);
        await apiClient.post("/auth/logout/", { refresh: tokens.refresh });
      }
    } finally {
      clearTokens();
    }
  },

  getProfile: () => apiClient.get<User>("/auth/profile/"),

  updateProfile: (data: Partial<User>) =>
    apiClient.patch<User>("/auth/profile/", data),

  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.put("/auth/change-password/", {
      old_password: oldPassword,
      new_password: newPassword,
    }),

  getCurrentUser: (): User | null => {
    const stored = localStorage.getItem("insightboard_user");
    return stored ? JSON.parse(stored) : null;
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem("insightboard_tokens");
  },
};
