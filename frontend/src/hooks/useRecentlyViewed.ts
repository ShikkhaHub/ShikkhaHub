import { useCallback, useMemo } from 'react';
import { useLocalStorage } from './useLocalStorage';
import type { Institution } from '../types';

const STORAGE_KEY = 'shikkhahub_recently_viewed';
const MAX_ITEMS = 10;

interface RecentlyViewedItem {
  id: number;
  name_en: string;
  name_bn?: string;
  slug: string;
  short_name?: string;
  type?: string;
  viewed_at: string;
}

interface UseRecentlyViewedReturn {
  recentlyViewed: RecentlyViewedItem[];
  addToRecentlyViewed: (institution: Institution) => void;
  removeFromRecentlyViewed: (id: number) => void;
  clearRecentlyViewed: () => void;
  isRecentlyViewed: (id: number) => boolean;
}

export function useRecentlyViewed(): UseRecentlyViewedReturn {
  const [recentlyViewed, setRecentlyViewed, clearRecentlyViewed] =
    useLocalStorage<RecentlyViewedItem[]>(STORAGE_KEY, []);

  const addToRecentlyViewed = useCallback(
    (institution: Institution) => {
      setRecentlyViewed((prev) => {
        // Remove if already exists
        const filtered = prev.filter((item) => item.id !== institution.id);

        // Add new item at the beginning
        const newItem: RecentlyViewedItem = {
          id: institution.id,
          name_en: institution.name_en,
          name_bn: institution.name_bn,
          slug: institution.slug,
          short_name: institution.short_name,
          type: institution.type?.name,
          viewed_at: new Date().toISOString(),
        };

        // Keep only MAX_ITEMS
        return [newItem, ...filtered].slice(0, MAX_ITEMS);
      });
    },
    [setRecentlyViewed]
  );

  const removeFromRecentlyViewed = useCallback(
    (id: number) => {
      setRecentlyViewed((prev) => prev.filter((item) => item.id !== id));
    },
    [setRecentlyViewed]
  );

  const isRecentlyViewed = useCallback(
    (id: number) => {
      return recentlyViewed.some((item) => item.id === id);
    },
    [recentlyViewed]
  );

  return {
    recentlyViewed,
    addToRecentlyViewed,
    removeFromRecentlyViewed,
    clearRecentlyViewed,
    isRecentlyViewed,
  };
}
