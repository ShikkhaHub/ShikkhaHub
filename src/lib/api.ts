const API_BASE_URL = import.meta.env.DEV ? '/api/v1' : 'http://localhost:8000/api/v1'

export interface Division {
  id: number
  name_en: string
  name_bn?: string
  code: string
  district_count: number
}

export interface Institution {
  id: number
  name_en: string
  name_bn?: string
  short_name?: string
  slug: string
  type_name?: string
  established_year?: number
  address?: string
  phone?: string
  email?: string
  website?: string
  division_name?: string
  district_name?: string
  upazila_name?: string
  verification_status: string
  is_featured: boolean
  view_count: number
  data_source?: string
  last_updated: string
}

export interface InstitutionListResponse {
  items: Institution[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface SearchFilters {
  q?: string
  type_id?: number
  division_id?: number
  district_id?: number
  verification_status?: string
  page?: number
  page_size?: number
}

export async function searchInstitutions(filters: SearchFilters): Promise<InstitutionListResponse> {
  const params = new URLSearchParams()
  
  if (filters.q) params.append('q', filters.q)
  if (filters.type_id) params.append('type_id', filters.type_id.toString())
  if (filters.division_id) params.append('division_id', filters.division_id.toString())
  if (filters.district_id) params.append('district_id', filters.district_id.toString())
  if (filters.verification_status) params.append('verification_status', filters.verification_status)
  if (filters.page) params.append('page', filters.page.toString())
  if (filters.page_size) params.append('page_size', filters.page_size.toString())
  
  const response = await fetch(`${API_BASE_URL}/institutions/search?${params}`)
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  
  return response.json()
}

export async function getInstitutions(filters: SearchFilters = {}): Promise<InstitutionListResponse> {
  const params = new URLSearchParams()
  
  if (filters.type_id) params.append('type_id', filters.type_id.toString())
  if (filters.division_id) params.append('division_id', filters.division_id.toString())
  if (filters.verification_status) params.append('verification_status', filters.verification_status)
  if (filters.page) params.append('page', filters.page.toString())
  if (filters.page_size) params.append('page_size', filters.page_size.toString())
  
  const response = await fetch(`${API_BASE_URL}/institutions/?${params}`)
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  
  return response.json()
}

export async function getInstitutionBySlug(slug: string): Promise<Institution> {
  const response = await fetch(`${API_BASE_URL}/institutions/${slug}`)
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  
  return response.json()
}

export async function getDivisions(): Promise<Division[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/locations/divisions`)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Divisions API error:', response.status, errorText)
      throw new Error(`API error: ${response.status} - ${errorText}`)
    }
    
    const data = await response.json()
    return data as Division[]
  } catch (error) {
    console.error('Failed to fetch divisions:', error)
    throw error
  }
}
