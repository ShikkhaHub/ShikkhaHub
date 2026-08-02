// API Client for ShikkhaHub
import type { ApiError } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

// Token management
const getToken = (): string | null => localStorage.getItem('access_token');
const setToken = (token: string): void => localStorage.setItem('access_token', token);
const removeToken = (): void => localStorage.removeItem('access_token');

// API Error class
export class ApiException extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ApiException';
  }
}

// Request options interface
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  requireAuth?: boolean;
  params?: Record<string, unknown>;
}

// Main API client function
async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = 'GET', body, headers = {}, requireAuth = true, params } = options;

  // Build URL
  let url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  // Append query parameters
  if (params) {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== '') {
        search.append(key, String(value));
      }
    }
    const qs = search.toString();
    if (qs) {
      url += (url.includes('?') ? '&' : '?') + qs;
    }
  }

  // Build headers
  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...headers,
  };

  // Add auth token if required
  if (requireAuth) {
    const token = getToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  // Build request options
  const fetchOptions: RequestInit = {
    method,
    headers: requestHeaders,
  };

  // Add body for non-GET requests
  if (body && method !== 'GET') {
    fetchOptions.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, fetchOptions);
    const data = await response.json();

    // Handle error responses
    if (!response.ok) {
      const error: ApiError = data.error || {
        code: 'UNKNOWN_ERROR',
        message: data.detail || 'An error occurred',
        details: data.details,
      };

      // Handle authentication errors
      if (response.status === 401) {
        removeToken();
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
      }

      throw new ApiException(
        response.status,
        error.code,
        error.message,
        error.details
      );
    }

    return data as T;
  } catch (error) {
    // Re-throw ApiException as-is
    if (error instanceof ApiException) {
      throw error;
    }

    // Wrap network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiException(
        0,
        'NETWORK_ERROR',
        'Unable to connect to the server. Please check your internet connection.'
      );
    }

    throw new ApiException(
      500,
      'UNKNOWN_ERROR',
      error instanceof Error ? error.message : 'An unexpected error occurred'
    );
  }
}

// Convenience methods
export const api = {
  get: <T>(endpoint: string, requireAuth = true): Promise<T> =>
    request<T>(endpoint, { method: 'GET', requireAuth }),

  post: <T>(endpoint: string, body: unknown, requireAuth = true): Promise<T> =>
    request<T>(endpoint, { method: 'POST', body, requireAuth }),

  put: <T>(endpoint: string, body: unknown, requireAuth = true): Promise<T> =>
    request<T>(endpoint, { method: 'PUT', body, requireAuth }),

  patch: <T>(endpoint: string, body: unknown, requireAuth = true): Promise<T> =>
    request<T>(endpoint, { method: 'PATCH', body, requireAuth }),

  delete: <T>(endpoint: string, requireAuth = true): Promise<T> =>
    request<T>(endpoint, { method: 'DELETE', requireAuth }),
};

// Chained API client (options-based) used by feature modules
export const apiClient = {
  get: <T>(endpoint: string, options: { params?: Record<string, unknown> } = {}): Promise<T> =>
    request<T>(endpoint, { method: 'GET', requireAuth: true, params: options.params }),

  post: <T>(endpoint: string, body?: unknown): Promise<T> =>
    request<T>(endpoint, { method: 'POST', body, requireAuth: true }),

  put: <T>(endpoint: string, body?: unknown): Promise<T> =>
    request<T>(endpoint, { method: 'PUT', body, requireAuth: true }),

  patch: <T>(endpoint: string, body?: unknown): Promise<T> =>
    request<T>(endpoint, { method: 'PATCH', body, requireAuth: true }),

  delete: <T>(endpoint: string): Promise<T> =>
    request<T>(endpoint, { method: 'DELETE', requireAuth: true }),
};

// Auth token utilities
export { getToken, setToken, removeToken };

// Base URL export for external use
export { API_BASE_URL };
