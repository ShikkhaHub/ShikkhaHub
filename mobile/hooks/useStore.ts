import { create } from 'zustand';
import { apiService, Institution, UserProfile } from '@services/api';

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  setToken: (token: string | null) => void;
}

interface SearchState {
  query: string;
  results: Institution[];
  isLoading: boolean;
  error: string | null;
  setQuery: (query: string) => void;
  search: (query: string) => Promise<void>;
  clearResults: () => void;
}

interface SavedState {
  institutions: Institution[];
  isLoading: boolean;
  error: string | null;
  fetchSaved: () => Promise<void>;
  saveInstitution: (id: string) => Promise<void>;
  removeSavedInstitution: (id: string) => Promise<void>;
  isSaved: (id: string) => boolean;
}

interface UIState {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  lastSearchLocation?: {
    latitude: number;
    longitude: number;
  };
  setSearchLocation: (lat: number, lon: number) => void;
}

// Auth Store
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const { token, user } = await apiService.login(email, password);
      set({ user, token, isLoading: false });
      apiService.setToken(token);
    } catch (error) {
      set({
        error: apiService.handleError(error),
        isLoading: false,
      });
      throw error;
    }
  },

  register: async (email: string, password: string, name: string) => {
    set({ isLoading: true, error: null });
    try {
      const { token, user } = await apiService.register(email, password, name);
      set({ user, token, isLoading: false });
      apiService.setToken(token);
    } catch (error) {
      set({
        error: apiService.handleError(error),
        isLoading: false,
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true, error: null });
    try {
      await apiService.logout();
      set({ user: null, token: null, isLoading: false });
    } catch (error) {
      set({
        error: apiService.handleError(error),
        isLoading: false,
      });
      throw error;
    }
  },

  setToken: (token: string | null) => {
    set({ token });
    apiService.setToken(token);
  },
}));

// Search Store
export const useSearchStore = create<SearchState>((set, get) => ({
  query: '',
  results: [],
  isLoading: false,
  error: null,

  setQuery: (query: string) => {
    set({ query });
  },

  search: async (query: string) => {
    set({ isLoading: true, error: null, query });
    try {
      const response = await apiService.searchInstitutions({ query });
      set({ results: response.data, isLoading: false });
    } catch (error) {
      set({
        error: apiService.handleError(error),
        isLoading: false,
      });
    }
  },

  clearResults: () => {
    set({ results: [], query: '', error: null });
  },
}));

// Saved Institutions Store
export const useSavedStore = create<SavedState>((set, get) => ({
  institutions: [],
  isLoading: false,
  error: null,

  fetchSaved: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiService.getSavedInstitutions();
      set({ institutions: response.data, isLoading: false });
    } catch (error) {
      set({
        error: apiService.handleError(error),
        isLoading: false,
      });
    }
  },

  saveInstitution: async (id: string) => {
    try {
      await apiService.saveInstitution(id);
      const state = get();
      // Refetch to ensure consistency
      await state.fetchSaved();
    } catch (error) {
      set({
        error: apiService.handleError(error),
      });
    }
  },

  removeSavedInstitution: async (id: string) => {
    try {
      await apiService.removeSavedInstitution(id);
      const state = get();
      // Refetch to ensure consistency
      await state.fetchSaved();
    } catch (error) {
      set({
        error: apiService.handleError(error),
      });
    }
  },

  isSaved: (id: string) => {
    const state = get();
    return state.institutions.some((inst) => inst.id === id);
  },
}));

// UI Store
export const useUIStore = create<UIState>((set) => ({
  isDarkMode: false,

  toggleDarkMode: () => {
    set((state) => ({ isDarkMode: !state.isDarkMode }));
  },

  setSearchLocation: (latitude: number, longitude: number) => {
    set({ lastSearchLocation: { latitude, longitude } });
  },
}));
