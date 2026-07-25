// Institution API endpoints
import { api } from './client';
import type {
  Institution,
  InstitutionType,
  InstitutionContact,
  InstitutionRequirement,
  SearchFilters,
  SearchResult,
} from '../types';

// ==================== INSTITUTIONS ====================

export interface GetInstitutionsParams extends SearchFilters {
  page?: number;
  page_size?: number;
  q?: string;
}

export async function getInstitutions(
  params: GetInstitutionsParams = {}
): Promise<SearchResult> {
  const queryParams = new URLSearchParams();

  // Add all params to query string
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      queryParams.append(key, String(value));
    }
  });

  const queryString = queryParams.toString();
  const endpoint = `/institutions${queryString ? `?${queryString}` : ''}`;

  return api.get<SearchResult>(endpoint, false);
}

export async function getInstitutionBySlug(slug: string): Promise<Institution> {
  return api.get<Institution>(`/institutions/${slug}`, false);
}

export async function getInstitutionById(id: number): Promise<Institution> {
  return api.get<Institution>(`/institutions/${id}`, false);
}

export async function createInstitution(
  data: Partial<Institution>
): Promise<Institution> {
  return api.post<Institution>('/institutions', data, true);
}

export async function updateInstitution(
  id: number,
  data: Partial<Institution>
): Promise<Institution> {
  return api.put<Institution>(`/institutions/${id}`, data, true);
}

export async function deleteInstitution(id: number): Promise<void> {
  return api.delete<void>(`/institutions/${id}`, true);
}

// ==================== INSTITUTION TYPES ====================

export async function getInstitutionTypes(): Promise<InstitutionType[]> {
  return api.get<InstitutionType[]>('/institutions/types', false);
}

// ==================== CONTACTS ====================

export async function getInstitutionContacts(
  institutionId: number
): Promise<InstitutionContact[]> {
  return api.get<InstitutionContact[]>(
    `/institutions/${institutionId}/contacts`,
    false
  );
}

export async function addInstitutionContact(
  institutionId: number,
  data: Partial<InstitutionContact>
): Promise<InstitutionContact> {
  return api.post<InstitutionContact>(
    `/institutions/${institutionId}/contacts`,
    data,
    true
  );
}

// ==================== REQUIREMENTS ====================

export async function getInstitutionRequirements(
  institutionId: number
): Promise<InstitutionRequirement[]> {
  return api.get<InstitutionRequirement[]>(
    `/institutions/${institutionId}/requirements`,
    false
  );
}

// ==================== FEATURED & POPULAR ====================

export async function getFeaturedInstitutions(
  limit: number = 6
): Promise<Institution[]> {
  return api.get<Institution[]>(`/institutions/featured?limit=${limit}`, false);
}

export async function getPopularInstitutions(
  limit: number = 10
): Promise<Institution[]> {
  return api.get<Institution[]>(`/institutions/popular?limit=${limit}`, false);
}

// ==================== COMPARE ====================

export async function getInstitutionsForCompare(
  ids: number[]
): Promise<Institution[]> {
  const idString = ids.join(',');
  return api.get<Institution[]>(`/institutions/compare?ids=${idString}`, false);
}

// ==================== ANALYTICS ====================

export async function trackInstitutionView(
  institutionId: number,
  sessionId?: string
): Promise<void> {
  // This uses the analytics endpoint
  const data = {
    event_type: 'pageview',
    institution_id: institutionId,
    page_path: `/institutions/${institutionId}`,
    session_id: sessionId,
  };

  // Fire and forget - don't wait for response
  try {
    await api.post('/analytics/track/click', data, false);
  } catch {
    // Silently fail - analytics shouldn't break user experience
  }
}
