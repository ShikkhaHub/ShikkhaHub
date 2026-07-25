// Authentication API endpoints
import { api, setToken, removeToken } from './client';
import type { User, AuthResponse, LoginCredentials, RegisterData } from '../types';

// ==================== AUTHENTICATION ====================

export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email);
  formData.append('password', credentials.password);

  const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const data: AuthResponse = await response.json();

  // Store token
  setToken(data.access_token);

  return data;
}

export async function register(data: RegisterData): Promise<User> {
  return api.post<User>('/auth/register', data, false);
}

export async function logout(): Promise<void> {
  removeToken();
  // Optionally notify backend
  try {
    await api.post('/auth/logout', {}, true);
  } catch {
    // Ignore errors on logout
  }
}

// ==================== CURRENT USER ====================

export async function getCurrentUser(): Promise<User> {
  return api.get<User>('/auth/me', true);
}

export async function refreshToken(): Promise<AuthResponse> {
  const refresh_token = localStorage.getItem('refresh_token');
  if (!refresh_token) {
    throw new Error('No refresh token available');
  }

  const response = await api.post<AuthResponse>('/auth/refresh', {
    refresh_token,
  }, false);

  setToken(response.access_token);
  localStorage.setItem('refresh_token', response.refresh_token);

  return response;
}

// ==================== PASSWORD MANAGEMENT ====================

export async function requestPasswordReset(email: string): Promise<void> {
  return api.post<void>('/auth/password-reset-request', { email }, false);
}

export async function resetPassword(
  token: string,
  newPassword: string
): Promise<void> {
  return api.post<void>('/auth/password-reset', {
    token,
    new_password: newPassword,
  }, false);
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<void> {
  return api.post<void>('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  }, true);
}

// ==================== PROFILE ====================

export async function updateProfile(
  data: Partial<User>
): Promise<User> {
  return api.patch<User>('/auth/profile', data, true);
}

export async function uploadAvatar(file: File): Promise<{ avatar_url: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const token = localStorage.getItem('access_token');

  const response = await fetch(
    `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/avatar`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error('Failed to upload avatar');
  }

  return response.json();
}
