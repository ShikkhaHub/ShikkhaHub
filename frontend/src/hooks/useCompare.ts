import { useCallback, useMemo } from 'react';
import { useLocalStorage } from './useLocalStorage';
import type { Institution } from '../types';

const STORAGE_KEY = 'shikkhahub_compare_list';
const MAX_COMPARE_ITEMS = 3;

interface CompareItem {
  id: number;
  name_en: string;
  name_bn?: string;
  slug: string;
  short_name?: string;
  type?: string;
  established_year?: number;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
}

interface UseCompareReturn {
  compareList: CompareItem[];
  addToCompare: (institution: Institution) => boolean;
  removeFromCompare: (id: number) => void;
  clearCompare: () => void;
  isInCompareList: (id: number) => boolean;
  canAddMore: boolean;
  isFull: boolean;
}

export function useCompare(): UseCompareReturn {
  const [compareList, setCompareList, clearCompare] = useLocalStorage<CompareItem[]>(
    STORAGE_KEY,
    []
  );

  const canAddMore = useMemo(() => compareList.length < MAX_COMPARE_ITEMS, [compareList.length]);
  const isFull = useMemo(() => compareList.length >= MAX_COMPARE_ITEMS, [compareList.length]);

  const addToCompare = useCallback(
    (institution: Institution): boolean => {
      // Check if already in list
      if (compareList.some((item) => item.id === institution.id)) {
        return true; // Already added, consider it success
      }

      // Check if list is full
      if (compareList.length >= MAX_COMPARE_ITEMS) {
        return false; // Can't add more
      }

      const newItem: CompareItem = {
        id: institution.id,
        name_en: institution.name_en,
        name_bn: institution.name_bn,
        slug: institution.slug,
        short_name: institution.short_name,
        type: institution.type?.name,
        established_year: institution.established_year,
        address: institution.address,
        phone: institution.phone,
        email: institution.email,
        website: institution.website,
      };

      setCompareList((prev) => [...prev, newItem]);
      return true;
    },
    [compareList, setCompareList]
  );

  const removeFromCompare = useCallback(
    (id: number) => {
      setCompareList((prev) => prev.filter((item) => item.id !== id));
    },
    [setCompareList]
  );

  const isInCompareList = useCallback(
    (id: number) => {
      return compareList.some((item) => item.id === id);
    },
    [compareList]
  );

  return {
    compareList,
    addToCompare,
    removeFromCompare,
    clearCompare,
    isInCompareList,
    canAddMore,
    isFull,
  };
}
