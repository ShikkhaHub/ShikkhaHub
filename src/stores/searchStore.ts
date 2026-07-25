import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Institution, SearchFilters, AutocompleteSuggestion } from '../types';

interface SearchState {
  // Search state
  query: string;
  filters: SearchFilters;
  results: Institution[];
  total: number;
  page: number;
  pageSize: number;
  pages: number;
  loading: boolean;
  error: string | null;
  suggestions: AutocompleteSuggestion[];
  hasSearched: boolean;

  // History
  searchHistory: string[];

  // Actions
  setQuery: (query: string) => void;
  setFilters: (filters: SearchFilters) => void;
  setResults: (results: Institution[], total: number, pages: number) => void;
  appendResults: (results: Institution[]) => void;
  setPage: (page: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSuggestions: (suggestions: AutocompleteSuggestion[]) => void;
  setHasSearched: (hasSearched: boolean) => void;
  addToHistory: (query: string) => void;
  clearHistory: () => void;
  reset: () => void;
}

const initialState = {
  query: '',
  filters: {},
  results: [],
  total: 0,
  page: 1,
  pageSize: 20,
  pages: 0,
  loading: false,
  error: null,
  suggestions: [],
  hasSearched: false,
};

export const useSearchStore = create<SearchState>()(
  persist(
    (set) => ({
      // Initial state
      ...initialState,
      searchHistory: [],

      // Actions
      setQuery: (query) => set({ query }),

      setFilters: (filters) => set({ filters }),

      setResults: (results, total, pages) =>
        set({
          results,
          total,
          pages,
          loading: false,
          error: null,
        }),

      appendResults: (results) =>
        set((state) => ({
          results: [...state.results, ...results],
        })),

      setPage: (page) => set({ page }),

      setLoading: (loading) => set({ loading }),

      setError: (error) => set({ error, loading: false }),

      setSuggestions: (suggestions) => set({ suggestions }),

      setHasSearched: (hasSearched) => set({ hasSearched }),

      addToHistory: (query) =>
        set((state) => {
          if (!query.trim()) return state;
          const filtered = state.searchHistory.filter((q) => q !== query);
          return {
            searchHistory: [query, ...filtered].slice(0, 20),
          };
        }),

      clearHistory: () => set({ searchHistory: [] }),

      reset: () => set({ ...initialState }),
    }),
    {
      name: 'shikkhahub-search',
      partialize: (state) => ({ searchHistory: state.searchHistory, filters: state.filters }),
    }
  )
);
