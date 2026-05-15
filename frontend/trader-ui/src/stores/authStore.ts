import { create } from 'zustand';
import { authApi, settingsApi } from '../lib/api';
import { applyTraderUiTheme, clearTraderUiTheme, normaliseUiPrefs } from '../lib/traderUiTheme';

interface AuthState {
  isAuthenticated: boolean;
  user: string | null;
  fullName: string | null;
  roles: string[];
  initialized: boolean;
  loading: boolean;
  error: string | null;

  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

async function hydrateUiFromServer(): Promise<void> {
  try {
    const res = await settingsApi.get();
    const ui = res.data?.message?.ui;
    if (ui) applyTraderUiTheme(normaliseUiPrefs(ui as Record<string, unknown>));
  } catch {
    /* settings optional at bootstrap */
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  fullName: null,
  roles: [],
  initialized: false,
  loading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ loading: true, error: null });
    try {
      await authApi.login(username, password);
      const res = await authApi.getLoggedUser();
      let roles: string[] = [];
      try {
        const rolesRes = await authApi.getRoles();
        roles = rolesRes.data.message || [];
      } catch { /* ignore */ }
      set({
        isAuthenticated: true,
        user: res.data.message,
        fullName: res.data.message,
        roles,
        initialized: true,
        loading: false,
      });
      void hydrateUiFromServer();
    } catch (err: any) {
      const message =
        err.response?.data?.message || err.response?.data?.exc || 'Login failed. Please check your credentials.';
      set({ loading: false, error: message, isAuthenticated: false, initialized: true });
      throw err;
    }
  },

  logout: async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore
    }
    clearTraderUiTheme();
    set({ isAuthenticated: false, user: null, fullName: null, roles: [], initialized: true });
  },

  checkAuth: async () => {
    try {
      const res = await authApi.getLoggedUser();
      if (res.data.message && res.data.message !== 'Guest') {
        let roles: string[] = [];
        try {
          const rolesRes = await authApi.getRoles();
          roles = rolesRes.data.message || [];
        } catch { /* ignore */ }
        set({
          isAuthenticated: true,
          user: res.data.message,
          fullName: res.data.message,
          roles,
          initialized: true,
        });
        void hydrateUiFromServer();
      } else {
        clearTraderUiTheme();
        set({ isAuthenticated: false, user: null, roles: [], initialized: true });
      }
    } catch {
      clearTraderUiTheme();
      set({ isAuthenticated: false, user: null, roles: [], initialized: true });
    }
  },

  clearError: () => set({ error: null }),
}));
