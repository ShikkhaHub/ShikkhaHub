// Locations API endpoints
import { api } from './client';
import type { Division, District, Upazila } from '../types';

// ==================== DIVISIONS ====================

export async function getDivisions(): Promise<Division[]> {
  return api.get<Division[]>('/locations/divisions', false);
}

// ==================== DISTRICTS ====================

export async function getDistricts(divisionId?: number): Promise<District[]> {
  let endpoint = '/locations/districts';
  if (divisionId) {
    endpoint += `?division_id=${divisionId}`;
  }
  return api.get<District[]>(endpoint, false);
}

export async function getDistrictsByDivision(
  divisionId: number
): Promise<District[]> {
  return api.get<District[]>(`/locations/divisions/${divisionId}/districts`, false);
}

// ==================== UPAZILAS ====================

export async function getUpazilas(districtId?: number): Promise<Upazila[]> {
  let endpoint = '/locations/upazilas';
  if (districtId) {
    endpoint += `?district_id=${districtId}`;
  }
  return api.get<Upazila[]>(endpoint, false);
}

export async function getUpazilasByDistrict(districtId: number): Promise<Upazila[]> {
  return api.get<Upazila[]>(`/locations/districts/${districtId}/upazilas`, false);
}

// ==================== FULL LOCATION DATA ====================

export interface LocationHierarchy {
  divisions: Division[];
  districts: District[];
  upazilas: Upazila[];
}

export async function getAllLocations(): Promise<LocationHierarchy> {
  const [divisions, districts, upazilas] = await Promise.all([
    getDivisions(),
    getDistricts(),
    getUpazilas(),
  ]);

  return { divisions, districts, upazilas };
}
