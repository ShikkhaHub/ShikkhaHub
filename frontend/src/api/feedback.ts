import { apiClient } from './client';

export type FeedbackType = 'bug_report' | 'feature_request' | 'improvement' | 'general' | 'complaint';
export type FeedbackStatus = 'new' | 'acknowledged' | 'in_progress' | 'completed' | 'wont_fix';
export type FeedbackPriority = 'low' | 'medium' | 'high' | 'critical';
export type FeedbackRating = 'very_poor' | 'poor' | 'average' | 'good' | 'excellent';

export interface Feedback {
  id: string;
  user_id: string;
  type: FeedbackType;
  title: string;
  description: string;
  rating?: FeedbackRating;
  status: FeedbackStatus;
  priority?: FeedbackPriority;
  public: boolean;
  metadata?: Record<string, any>;
  upvote_count: number;
  comment_count: number;
  user_upvoted?: boolean;
  created_at: string;
  updated_at: string;
}

export interface FeedbackComment {
  id: string;
  feedback_id: string;
  user_id: string;
  text: string;
  internal: boolean;
  created_at: string;
  updated_at: string;
}

export interface FeedbackCreate {
  type: FeedbackType;
  title: string;
  description: string;
  rating?: FeedbackRating;
  public?: boolean;
  metadata?: Record<string, any>;
}

export interface FeedbackCommentCreate {
  text: string;
  internal?: boolean;
}

export const feedbackAPI = {
  // Create feedback
  create: async (data: FeedbackCreate): Promise<Feedback> => {
    const response = await apiClient.post<Feedback>('/api/v1/feedback', data);
    return response;
  },

  // Get all feedback with filters
  getAll: async (
    type?: FeedbackType,
    status?: FeedbackStatus,
    limit = 20,
    offset = 0
  ): Promise<{ data: Feedback[]; total: number }> => {
    const response = await apiClient.get<{ data: Feedback[]; total: number }>('/api/v1/feedback', {
      params: { type, status, limit, offset },
    });
    return response;
  },

  // Get specific feedback
  getById: async (id: string): Promise<Feedback> => {
    const response = await apiClient.get<Feedback>(`/api/v1/feedback/${id}`);
    return response;
  },

  // Add comment to feedback
  addComment: async (feedbackId: string, data: FeedbackCommentCreate): Promise<FeedbackComment> => {
    const response = await apiClient.post<FeedbackComment>(`/api/v1/feedback/${feedbackId}/comments`, data);
    return response;
  },

  // Get comments for feedback
  getComments: async (
    feedbackId: string,
    limit = 20,
    offset = 0
  ): Promise<{ data: FeedbackComment[]; total: number }> => {
    const response = await apiClient.get<{ data: FeedbackComment[]; total: number }>(
      `/api/v1/feedback/${feedbackId}/comments`,
      { params: { limit, offset } }
    );
    return response;
  },

  // Upvote feedback
  upvote: async (id: string): Promise<Feedback> => {
    const response = await apiClient.post<Feedback>(`/api/v1/feedback/${id}/upvote`);
    return response;
  },

  // Change feedback status (admin)
  updateStatus: async (id: string, status: FeedbackStatus): Promise<Feedback> => {
    const response = await apiClient.patch<Feedback>(`/api/v1/feedback/${id}/status`, { status });
    return response;
  },

  // Get analytics summary
  getAnalytics: async (): Promise<{
    total_feedback: number;
    by_type: Record<FeedbackType, number>;
    by_status: Record<FeedbackStatus, number>;
    avg_rating: number;
  }> => {
    const response = await apiClient.get<{
      total_feedback: number;
      by_type: Record<FeedbackType, number>;
      by_status: Record<FeedbackStatus, number>;
      avg_rating: number;
    }>('/api/v1/analytics/summary');
    return response;
  },

  // Get feedback templates
  getTemplates: async (): Promise<any[]> => {
    const response = await apiClient.get<any[]>('/api/v1/templates/all');
    return response;
  },
};

export default feedbackAPI;
