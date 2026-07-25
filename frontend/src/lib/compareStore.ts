import type { Institution } from './api'

const STORAGE_KEY = 'shikkhahub_compare'
const MAX_COMPARE = 3

export function getComparisonList(): Institution[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

export function addToComparison(institution: Institution): { success: boolean; message?: string } {
  const current = getComparisonList()
  
  // Check if already added
  if (current.some(i => i.id === institution.id)) {
    return { success: false, message: 'Already in comparison list' }
  }
  
  // Check max limit
  if (current.length >= MAX_COMPARE) {
    return { success: false, message: `Can only compare up to ${MAX_COMPARE} institutions` }
  }
  
  const updated = [...current, institution]
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  return { success: true }
}

export function removeFromComparison(institutionId: number): void {
  const current = getComparisonList()
  const updated = current.filter(i => i.id !== institutionId)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
}

export function clearComparison(): void {
  localStorage.removeItem(STORAGE_KEY)
}

export function isInComparison(institutionId: number): boolean {
  const current = getComparisonList()
  return current.some(i => i.id === institutionId)
}

export function getComparisonCount(): number {
  return getComparisonList().length
}
