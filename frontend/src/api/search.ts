// Search API endpoints
import { api } from './client';
import type {
  Institution,
  SearchResult,
  SearchFilters,
  AutocompleteSuggestion,
  PopularSearch,
} from '../types';

// ==================== BASIC SEARCH ====================

export interface SearchParams extends SearchFilters {
  q?: string;
  page?: number;
  page_size?: number;
}

export async function searchInstitutions(
  params: SearchParams = {}
): Promise<SearchResult> {
  const queryParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      queryParams.append(key, String(value));
    }
  });

  const queryString = queryParams.toString();
  const endpoint = `/search/advanced${queryString ? `?${queryString}` : ''}`;

  return api.get<SearchResult>(endpoint, false);
}

// ==================== AUTOCOMPLETE ====================

export async function getAutocompleteSuggestions(
  query: string,
  limit: number = 10
): Promise<AutocompleteSuggestion[]> {
  const response = await api.get<{ suggestions: AutocompleteSuggestion[] }>(
    `/search/autocomplete?q=${encodeURIComponent(query)}&limit=${limit}`,
    false
  );
  return response.suggestions;
}

// ==================== FUZZY SEARCH ====================

export interface FuzzySearchParams {
  q: string;
  threshold?: number;
  limit?: number;
}

export interface FuzzySearchResponse {
  query: string;
  results: Institution[];
  count: number;
  suggestions: string[];
  threshold: number;
}

export async function fuzzySearch(
  params: FuzzySearchParams
): Promise<FuzzySearchResponse> {
  const queryParams = new URLSearchParams();
  queryParams.append('q', params.q);
  if (params.threshold) queryParams.append('threshold', String(params.threshold));
  if (params.limit) queryParams.append('limit', String(params.limit));

  return api.get<FuzzySearchResponse>(
    `/search/fuzzy?${queryParams.toString()}`,
    false
  );
}

// ==================== DID YOU MEAN ====================

export interface SpellCheckResponse {
  query: string;
  suggestions: string[];
  has_corrections: boolean;
}

export async function getSpellSuggestions(
  query: string,
  limit: number = 3
): Promise<SpellCheckResponse> {
  return api.get<SpellCheckResponse>(
    `/search/did-you-mean?q=${encodeURIComponent(query)}&limit=${limit}`,
    false
  );
}

// ==================== PERSONALIZED SEARCH ====================

export interface PersonalizedSearchParams extends SearchParams {
  session_id?: string;
}

export async function personalizedSearch(
  params: PersonalizedSearchParams = {}
): Promise<SearchResult> {
  const queryParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      queryParams.append(key, String(value));
    }
  });

  const queryString = queryParams.toString();
  return api.get<SearchResult>(
    `/search/personalized${queryString ? `?${queryString}` : ''}`,
    false
  );
}

// ==================== SUGGESTIONS ====================

export interface SuggestionsResponse {
  suggestions: Institution[];
  count: number;
  personalized: boolean;
}

export async function getSuggestionsForYou(
  limit: number = 5,
  sessionId?: string
): Promise<SuggestionsResponse> {
  let url = `/search/suggestions-for-you?limit=${limit}`;
  if (sessionId) {
    url += `&session_id=${sessionId}`;
  }
  return api.get<SuggestionsResponse>(url, false);
}

// ==================== POPULAR SEARCHES ====================

export async function getPopularSearches(
  limit: number = 10
): Promise<PopularSearch[]> {
  const response = await api.get<{ popular_searches: PopularSearch[] }>(
    `/search/popular-queries?limit=${limit}`,
    false
  );
  return response.popular_searches;
}

// ==================== SEARCH ANALYTICS ====================

export interface TrackSearchParams {
  query: string;
  results_count: number;
  filters?: Record<string, unknown>;
  search_duration_ms?: number;
  session_id?: string;
}

export async function trackSearch(
  params: TrackSearchParams
): Promise<{ search_event_id: number }> {
  return api.post<{ search_event_id: number }>(
    '/analytics/track/search',
    params,
    false
  );
}

export async function trackSearchClick(
  searchEventId: number,
  institutionId: number
): Promise<void> {
  return api.post<void>(
    '/analytics/track/search-click',
    {
      search_event_id: searchEventId,
      institution_id: institutionId,
    },
    false
  );
}
