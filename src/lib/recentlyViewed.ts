const STORAGE_KEY = 'shikkhahub_recently_viewed'
const MAX_ITEMS = 10

export interface RecentlyViewedItem {
  id: number
  slug: string
  name_en: string
  name_bn?: string
  type_name?: string
  short_name?: string
  division_name?: string
  viewed_at: string
}

export function getRecentlyViewed(): RecentlyViewedItem[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (!data) return []
    return JSON.parse(data)
  } catch {
    return []
  }
}

export function addToRecentlyViewed(institution: Omit<RecentlyViewedItem, 'viewed_at'>): void {
  try {
    const current = getRecentlyViewed()
    
    // Remove if already exists (to move to front)
    const filtered = current.filter(item => item.id !== institution.id)
    
    // Add new item at front
    const newItem: RecentlyViewedItem = {
      ...institution,
      viewed_at: new Date().toISOString()
    }
    
    const updated = [newItem, ...filtered].slice(0, MAX_ITEMS)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  } catch {
    // Ignore storage errors
  }
}

export function clearRecentlyViewed(): void {
  localStorage.removeItem(STORAGE_KEY)
}
