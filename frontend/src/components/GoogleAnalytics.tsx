import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

// Google Analytics Measurement ID
const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID || 'G-XXXXXXXXXX';

// Initialize Google Analytics
export const initGA = () => {
  if (typeof window === 'undefined') return;
  
  // Load GA script
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);
  
  // Initialize gtag
  window.dataLayer = window.dataLayer || [];
  function gtag(...args: any[]) {
    window.dataLayer.push(args);
  }
  gtag('js', new Date());
  gtag('config', GA_MEASUREMENT_ID, {
    page_title: document.title,
    page_location: window.location.href,
    send_page_view: true,
    cookie_flags: 'SameSite=None;Secure',
    cookie_domain: 'auto',
  });
};

// Track page views
export const pageView = (url: string, title?: string) => {
  if (typeof window === 'undefined' || !window.gtag) return;
  
  window.gtag('config', GA_MEASUREMENT_ID, {
    page_path: url,
    page_title: title || document.title,
    page_location: window.location.href,
  });
};

// Track custom events
export const trackEvent = (
  action: string,
  category: string,
  label?: string,
  value?: number,
  params?: Record<string, any>
) => {
  if (typeof window === 'undefined' || !window.gtag) return;
  
  window.gtag('event', action, {
    event_category: category,
    event_label: label,
    value: value,
    ...params,
  });
};

// Track search queries
export const trackSearch = (query: string, resultsCount: number) => {
  trackEvent('search', 'engagement', query, resultsCount, {
    search_term: query,
    results_count: resultsCount,
  });
};

// Track institution views
export const trackInstitutionView = (institutionName: string, institutionId: number) => {
  trackEvent('view_institution', 'engagement', institutionName, institutionId, {
    institution_name: institutionName,
    institution_id: institutionId,
  });
};

// Track comparisons
export const trackComparison = (institutionNames: string[]) => {
  trackEvent('compare_institutions', 'engagement', institutionNames.join(' vs '), institutionNames.length, {
    institutions: institutionNames,
    count: institutionNames.length,
  });
};

// Track review interactions
export const trackReviewAction = (action: 'view' | 'create' | 'helpful', institutionName: string) => {
  trackEvent(`${action}_review`, 'engagement', institutionName, undefined, {
    action,
    institution: institutionName,
  });
};

// Track Q&A interactions
export const trackQAAction = (action: 'ask' | 'answer' | 'vote', questionTitle?: string) => {
  trackEvent(`${action}_question`, 'engagement', questionTitle, undefined, {
    action,
    question: questionTitle,
  });
};

// Track AI chat usage
export const trackAIChat = (messageCount: number, sessionId?: string) => {
  trackEvent('ai_chat', 'engagement', 'AI Assistant', messageCount, {
    session_id: sessionId,
    message_count: messageCount,
  });
};

// Main component that tracks route changes
export function GoogleAnalytics() {
  const location = useLocation();
  
  useEffect(() => {
    // Initialize GA on first mount
    initGA();
  }, []);
  
  useEffect(() => {
    // Track page view on route change
    const timeoutId = setTimeout(() => {
      pageView(location.pathname + location.search);
    }, 100); // Small delay to ensure title is updated
    
    return () => clearTimeout(timeoutId);
  }, [location]);
  
  return null;
}

// Type declaration for window.gtag
declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
  }
}

export default GoogleAnalytics;
