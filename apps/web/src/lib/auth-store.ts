/**
 * Store global de autenticación con Zustand.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

import { authApi, type User } from "./api";

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    full_name?: string;
    organization_name?: string;
    organization_slug?: string;
  }) => Promise<void>;
  logout: () => void;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const { access_token } = await authApi.login({ email, password });
          localStorage.setItem("access_token", access_token);

          const user = await authApi.me();
          set({ user, token: access_token, isLoading: false });
        } catch (err: any) {
          const error = err?.response?.data?.detail || "Error al iniciar sesión";
          set({ isLoading: false, error });
          throw new Error(error);
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const result = await authApi.register(data);
          localStorage.setItem("access_token", result.access_token);
          set({
            user: result.user,
            token: result.access_token,
            isLoading: false,
          });
        } catch (err: any) {
          const error = err?.response?.data?.detail || "Error al registrarse";
          set({ isLoading: false, error });
          throw new Error(error);
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        set({ user: null, token: null });
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        user: state.user,
        token: state.token,
      }),
    }
  )
);
