import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiService, UserProfile } from '../services/api';

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  loading: boolean;
  error: string | null;

  // Actions
  initializeAuth: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: Partial<UserProfile>) => Promise<void>;
  clearError: () => void;
}

const TOKEN_KEY = '@shikkhahub_token';
const USER_KEY = '@shikkhahub_user';

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isInitialized: false,
  loading: false,
  error: null,

  initializeAuth: async () => {
    try {
      set({ loading: true });
      
      // Try to restore token and user from AsyncStorage
      const token = await AsyncStorage.getItem(TOKEN_KEY);
      const userStr = await AsyncStorage.getItem(USER_KEY);

      if (token) {
        apiService.setToken(token);
        
        try {
          // Verify token is still valid by fetching profile
          const response = await apiService.getProfile();
          set({
            token,
            user: response.data,
            isAuthenticated: true,
            isInitialized: true,
            loading: false,
            error: null,
          });
        } catch (error) {
          // Token is invalid, clear it
          await AsyncStorage.removeItem(TOKEN_KEY);
          await AsyncStorage.removeItem(USER_KEY);
          apiService.setToken(null);
          set({
            token: null,
            user: null,
            isAuthenticated: false,
            isInitialized: true,
            loading: false,
            error: null,
          });
        }
      } else {
        set({
          isInitialized: true,
          loading: false,
        });
      }
    } catch (error) {
      set({
        isInitialized: true,
        loading: false,
        error: 'Failed to initialize authentication',
      });
    }
  },

  login: async (email: string, password: string) => {
    try {
      set({ loading: true, error: null });

      const response = await apiService.login(email, password);
      
      // Store token and user
      await AsyncStorage.setItem(TOKEN_KEY, response.token);
      await AsyncStorage.setItem(USER_KEY, JSON.stringify(response.user));
      
      apiService.setToken(response.token);

      set({
        token: response.token,
        user: response.user,
        isAuthenticated: true,
        loading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = apiService.handleError(error);
      set({
        loading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  register: async (email: string, password: string, name: string) => {
    try {
      set({ loading: true, error: null });

      const response = await apiService.register(email, password, name);
      
      // Store token and user
      await AsyncStorage.setItem(TOKEN_KEY, response.token);
      await AsyncStorage.setItem(USER_KEY, JSON.stringify(response.user));
      
      apiService.setToken(response.token);

      set({
        token: response.token,
        user: response.user,
        isAuthenticated: true,
        loading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = apiService.handleError(error);
      set({
        loading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  logout: async () => {
    try {
      set({ loading: true, error: null });

      await apiService.logout();
      
      // Clear stored credentials
      await AsyncStorage.removeItem(TOKEN_KEY);
      await AsyncStorage.removeItem(USER_KEY);
      
      apiService.setToken(null);

      set({
        token: null,
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = apiService.handleError(error);
      set({
        loading: false,
        error: errorMessage,
      });
    }
  },

  updateProfile: async (data: Partial<UserProfile>) => {
    try {
      set({ loading: true, error: null });

      const response = await apiService.updateProfile(data);
      
      // Update stored user
      await AsyncStorage.setItem(USER_KEY, JSON.stringify(response.data));

      set({
        user: response.data,
        loading: false,
        error: null,
      });
    } catch (error: any) {
      const errorMessage = apiService.handleError(error);
      set({
        loading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));
