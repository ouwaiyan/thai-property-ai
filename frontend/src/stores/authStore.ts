import { create } from 'zustand';
import type { UserMe } from '@/types/auth';
import * as api from '@/lib/api';
import { setTokens, clearTokens, getAccessToken } from '@/lib/auth';

interface AuthState {
  user: UserMe | null;
  loading: boolean;
  initialized: boolean;

  login: (email: string, password: string) => Promise<UserMe>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: false,
  initialized: false,

  login: async (email: string, password: string) => {
    set({ loading: true });
    try {
      const tokens = await api.login({ email, password });
      setTokens(tokens.access_token, tokens.refresh_token);
      const user = await api.getMe();
      set({ user, loading: false });
      return user;
    } catch (e: unknown) {
      set({ loading: false });
      const err = e as { response?: { data?: { detail?: string } }; message?: string };
      const detail = err?.response?.data?.detail || err?.message || 'auth.invalid_credentials';
      throw new Error(detail);
    }
  },

  logout: () => {
    clearTokens();
    set({ user: null, initialized: true });
  },

  fetchMe: async () => {
    try {
      const user = await api.getMe();
      set({ user });
      return;
    } catch {
      clearTokens();
      set({ user: null });
    }
  },

  initialize: async () => {
    const token = getAccessToken();
    if (!token) {
      set({ initialized: true });
      return;
    }
    try {
      const user = await api.getMe();
      set({ user, initialized: true });
    } catch {
      clearTokens();
      set({ initialized: true });
    }
  },
}));
