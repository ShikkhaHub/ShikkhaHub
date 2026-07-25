// API module exports

// Client
export { api, ApiException, getToken, setToken, removeToken, API_BASE_URL } from './client';

// Auth
export {
  login,
  register,
  logout,
  getCurrentUser,
  refreshToken,
  requestPasswordReset,
  resetPassword,
  changePassword,
  updateProfile,
  uploadAvatar,
} from './auth';

// Institutions
export {
  getInstitutions,
  getInstitutionBySlug,
  getInstitutionById,
  createInstitution,
  updateInstitution,
  deleteInstitution,
  getInstitutionTypes,
  getInstitutionContacts,
  addInstitutionContact,
  getInstitutionRequirements,
  getFeaturedInstitutions,
  getPopularInstitutions,
  getInstitutionsForCompare,
  trackInstitutionView,
  type GetInstitutionsParams,
} from './institutions';

// Search
export {
  searchInstitutions,
  getAutocompleteSuggestions,
  fuzzySearch,
  getSpellSuggestions,
  personalizedSearch,
  getSuggestionsForYou,
  getPopularSearches,
  trackSearch,
  trackSearchClick,
  type SearchParams,
  type FuzzySearchParams,
  type FuzzySearchResponse,
  type SpellCheckResponse,
  type PersonalizedSearchParams,
  type SuggestionsResponse,
  type TrackSearchParams,
} from './search';

// Locations
export {
  getDivisions,
  getDistricts,
  getDistrictsByDivision,
  getUpazilas,
  getUpazilasByDistrict,
  getAllLocations,
  type LocationHierarchy,
} from './locations';
