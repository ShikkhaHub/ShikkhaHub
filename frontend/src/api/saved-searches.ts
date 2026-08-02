import { apiClient } from './client';

export interface SavedSearch {
  id: string;
  user_id: string;
  name: string;
  query: string;
  filters: Record<string, any>;
  notify: boolean;
  notify_frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
  created_at: string;
  updated_at: string;
  last_run_at?: string;
  match_count?: number;
}

export interface SavedSearchCreate {
  name: string;
  query: string;
  filters?: Record<string, any>;
  notify?: boolean;
  notify_frequency?: 'immediate' | 'daily' | 'weekly' | 'monthly';
}

export interface SavedSearchUpdate {
  name?: string;
  query?: string;
  filters?: Record<string, any>;
  notify?: boolean;
  notify_frequency?: 'immediate' | 'daily' | 'weekly' | 'monthly';
}

export const savedSearchesAPI = {
  // Create a new saved search
  create: async (data: SavedSearchCreate): Promise<SavedSearch> => {
    const response = await apiClient.post<SavedSearch>('/api/v1/saved-searches', data);
    return response;
  },

  // Get all saved searches for user
  getAll: async (limit = 50, offset = 0): Promise<{ data: SavedSearch[]; total: number }> => {
    const response = await apiClient.get<{ data: SavedSearch[]; total: number }>('/api/v1/saved-searches', {
      params: { limit, offset },
    });
    return response;
  },

  // Get specific saved search
  getById: async (id: string): Promise<SavedSearch> => {
    const response = await apiClient.get<SavedSearch>(`/api/v1/saved-searches/${id}`);
    return response;
  },

  // Update saved search
  update: async (id: string, data: SavedSearchUpdate): Promise<SavedSearch> => {
    const response = await apiClient.patch<SavedSearch>(`/api/v1/saved-searches/${id}`, data);
    return response;
  },

  // Delete saved search
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/saved-searches/${id}`);
  },

  // Run search and cache results
  runSearch: async (id: string): Promise<{ results: any[]; count: number }> => {
    const response = await apiClient.post<{ results: any[]; count: number }>(`/api/v1/saved-searches/${id}/run`);
    return response;
  },

  // Toggle notifications for a search
  toggleNotifications: async (id: string, enabled: boolean): Promise<SavedSearch> => {
    const response = await apiClient.post<SavedSearch>(
      `/api/v1/saved-searches/${id}/toggle-notifications`,
      { enabled }
    );
    return response;
  },

  // Get cached results for saved search
  getResults: async (id: string, limit = 50, offset = 0): Promise<{ data: any[]; total: number }> => {
    const response = await apiClient.get<{ data: any[]; total: number }>(`/api/v1/saved-searches/${id}/results`, {
      params: { limit, offset },
    });
    return response;
  },
};

export default savedSearchesAPI;
