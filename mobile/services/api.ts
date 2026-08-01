import axios, { AxiosInstance, AxiosError } from 'axios';
import Constants from 'expo-constants';

interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

interface Institution {
  id: string;
  name: string;
  type: string;
  division: string;
  district: string;
  latitude?: number;
  longitude?: number;
  description?: string;
  phone?: string;
  email?: string;
  website?: string;
  established_year?: number;
  logo_url?: string;
  rating?: number;
  review_count?: number;
}

interface SearchParams {
  query?: string;
  type?: string;
  division?: string;
  district?: string;
  limit?: number;
  offset?: number;
  latitude?: number;
  longitude?: number;
  radius?: number;
}

interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  saved_institutions?: string[];
  created_at: string;
}

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    const baseURL = Constants.expoConfig?.extra?.apiUrl || 'https://api.shikkhahub.edu.bd/api/v1';

    this.api = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'ShikkhaHub-Mobile/1.0.0',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - clear token and redirect to login
          this.token = null;
          // TODO: Trigger logout action in store
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(email: string, password: string): Promise<{ token: string; user: UserProfile }> {
    const response = await this.api.post('/auth/login', { email, password });
    this.token = response.data.token;
    return response.data;
  }

  async register(email: string, password: string, name: string): Promise<{ token: string; user: UserProfile }> {
    const response = await this.api.post('/auth/register', { email, password, name });
    this.token = response.data.token;
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/auth/logout');
    } finally {
      this.token = null;
    }
  }

  setToken(token: string | null): void {
    this.token = token;
  }

  // Search & Browse
  async searchInstitutions(params: SearchParams): Promise<ApiResponse<Institution[]>> {
    const response = await this.api.get('/institutions/search', { params });
    return response.data;
  }

  async getInstitution(id: string): Promise<ApiResponse<Institution>> {
    const response = await this.api.get(`/institutions/${id}`);
    return response.data;
  }

  async getNearbyInstitutions(
    latitude: number,
    longitude: number,
    radius: number = 50
  ): Promise<ApiResponse<Institution[]>> {
    const response = await this.api.get('/institutions/nearby', {
      params: { latitude, longitude, radius },
    });
    return response.data;
  }

  async getInstitutionsByType(type: string, limit: number = 20): Promise<ApiResponse<Institution[]>> {
    const response = await this.api.get(`/institutions/type/${type}`, { params: { limit } });
    return response.data;
  }

  async getInstitutionsByDivision(division: string, limit: number = 50): Promise<ApiResponse<Institution[]>> {
    const response = await this.api.get(`/divisions/${division}/institutions`, { params: { limit } });
    return response.data;
  }

  // Autocomplete & Suggestions
  async autocomplete(query: string, limit: number = 10): Promise<ApiResponse<string[]>> {
    const response = await this.api.get('/search/autocomplete', { params: { query, limit } });
    return response.data;
  }

  async getSuggestions(): Promise<ApiResponse<Institution[]>> {
    const response = await this.api.get('/search/suggestions');
    return response.data;
  }

  // User Profile
  async getProfile(): Promise<ApiResponse<UserProfile>> {
    const response = await this.api.get('/users/profile');
    return response.data;
  }

  async updateProfile(data: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    const response = await this.api.patch('/users/profile', data);
    return response.data;
  }

  // Saved Institutions (Wishlist)
  async getSavedInstitutions(): Promise<ApiResponse<Institution[]>> {
    const response = await this.api.get('/users/saved-institutions');
    return response.data;
  }

  async saveInstitution(institutionId: string): Promise<ApiResponse<{ saved: boolean }>> {
    const response = await this.api.post(`/users/saved-institutions/${institutionId}`);
    return response.data;
  }

  async removeSavedInstitution(institutionId: string): Promise<ApiResponse<{ saved: boolean }>> {
    const response = await this.api.delete(`/users/saved-institutions/${institutionId}`);
    return response.data;
  }

  // Reviews & Ratings
  async getInstitutionReviews(institutionId: string, limit: number = 10): Promise<ApiResponse<any[]>> {
    const response = await this.api.get(`/institutions/${institutionId}/reviews`, { params: { limit } });
    return response.data;
  }

  async submitReview(
    institutionId: string,
    rating: number,
    review: string
  ): Promise<ApiResponse<{ review_id: string }>> {
    const response = await this.api.post(`/institutions/${institutionId}/reviews`, { rating, review });
    return response.data;
  }

  // FAQ & AI Assistant
  async getAIResponse(question: string, institutionId?: string): Promise<ApiResponse<{ answer: string }>> {
    const response = await this.api.post('/ai/ask', { question, institution_id: institutionId });
    return response.data;
  }

  // Categories
  async getCategories(): Promise<ApiResponse<any[]>> {
    const response = await this.api.get('/categories');
    return response.data;
  }

  async getDivisions(): Promise<ApiResponse<any[]>> {
    const response = await this.api.get('/divisions');
    return response.data;
  }

  async getDistricts(division: string): Promise<ApiResponse<any[]>> {
    const response = await this.api.get(`/divisions/${division}/districts`);
    return response.data;
  }

  // Error handling helper
  handleError(error: unknown): string {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 429) {
        return 'Too many requests. Please try again later.';
      }
      if (error.response?.status === 401) {
        return 'Authentication failed. Please log in again.';
      }
      if (error.response?.status === 403) {
        return 'Access denied.';
      }
      if (error.response?.status === 404) {
        return 'Not found.';
      }
      if (error.response?.data?.message) {
        return error.response.data.message;
      }
    }
    return 'An error occurred. Please try again.';
  }
}

export const apiService = new ApiService();
export type { Institution, SearchParams, UserProfile };
