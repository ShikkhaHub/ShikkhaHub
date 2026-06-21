import { useState, useEffect, useCallback } from 'react';
import { getInstitutionBySlug, getInstitutionById } from '../api';
import type { Institution } from '../types';

interface UseInstitutionOptions {
  trackView?: boolean;
}

interface UseInstitutionReturn {
  institution: Institution | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useInstitution(
  slugOrId: string | number,
  options: UseInstitutionOptions = {}
): UseInstitutionReturn {
  const { trackView = true } = options;

  const [institution, setInstitution] = useState<Institution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchInstitution = useCallback(async () => {
    if (!slugOrId) {
      setInstitution(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data =
        typeof slugOrId === 'number'
          ? await getInstitutionById(slugOrId)
          : await getInstitutionBySlug(slugOrId);

      setInstitution(data);

      // Track view if enabled
      if (trackView && data.id) {
        // Analytics tracking is handled in the API layer
        import('../api').then(({ trackInstitutionView }) => {
          trackInstitutionView(data.id).catch(() => {
            // Silently fail tracking
          });
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load institution'));
      setInstitution(null);
    } finally {
      setLoading(false);
    }
  }, [slugOrId, trackView]);

  useEffect(() => {
    fetchInstitution();
  }, [fetchInstitution]);

  return {
    institution,
    loading,
    error,
    refetch: fetchInstitution,
  };
}
