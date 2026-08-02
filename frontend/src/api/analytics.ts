// Student Analytics API client for ShikkhaHub
import { api } from './client';
import type {
  Student360,
  StudentProfile,
  Recommendations,
  LearningAnalytics,
  StudentSegment,
  AIStudentProfile,
} from '../types';

export interface TrackEventPayload {
  event_type: string;
  session_id?: string;
  institution_id?: number;
  course_id?: number;
  subject?: string;
  page_path?: string;
  source?: string;
  event_data?: Record<string, unknown>;
  duration_seconds?: number;
}

export interface TrackStudyPayload {
  subject?: string;
  course_id?: number;
  duration_minutes: number;
  lessons_completed?: number;
  quiz_accuracy?: number;
  average_score?: number;
  content_type?: string;
}

export const studentAnalyticsApi = {
  // Profile
  getProfile: () =>
    api.get<{ profile: StudentProfile }>('/students/me/profile'),
  updateProfile: (data: Partial<StudentProfile>) =>
    api.post<{ success: boolean; profile: StudentProfile }>('/students/profile', data),

  // 360 dashboard
  getStudent360: () =>
    api.get<Student360>('/students/me'),

  // AI profile
  getAIProfile: (refresh = false) =>
    api.get<AIStudentProfile & StudentProfile>(
      `/students/me/ai-profile${refresh ? '?refresh=true' : ''}`
    ),

  // Learning analytics
  getLearning: (days = 30) =>
    api.get<LearningAnalytics>(`/students/me/learning?days=${days}`),

  // Segments
  getSegments: () =>
    api.get<{ segments: StudentSegment[] }>('/students/me/segments'),

  // Recommendations
  getRecommendations: () =>
    api.get<Recommendations>('/students/me/recommendations'),
  getInstitutionRecommendations: () =>
    api.get<Recommendations['institutions']>('/students/me/recommendations/institutions'),
  getCourseRecommendations: () =>
    api.get<Recommendations['courses']>('/students/me/recommendations/courses'),
  getScholarshipRecommendations: () =>
    api.get<Recommendations['scholarships']>('/students/me/recommendations/scholarships'),

  // Event tracking (no auth required; uses local session id)
  trackEvent: (payload: TrackEventPayload) =>
    api.post<{ success: boolean; event_id: number; is_anonymous: boolean }>(
      '/analytics/track/event',
      payload,
      false
    ),
  trackStudy: (payload: TrackStudyPayload) =>
    api.post<{ success: boolean; study_session_id: number }>('/analytics/track/study', payload),

  // Consent
  setConsent: (granted: boolean, consentType = 'analytics', version = '1.0') =>
    api.post<{ success: boolean; analytics_consent: boolean; history: unknown[] }>(
      '/students/consent',
      { granted, consent_type: consentType, consent_version: version }
    ),
  getConsentHistory: () =>
    api.get<{ history: unknown[] }>('/students/consent/history'),
};
