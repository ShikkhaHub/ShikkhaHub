import { useState, useCallback, useEffect } from 'react';
import {
  Notification,
  NotificationPreference,
  NotificationSummary,
  notificationsAPI,
} from '../api/notifications';

export interface UseNotificationsState {
  notifications: Notification[];
  preferences: NotificationPreference | null;
  summary: NotificationSummary | null;
  loading: boolean;
  error: string | null;
}

export const useNotifications = () => {
  const [state, setState] = useState<UseNotificationsState>({
    notifications: [],
    preferences: null,
    summary: null,
    loading: false,
    error: null,
  });

  // Fetch notifications
  const fetchNotifications = useCallback(async (filter?: 'unread' | 'archived') => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const result = await notificationsAPI.getAll(20, 0, filter);
      setState((s) => ({ ...s, notifications: result.data, loading: false }));
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
    }
  }, []);

  // Fetch notification summary
  const fetchSummary = useCallback(async () => {
    try {
      const summary = await notificationsAPI.getSummary();
      setState((s) => ({ ...s, summary }));
    } catch (error) {
      console.error('[v0] Error fetching summary:', error);
    }
  }, []);

  // Fetch preferences
  const fetchPreferences = useCallback(async () => {
    try {
      const preferences = await notificationsAPI.getPreferences();
      setState((s) => ({ ...s, preferences }));
    } catch (error) {
      console.error('[v0] Error fetching preferences:', error);
    }
  }, []);

  // Mark as read
  const markAsRead = useCallback(async (id: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      await notificationsAPI.markAsRead(id);
      setState((s) => ({
        ...s,
        notifications: s.notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n
        ),
        loading: false,
      }));
      await fetchSummary();
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
    }
  }, [fetchSummary]);

  // Mark all as read
  const markAllAsRead = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      await notificationsAPI.markAllAsRead();
      setState((s) => ({
        ...s,
        notifications: s.notifications.map((n) => ({ ...n, read: true })),
        loading: false,
      }));
      await fetchSummary();
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
    }
  }, [fetchSummary]);

  // Archive notification
  const archive = useCallback(async (id: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      await notificationsAPI.archive(id);
      setState((s) => ({
        ...s,
        notifications: s.notifications.filter((n) => n.id !== id),
        loading: false,
      }));
      await fetchSummary();
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
    }
  }, [fetchSummary]);

  // Delete notification
  const deleteNotification = useCallback(async (id: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      await notificationsAPI.delete(id);
      setState((s) => ({
        ...s,
        notifications: s.notifications.filter((n) => n.id !== id),
        loading: false,
      }));
      await fetchSummary();
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
    }
  }, [fetchSummary]);

  // Update preferences
  const updatePreferences = useCallback(async (prefs: Partial<NotificationPreference>) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const updated = await notificationsAPI.updatePreferences(prefs);
      setState((s) => ({ ...s, preferences: updated, loading: false }));
      return updated;
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
      throw error;
    }
  }, []);

  // Initialize on mount
  useEffect(() => {
    fetchNotifications();
    fetchSummary();
    fetchPreferences();
  }, [fetchNotifications, fetchSummary, fetchPreferences]);

  return {
    ...state,
    fetchNotifications,
    fetchSummary,
    fetchPreferences,
    markAsRead,
    markAllAsRead,
    archive,
    deleteNotification,
    updatePreferences,
  };
};
