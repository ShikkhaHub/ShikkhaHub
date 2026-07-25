// Core type definitions for ShikkhaHub frontend

// ==================== LOCATION TYPES ====================

export interface Division {
  id: number;
  name_en: string;
  name_bn?: string;
}

export interface District {
  id: number;
  name_en: string;
  name_bn?: string;
  division_id: number;
  division?: Division;
}

export interface Upazila {
  id: number;
  name_en: string;
  name_bn?: string;
  district_id: number;
  district?: District;
}

// ==================== INSTITUTION TYPES ====================

export interface InstitutionType {
  id: number;
  name: string;
  category?: string;
  display_order: number;
}

export interface InstitutionContact {
  id: number;
  institution_id: number;
  contact_type: string; // admission, admin, registrar, principal
  name?: string;
  designation?: string;
  phone?: string;
  email?: string;
  is_primary: boolean;
}

export interface InstitutionRequirement {
  id: number;
  institution_id: number;
  requirement_type: string; // admission, scholarship, transfer
  level: string; // hsc, undergraduate, graduate
  min_gpa?: number;
  required_subjects?: string;
  admission_test_required: boolean;
  admission_test_details?: string;
  application_process?: string;
  documents_required?: string;
  fees?: string;
  deadlines?: string;
}

export interface Institution {
  id: number;
  name_en: string;
  name_bn?: string;
  short_name?: string;
  slug: string;
  type_id: number;
  type?: InstitutionType;
  established_year?: number;
  upazila_id?: number;
  upazila?: Upazila;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  description?: string;
  history?: string;
  data_source?: string; // bmeb, ugc, manual, scraped
  verification_status: 'verified' | 'pending' | 'flagged';
  last_updated?: string;
  is_active: boolean;
  is_featured: boolean;
  view_count: number;
  search_count: number;
  latitude?: number;
  longitude?: number;
  // Related data
  contacts?: InstitutionContact[];
  requirements?: InstitutionRequirement[];
  courses?: Course[];
  affiliations?: Affiliation[];
  // Computed fields
  division_name?: string;
  district_name?: string;
}

// ==================== COURSE & SUBJECT TYPES ====================

export interface CourseType {
  id: number;
  name: string;
  category?: string;
}

export interface Course {
  id: number;
  institution_id: number;
  name: string;
  course_type_id?: number;
  course_type?: CourseType;
  duration?: string;
  degree_awarded?: string;
  description?: string;
  fees?: string;
  subjects?: Subject[];
}

export interface Subject {
  id: number;
  name_en: string;
  name_bn?: string;
  code?: string;
  category?: string;
}

// ==================== AFFILIATION TYPES ====================

export interface EducationBoard {
  id: number;
  name: string;
  short_code?: string;
}

export interface UniversityGrantCommission {
  id: number;
  name: string;
  short_code?: string;
}

export interface Affiliation {
  id: number;
  institution_id: number;
  institution?: Institution;
  parent_institution_id?: number;
  parent_institution?: Institution;
  affiliation_type: string;
}

// ==================== SEARCH TYPES ====================

export interface SearchFilters {
  type_id?: number;
  type_name?: string;
  division_id?: number;
  division_name?: string;
  district_id?: number;
  district_name?: string;
  verification_status?: string;
  is_featured?: boolean;
  established_year_from?: number;
  established_year_to?: number;
}

export interface SearchResult {
  items: Institution[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  query?: string;
  source?: string;
  fuzzy_score?: number;
  match_type?: string;
  relevance_score?: number;
  personalization_boost?: number;
}

export interface AutocompleteSuggestion {
  id: number;
  name: string;
  short_name?: string;
  slug: string;
  type?: string;
}

export interface FuzzySearchResult extends Institution {
  fuzzy_score: number;
  match_type: 'fuzzy';
}

export interface PopularSearch {
  query: string;
  search_count: number;
  result_count?: number;
}

// ==================== USER TYPES ====================

export type UserRole = 'user' | 'admin' | 'super_admin' | 'moderator';

export interface User {
  id: number;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  phone?: string;
  avatar_url?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at?: string;
  last_login?: string;
  preferred_language: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

// ==================== API TYPES ====================

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  success: boolean;
  message?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ==================== ANALYTICS TYPES ====================

export interface SearchEvent {
  id: number;
  query: string;
  user_id?: number;
  session_id?: string;
  filters_used?: string;
  results_count: number;
  clicked_result: boolean;
  clicked_institution_id?: number;
  search_duration_ms?: number;
  created_at: string;
}

export interface PageViewEvent {
  id: number;
  path: string;
  user_id?: number;
  session_id?: string;
  institution_id?: number;
  institution_name?: string;
  referrer?: string;
  device_type?: string;
  created_at: string;
}

export interface ClickEvent {
  id: number;
  event_type: string; // compare, favorite, share, contact
  element_id?: string;
  element_text?: string;
  page_path: string;
  institution_id?: number;
  user_id?: number;
  session_id?: string;
  created_at: string;
}

// ==================== COMPARE TYPES ====================

export interface CompareItem {
  id: number;
  name_en: string;
  name_bn?: string;
  short_name?: string;
  type?: string;
  established_year?: number;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
}

// ==================== REVIEW & Q&A TYPES ====================

export interface Review {
  id: number;
  institution_id: number;
  user_id: number;
  user?: User;
  rating: number;
  title?: string;
  content: string;
  status: 'pending' | 'approved' | 'rejected';
  helpful_count: number;
  created_at: string;
  updated_at?: string;
}

export interface Question {
  id: number;
  institution_id?: number;
  user_id: number;
  user?: User;
  title: string;
  content: string;
  status: string;
  vote_count: number;
  answer_count: number;
  created_at: string;
}

export interface Answer {
  id: number;
  question_id: number;
  user_id: number;
  user?: User;
  content: string;
  is_best_answer: boolean;
  vote_count: number;
  created_at: string;
}

// ==================== UI TYPES ====================

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

export type Theme = 'light' | 'dark' | 'system';

// ==================== ADMIN TYPES ====================

export interface DashboardStats {
  total_institutions: number;
  total_users: number;
  total_reviews: number;
  pending_verifications: number;
  recent_institutions: Institution[];
  popular_searches: PopularSearch[];
}

export interface BackupMetadata {
  id: string;
  created_at: string;
  status: string;
  backup_type: string;
  file_size_bytes: number;
  checksum: string;
  compressed: boolean;
  tables_backed_up: number;
  rows_backed_up: number;
}

// ==================== UTILITY TYPES ====================

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
  data?: T;
  loading: boolean;
  error?: Error;
}
