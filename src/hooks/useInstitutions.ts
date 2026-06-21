import { useState, useEffect, useCallback } from 'react';
import { getInstitutions } from '../api';
import type { Institution, SearchFilters } from '../types';

interface UseInstitutionsParams extends SearchFilters {
  page?: number;
  page_size?: number;
  q?: string;
}

interface UseInstitutionsReturn {
  institutions: Institution[];
  total: number;
  page: number;
  pages: number;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  setPage: (page: number) => void;
}

export function useInstitutions(
  params: UseInstitutionsParams = {}
): UseInstitutionsReturn {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(params.page || 1);
  const [pages, setPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchInstitutions = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getInstitutions({
        ...params,
        page,
        page_size: params.page_size || 20,
      });

      setInstitutions(response.items);
      setTotal(response.total);
      setPages(response.pages);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load institutions'));
      setInstitutions([]);
    } finally {
      setLoading(false);
    }
  }, [params, page]);

  useEffect(() => {
    fetchInstitutions();
  }, [fetchInstitutions]);

  // Update page when params.page changes
  useEffect(() => {
    if (params.page && params.page !== page) {
      setPage(params.page);
    }
  }, [params.page, page]);

  return {
    institutions,
    total,
    page,
    pages,
    loading,
    error,
    refetch: fetchInstitutions,
    setPage,
  };
}
