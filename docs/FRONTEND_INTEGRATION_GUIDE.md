# Frontend Integration Guide

## Overview

This guide explains how to integrate the new frontend components, hooks, and APIs into the main ShikkhaHub React application.

## Components Added

### 1. SavedSearchesPanel
Location: `frontend/src/components/SavedSearchesPanel.tsx`

**Purpose:** Manage saved institution searches with notification preferences

**Integration:**
```tsx
import { SavedSearchesPanel } from './components/SavedSearchesPanel';

// Add to your search/dashboard page:
<SavedSearchesPanel />
```

**Features:**
- Create new searches with custom name and query
- Toggle notifications for each search
- Display match count
- Delete searches
- Visual feedback for active/selected searches

**Usage Example:**
```tsx
function SearchPage() {
  return (
    <div className="search-container">
      <SearchBar />
      <div className="search-layout">
        <aside>
          <SavedSearchesPanel />
        </aside>
        <main>
          {/* Search results here */}
        </main>
      </div>
    </div>
  );
}
```

### 2. NotificationsDropdown
Location: `frontend/src/components/NotificationsDropdown.tsx`

**Purpose:** Display and manage user notifications

**Integration:**
```tsx
import { NotificationsDropdown } from './components/NotificationsDropdown';

// Add to your header/navbar:
<header>
  <nav>
    {/* Other nav items */}
    <NotificationsDropdown />
  </nav>
</header>
```

**Features:**
- Badge showing unread notification count
- Dropdown menu with recent notifications
- Mark individual notifications as read
- Mark all as read
- Delete notifications
- Link to full notifications page

**Styling:** Uses CSS-in-JS with responsive design

### 3. FeedbackModal
Location: `frontend/src/components/FeedbackModal.tsx`

**Purpose:** Collect user feedback

**Integration:**
```tsx
import { FeedbackModal } from './components/FeedbackModal';
import { useState } from 'react';

function Page() {
  const [showFeedback, setShowFeedback] = useState(false);

  return (
    <>
      <button onClick={() => setShowFeedback(true)}>
        Send Feedback
      </button>
      <FeedbackModal
        isOpen={showFeedback}
        onClose={() => setShowFeedback(false)}
        initialType="feature_request"
      />
    </>
  );
}
```

**Features:**
- Multiple feedback types (bug, feature, improvement, etc)
- Rating system for severity
- Character count validation
- Success confirmation
- Error handling

## Custom Hooks

### useSavedSearches
```tsx
import { useSavedSearches } from './hooks/useSavedSearches';

function MyComponent() {
  const {
    searches,
    selectedSearch,
    loading,
    error,
    fetchSearches,
    createSearch,
    updateSearch,
    deleteSearch,
    toggleNotifications,
    selectSearch,
  } = useSavedSearches();

  // Use in your component
}
```

**Methods:**
- `fetchSearches()`: Load all saved searches
- `createSearch(data)`: Create new search
- `updateSearch(id, data)`: Update existing search
- `deleteSearch(id)`: Delete search
- `toggleNotifications(id, enabled)`: Enable/disable alerts
- `selectSearch(search)`: Set active search

### useNotifications
```tsx
import { useNotifications } from './hooks/useNotifications';

function MyComponent() {
  const {
    notifications,
    preferences,
    summary,
    loading,
    error,
    fetchNotifications,
    fetchPreferences,
    markAsRead,
    markAllAsRead,
    archive,
    deleteNotification,
    updatePreferences,
  } = useNotifications();

  // Auto-initializes on mount
}
```

**Methods:**
- `fetchNotifications(filter)`: Load notifications
- `fetchPreferences()`: Load user preferences
- `markAsRead(id)`: Mark single notification as read
- `markAllAsRead()`: Mark all as read
- `archive(id)`: Archive notification
- `deleteNotification(id)`: Delete notification
- `updatePreferences(prefs)`: Update notification settings

### useFeedback
```tsx
import { useFeedback } from './hooks/useFeedback';

function MyComponent() {
  const {
    feedback,
    selectedFeedback,
    comments,
    loading,
    error,
    fetchFeedback,
    createFeedback,
    selectFeedback,
    addComment,
    upvote,
    updateStatus,
  } = useFeedback();
}
```

**Methods:**
- `fetchFeedback(type, status)`: Load feedback items
- `createFeedback(data)`: Submit new feedback
- `selectFeedback(id)`: Load feedback and comments
- `addComment(feedbackId, data)`: Add comment
- `upvote(id)`: Upvote feedback
- `updateStatus(id, status)`: Change feedback status (admin)

## API Clients

### savedSearchesAPI
```tsx
import { savedSearchesAPI } from './api/saved-searches';

// Create search
const search = await savedSearchesAPI.create({
  name: 'Universities in Dhaka',
  query: 'university',
  filters: { division: 'Dhaka' },
  notify: true,
  notify_frequency: 'daily',
});

// Get all
const { data, total } = await savedSearchesAPI.getAll();

// Update
const updated = await savedSearchesAPI.update(id, { name: 'New name' });

// Toggle notifications
await savedSearchesAPI.toggleNotifications(id, true);

// Get results
const { data: results } = await savedSearchesAPI.getResults(id);
```

### notificationsAPI
```tsx
import { notificationsAPI } from './api/notifications';

// Get notifications
const { data, total } = await notificationsAPI.getAll(20, 0);

// Mark as read
await notificationsAPI.markAsRead(notificationId);

// Get preferences
const prefs = await notificationsAPI.getPreferences();

// Update preferences
await notificationsAPI.updatePreferences({
  email_enabled: true,
  email_frequency: 'daily',
});

// Get summary
const summary = await notificationsAPI.getSummary();
```

### feedbackAPI
```tsx
import { feedbackAPI } from './api/feedback';

// Submit feedback
const feedback = await feedbackAPI.create({
  type: 'feature_request',
  title: 'Add dark mode',
  description: 'Please add a dark mode for the interface',
  rating: 'good',
  public: true,
});

// Get feedback
const { data, total } = await feedbackAPI.getAll('feature_request', 'new');

// Add comment
const comment = await feedbackAPI.addComment(feedbackId, {
  text: 'Great idea!',
  internal: false,
});

// Upvote
await feedbackAPI.upvote(feedbackId);
```

## Layout Integration

### Sidebar with Saved Searches
```tsx
<div style={{ display: 'grid', gridTemplateColumns: '300px 1fr' }}>
  <aside className="sidebar">
    <SavedSearchesPanel />
  </aside>
  <main>
    {/* Main content */}
  </main>
</div>
```

### Header with Notifications
```tsx
<header style={{ display: 'flex', justifyContent: 'space-between' }}>
  <h1>ShikkhaHub</h1>
  <div style={{ display: 'flex', gap: '12px' }}>
    <NotificationsDropdown />
    <ProfileMenu />
  </div>
</header>
```

### Feedback Button with Modal
```tsx
function App() {
  const [showFeedback, setShowFeedback] = useState(false);

  return (
    <>
      <main>{/* App content */}</main>
      <button
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
        }}
        onClick={() => setShowFeedback(true)}
      >
        💬 Feedback
      </button>
      <FeedbackModal
        isOpen={showFeedback}
        onClose={() => setShowFeedback(false)}
      />
    </>
  );
}
```

## Styling

All components use CSS-in-JS with `<style jsx>` blocks. They're self-contained and don't require external CSS files.

**Color Scheme:**
- Primary: `#2563eb` (Blue)
- Danger: `#dc2626` (Red)
- Success: `#059669` (Green)
- Warning: `#f59e0b` (Amber)
- Backgrounds: `#f9fafb`, `#ffffff`
- Borders: `#e5e7eb`

**Responsive Design:**
- Mobile-first approach
- Works on all screen sizes
- No external breakpoints needed

## Type Safety

All components and hooks are fully typed with TypeScript:

```tsx
import {
  SavedSearch,
  SavedSearchCreate,
  Notification,
  Feedback,
  FeedbackType,
} from './api/';
```

## Error Handling

Components include built-in error handling:

```tsx
// Display error messages
{error && <div className="error-message">{error}</div>}

// Handle errors in hooks
try {
  await createSearch(data);
} catch (error) {
  console.error('Creation failed:', error);
}
```

## Loading States

All components show loading indicators:

```tsx
{loading && <div className="loading">Loading...</div>}
```

## Data Persistence

Data is managed through API calls. Zustand hooks maintain local state and sync with backend:

```tsx
// State is automatically synchronized
// when user navigates between pages
const { fetchSearches } = useSavedSearches();
useEffect(() => {
  fetchSearches(); // Refresh from API
}, []);
```

## Integration Checklist

- [ ] Copy API client files to `frontend/src/api/`
- [ ] Copy hook files to `frontend/src/hooks/`
- [ ] Copy component files to `frontend/src/components/`
- [ ] Add components to relevant pages
- [ ] Test API connectivity
- [ ] Verify token/auth handling
- [ ] Test error scenarios
- [ ] Verify responsive design
- [ ] Test accessibility
- [ ] Performance testing

## Next Steps

1. Add components to pages incrementally
2. Test with real API endpoints
3. Add analytics tracking
4. Create dedicated pages for:
   - `/notifications` - Full notifications page
   - `/settings/notifications` - Notification preferences
   - `/feedback` - Feedback list (admin)
5. Implement real-time updates (WebSocket)
6. Add keyboard shortcuts (e.g., `Cmd+K` for saved searches)

## Support

For issues or questions, refer to:
- Backend API documentation: `/docs/API.md`
- Individual component comments in source files
- Hook implementation for state management patterns
