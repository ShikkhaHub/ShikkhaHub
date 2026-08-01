import { apiClient } from './client';

export type NotificationChannel = 'email' | 'push' | 'sms' | 'in_app';
export type NotificationType =
  | 'system'
  | 'search_alert'
  | 'review_response'
  | 'rating_update'
  | 'news'
  | 'ambassador_reward'
  | 'event';

export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  data?: Record<string, any>;
  read: boolean;
  archived: boolean;
  channel: NotificationChannel;
  created_at: string;
}

export interface NotificationPreference {
  user_id: string;
  email_enabled: boolean;
  push_enabled: boolean;
  sms_enabled: boolean;
  email_frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  categories: Record<NotificationType, boolean>;
}

export interface NotificationSummary {
  unread_count: number;
  archived_count: number;
  total_count: number;
}

export const notificationsAPI = {
  // Get all notifications
  getAll: async (
    limit = 20,
    offset = 0,
    filter?: 'unread' | 'archived'
  ): Promise<{ data: Notification[]; total: number }> => {
    const response = await apiClient.get('/api/v1/notifications', {
      params: { limit, offset, filter },
    });
    return response.data;
  },

  // Get notification by ID
  getById: async (id: string): Promise<Notification> => {
    const response = await apiClient.get(`/api/v1/notifications/${id}`);
    return response.data;
  },

  // Mark notification as read
  markAsRead: async (id: string): Promise<Notification> => {
    const response = await apiClient.patch(`/api/v1/notifications/${id}/read`);
    return response.data;
  },

  // Mark all notifications as read
  markAllAsRead: async (): Promise<void> => {
    await apiClient.post('/api/v1/notifications/read-all');
  },

  // Archive notification
  archive: async (id: string): Promise<Notification> => {
    const response = await apiClient.patch(`/api/v1/notifications/${id}/archive`);
    return response.data;
  },

  // Delete notification
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/notifications/${id}`);
  },

  // Get notification summary
  getSummary: async (): Promise<NotificationSummary> => {
    const response = await apiClient.get('/api/v1/notifications/summary/unread-count');
    return response.data;
  },

  // Get user preferences
  getPreferences: async (): Promise<NotificationPreference> => {
    const response = await apiClient.get('/api/v1/notifications/preferences');
    return response.data;
  },

  // Update preferences
  updatePreferences: async (preferences: Partial<NotificationPreference>): Promise<NotificationPreference> => {
    const response = await apiClient.patch('/api/v1/notifications/preferences', preferences);
    return response.data;
  },

  // Send test notification
  sendTest: async (channel: NotificationChannel): Promise<void> => {
    await apiClient.post('/api/v1/notifications/send-test', { channel });
  },
};

export default notificationsAPI;
