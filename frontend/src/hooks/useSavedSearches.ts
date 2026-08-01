import { useState, useCallback } from 'react';
import { SavedSearch, SavedSearchCreate, SavedSearchUpdate, savedSearchesAPI } from '../api/saved-searches';

export interface UseSavedSearchesState {
  searches: SavedSearch[];
  selectedSearch: SavedSearch | null;
  loading: boolean;
  error: string | null;
}

export const useSavedSearches = () => {
  const [state, setState] = useState<UseSavedSearchesState>({
    searches: [],
    selectedSearch: null,
    loading: false,
    error: null,
  });

  // Fetch all saved searches
  const fetchSearches = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const result = await savedSearchesAPI.getAll();
      setState((s) => ({ ...s, searches: result.data, loading: false }));
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
    }
  }, []);

  // Create a new saved search
  const createSearch = useCallback(async (data: SavedSearchCreate) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const newSearch = await savedSearchesAPI.create(data);
      setState((s) => ({
        ...s,
        searches: [...s.searches, newSearch],
        loading: false,
      }));
      return newSearch;
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
      throw error;
    }
  }, []);

  // Update a saved search
  const updateSearch = useCallback(async (id: string, data: SavedSearchUpdate) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const updated = await savedSearchesAPI.update(id, data);
      setState((s) => ({
        ...s,
        searches: s.searches.map((s) => (s.id === id ? updated : s)),
        selectedSearch: s.selectedSearch?.id === id ? updated : s.selectedSearch,
        loading: false,
      }));
      return updated;
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
      throw error;
    }
  }, []);

  // Delete a saved search
  const deleteSearch = useCallback(async (id: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      await savedSearchesAPI.delete(id);
      setState((s) => ({
        ...s,
        searches: s.searches.filter((s) => s.id !== id),
        selectedSearch: s.selectedSearch?.id === id ? null : s.selectedSearch,
        loading: false,
      }));
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
      throw error;
    }
  }, []);

  // Toggle notifications for a search
  const toggleNotifications = useCallback(async (id: string, enabled: boolean) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const updated = await savedSearchesAPI.toggleNotifications(id, enabled);
      setState((s) => ({
        ...s,
        searches: s.searches.map((s) => (s.id === id ? updated : s)),
        selectedSearch: s.selectedSearch?.id === id ? updated : s.selectedSearch,
        loading: false,
      }));
      return updated;
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
      throw error;
    }
  }, []);

  // Select a search
  const selectSearch = useCallback((search: SavedSearch | null) => {
    setState((s) => ({ ...s, selectedSearch: search }));
  }, []);

  return {
    ...state,
    fetchSearches,
    createSearch,
    updateSearch,
    deleteSearch,
    toggleNotifications,
    selectSearch,
  };
};
