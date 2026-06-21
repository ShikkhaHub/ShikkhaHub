import { useState, useEffect, useCallback } from 'react';
import { searchInstitutions, getAutocompleteSuggestions, trackSearch } from '../api';
import { useDebounce } from './useDebounce';
import type { SearchParams, SearchResult, AutocompleteSuggestion, Institution } from '../types';

interface UseSearchOptions {
  debounceMs?: number;
  minQueryLength?: number;
  trackAnalytics?: boolean;
}

interface UseSearchReturn {
  query: string;
  setQuery: (query: string) => void;
  results: Institution[];
  total: number;
  page: number;
  pageSize: number;
  pages: number;
  loading: boolean;
  error: Error | null;
  suggestions: AutocompleteSuggestion[];
  hasSearched: boolean;
  search: (params?: Partial<SearchParams>) => Promise<void>;
  loadMore: () => Promise<void>;
  reset: () => void;
}

export function useSearch(
  initialParams: SearchParams = {},
  options: UseSearchOptions = {}
): UseSearchReturn {
  const {
    debounceMs = 300,
    minQueryLength = 2,
    trackAnalytics = true,
  } = options;

  const [query, setQuery] = useState(initialParams.q || '');
  const [results, setResults] = useState<Institution[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(initialParams.page || 1);
  const [pageSize] = useState(initialParams.page_size || 20);
  const [pages, setPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchEventId, setSearchEventId] = useState<number | null>(null);

  const debouncedQuery = useDebounce(query, debounceMs);

  // Fetch autocomplete suggestions
  useEffect(() => {
    if (debouncedQuery.length >= minQueryLength) {
      getAutocompleteSuggestions(debouncedQuery, 5)
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    } else {
      setSuggestions([]);
    }
  }, [debouncedQuery, minQueryLength]);

  // Perform search
  const search = useCallback(async (params: Partial<SearchParams> = {}) => {
    if (!query && !params.q) {
      setResults([]);
      setHasSearched(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const searchParams: SearchParams = {
        q: query,
        page,
        page_size: pageSize,
        ...initialParams,
        ...params,
      };

      const response: SearchResult = await searchInstitutions(searchParams);

      setResults(response.items);
      setTotal(response.total);
      setPages(response.pages);
      setHasSearched(true);

      // Track search analytics
      if (trackAnalytics) {
        try {
          const trackResponse = await trackSearch({
            query: searchParams.q || '',
            results_count: response.total,
            filters: {
              type_id: searchParams.type_id,
              division_id: searchParams.division_id,
            },
          });
          setSearchEventId(trackResponse.search_event_id);
        } catch {
          // Silently fail tracking
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Search failed'));
    } finally {
      setLoading(false);
    }
  }, [query, page, pageSize, initialParams, trackAnalytics]);

  // Load more results (pagination)
  const loadMore = useCallback(async () => {
    if (page >= pages || loading) return;

    const nextPage = page + 1;
    setLoading(true);

    try {
      const response = await searchInstitutions({
        q: query,
        page: nextPage,
        page_size: pageSize,
        ...initialParams,
      });

      setResults((prev) => [...prev, ...response.items]);
      setPage(nextPage);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load more'));
    } finally {
      setLoading(false);
    }
  }, [query, page, pages, pageSize, initialParams, loading]);

  // Reset search state
  const reset = useCallback(() => {
    setQuery('');
    setResults([]);
    setTotal(0);
    setPage(1);
    setPages(0);
    setError(null);
    setSuggestions([]);
    setHasSearched(false);
    setSearchEventId(null);
  }, []);

  return {
    query,
    setQuery,
    results,
    total,
    page,
    pageSize,
    pages,
    loading,
    error,
    suggestions,
    hasSearched,
    search,
    loadMore,
    reset,
  };
}
