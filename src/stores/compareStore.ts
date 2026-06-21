import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Institution } from '../types';

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

interface CompareState {
  items: CompareItem[];
  maxItems: number;

  // Actions
  addItem: (institution: Institution) => { success: boolean; message: string };
  removeItem: (id: number) => void;
  clearItems: () => void;
  isInCompareList: (id: number) => boolean;
  canAddMore: () => boolean;
}

const MAX_COMPARE_ITEMS = 3;

export const useCompareStore = create<CompareState>()(
  persist(
    (set, get) => ({
      // Initial state
      items: [],
      maxItems: MAX_COMPARE_ITEMS,

      // Actions
      addItem: (institution) => {
        const { items, maxItems } = get();

        // Check if already in list
        if (items.some((item) => item.id === institution.id)) {
          return { success: true, message: 'Already in compare list' };
        }

        // Check if list is full
        if (items.length >= maxItems) {
          return {
            success: false,
            message: `You can only compare up to ${maxItems} institutions`,
          };
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

        set({ items: [...items, newItem] });
        return { success: true, message: 'Added to compare list' };
      },

      removeItem: (id) =>
        set((state) => ({
          items: state.items.filter((item) => item.id !== id),
        })),

      clearItems: () => set({ items: [] }),

      isInCompareList: (id) => {
        return get().items.some((item) => item.id === id);
      },

      canAddMore: () => {
        return get().items.length < get().maxItems;
      },
    }),
    {
      name: 'shikkhahub-compare',
    }
  )
);
