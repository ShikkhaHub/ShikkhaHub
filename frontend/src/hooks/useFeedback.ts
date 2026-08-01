import { useState, useCallback } from 'react';
import {
  Feedback,
  FeedbackComment,
  FeedbackCreate,
  FeedbackCommentCreate,
  FeedbackStatus,
  FeedbackType,
  feedbackAPI,
} from '../api/feedback';

export interface UseFeedbackState {
  feedback: Feedback[];
  selectedFeedback: Feedback | null;
  comments: FeedbackComment[];
  loading: boolean;
  error: string | null;
}

export const useFeedback = () => {
  const [state, setState] = useState<UseFeedbackState>({
    feedback: [],
    selectedFeedback: null,
    comments: [],
    loading: false,
    error: null,
  });

  // Fetch all feedback
  const fetchFeedback = useCallback(async (type?: FeedbackType, status?: FeedbackStatus) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const result = await feedbackAPI.getAll(type, status, 20, 0);
      setState((s) => ({ ...s, feedback: result.data, loading: false }));
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
    }
  }, []);

  // Create feedback
  const createFeedback = useCallback(async (data: FeedbackCreate) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const newFeedback = await feedbackAPI.create(data);
      setState((s) => ({
        ...s,
        feedback: [newFeedback, ...s.feedback],
        loading: false,
      }));
      return newFeedback;
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
      throw error;
    }
  }, []);

  // Select feedback
  const selectFeedback = useCallback(async (id: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const feedback = await feedbackAPI.getById(id);
      const commentsResult = await feedbackAPI.getComments(id);
      setState((s) => ({
        ...s,
        selectedFeedback: feedback,
        comments: commentsResult.data,
        loading: false,
      }));
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
    }
  }, []);

  // Add comment
  const addComment = useCallback(
    async (feedbackId: string, data: FeedbackCommentCreate) => {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const comment = await feedbackAPI.addComment(feedbackId, data);
        setState((s) => ({
          ...s,
          comments: [...s.comments, comment],
          loading: false,
        }));
        return comment;
      } catch (error) {
        setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
        throw error;
      }
    },
    []
  );

  // Upvote feedback
  const upvote = useCallback(async (id: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const updated = await feedbackAPI.upvote(id);
      setState((s) => ({
        ...s,
        feedback: s.feedback.map((f) => (f.id === id ? updated : f)),
        selectedFeedback: s.selectedFeedback?.id === id ? updated : s.selectedFeedback,
        loading: false,
      }));
      return updated;
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
      throw error;
    }
  }, []);

  // Update feedback status (admin)
  const updateStatus = useCallback(async (id: string, status: FeedbackStatus) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const updated = await feedbackAPI.updateStatus(id, status);
      setState((s) => ({
        ...s,
        feedback: s.feedback.map((f) => (f.id === id ? updated : f)),
        selectedFeedback: s.selectedFeedback?.id === id ? updated : s.selectedFeedback,
        loading: false,
      }));
      return updated;
    } catch (error) {
      setState((s) => ({ ...s, error: (error as Error).message, loading: false }));
      throw error;
    }
  }, []);

  // Clear selection
  const clearSelection = useCallback(() => {
    setState((s) => ({
      ...s,
      selectedFeedback: null,
      comments: [],
    }));
  }, []);

  return {
    ...state,
    fetchFeedback,
    createFeedback,
    selectFeedback,
    addComment,
    upvote,
    updateStatus,
    clearSelection,
  };
};
