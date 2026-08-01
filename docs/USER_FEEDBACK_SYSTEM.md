# User Feedback System

## Overview

Comprehensive system for collecting, managing, and analyzing user feedback, bug reports, and feature requests.

## Components

1. **Feedback Collection**: In-app feedback forms
2. **Feedback Management**: Internal dashboard for team
3. **User Engagement**: Public voting and comments
4. **Analytics**: Aggregated insights and trends
5. **Notifications**: Team alerts on new feedback

---

## 1. Feedback Types

### Bug Report
- For reporting application issues
- Auto-prioritized based on impact
- Tracked to resolution
- Example: "Search not showing results"

### Feature Request
- For suggesting new features
- Community voting
- Tracks interest level
- Example: "Add institution favorites"

### Improvement
- For UX/performance improvements
- Tied to specific sections
- Example: "Make search filters easier to use"

### General
- For other feedback
- Lowest priority by default
- Example: "Great app, keep it up!"

### Complaint
- For negative experiences
- Flagged for quick response
- Example: "App crashed on search"

---

## 2. Frontend Integration

### Feedback Modal Component

```typescript
// components/FeedbackModal.tsx
import { useState } from "react";
import { Button, Modal, Textarea, Select, Rating } from "@/ui";

export function FeedbackModal({ isOpen, onClose }) {
  const [type, setType] = useState("general");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [rating, setRating] = useState(null);

  const handleSubmit = async () => {
    await apiService.submitFeedback({
      type,
      title,
      description,
      rating,
      page_url: window.location.href,
      user_agent: navigator.userAgent,
      metadata: {
        app_version: APP_VERSION,
        timestamp: new Date().toISOString(),
      },
    });

    // Show success message
    showToast("Thank you for your feedback!");
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="space-y-4 p-6">
        <h2 className="text-2xl font-bold">Send Feedback</h2>

        <Select
          label="Feedback Type"
          value={type}
          onChange={(e) => setType(e.target.value)}
          options={[
            { value: "bug_report", label: "Bug Report" },
            { value: "feature_request", label: "Feature Request" },
            { value: "improvement", label: "Improvement" },
            { value: "complaint", label: "Complaint" },
            { value: "general", label: "General" },
          ]}
        />

        <input
          type="text"
          placeholder="Brief title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full border rounded p-2"
        />

        <Textarea
          placeholder="Describe your feedback in detail"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={5}
        />

        <Rating
          label="Rate your experience"
          value={rating}
          onChange={setRating}
        />

        <div className="flex justify-end space-x-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Submit Feedback</Button>
        </div>
      </div>
    </Modal>
  );
}
```

### Feedback Button

```typescript
// components/FeedbackButton.tsx
import { useState } from "react";
import { FeedbackModal } from "./FeedbackModal";

export function FeedbackButton() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 bg-blue-500 text-white rounded-full p-3 shadow-lg hover:bg-blue-600"
        title="Send Feedback"
      >
        💬
      </button>
      <FeedbackModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}
```

---

## 3. Mobile Integration (React Native)

```typescript
// screens/FeedbackScreen.tsx
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Picker,
} from "react-native";
import { Rating } from "react-native-ratings";
import { apiService } from "@services/api";

const FeedbackScreen = ({ navigation }) => {
  const [type, setType] = useState("general");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [rating, setRating] = useState(5);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!title.trim() || !description.trim()) {
      alert("Please fill in all fields");
      return;
    }

    try {
      setLoading(true);
      await apiService.submitFeedback({
        type,
        title,
        description,
        rating: rating ? `${Math.round(rating)}` : null,
        user_agent: "Mobile-App",
      });

      alert("Thank you for your feedback!");
      navigation.goBack();
    } catch (error) {
      alert("Failed to submit feedback");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Send Us Your Feedback</Text>

      <View style={styles.section}>
        <Text style={styles.label}>Feedback Type</Text>
        <Picker
          selectedValue={type}
          onValueChange={setType}
          style={styles.picker}
        >
          <Picker.Item label="General" value="general" />
          <Picker.Item label="Bug Report" value="bug_report" />
          <Picker.Item label="Feature Request" value="feature_request" />
          <Picker.Item label="Improvement" value="improvement" />
          <Picker.Item label="Complaint" value="complaint" />
        </Picker>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Title</Text>
        <TextInput
          style={styles.input}
          placeholder="Brief title"
          value={title}
          onChangeText={setTitle}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Description</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Tell us more about your feedback"
          multiline
          numberOfLines={5}
          value={description}
          onChangeText={setDescription}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Rate Your Experience</Text>
        <Rating
          ratingCount={5}
          imageSize={30}
          onFinishRating={setRating}
          style={styles.rating}
        />
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleSubmit}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? "Submitting..." : "Submit Feedback"}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: "#f9fafb",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
  },
  section: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  textArea: {
    minHeight: 120,
    textAlignVertical: "top",
  },
  picker: {
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
  },
  rating: {
    marginVertical: 10,
  },
  button: {
    backgroundColor: "#2563eb",
    padding: 14,
    borderRadius: 8,
    alignItems: "center",
    marginBottom: 20,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "bold",
  },
});

export default FeedbackScreen;
```

---

## 4. Admin Dashboard

### Feedback Management

```
Dashboard Features:
- List of all feedback items
- Filter by type, status, priority
- Search functionality
- Sorting by date, upvotes, priority
- Bulk actions (mark as duplicate, resolve, etc.)
- Response time metrics
- Sentiment analysis
```

### Status Workflow

```
NEW → ACKNOWLEDGED → IN_PROGRESS → COMPLETED
  ↓                                    ↓
  └────→ WONT_FIX ───────────────────┘
              ↓
           CLOSED

DUPLICATE → CLOSED
```

### Key Metrics

```
- Average response time to feedback
- Resolution rate (% resolved within 7 days)
- Sentiment ratio (positive/neutral/negative)
- Most requested features
- Most reported bugs
- Community engagement (comments, upvotes)
```

---

## 5. API Endpoints

### POST /api/v1/feedback
Create new feedback

```json
{
  "type": "feature_request",
  "title": "Add saved searches",
  "description": "Would be useful to save search criteria",
  "rating": "good",
  "section": "search",
  "page_url": "https://shikkhahub.edu.bd/search",
  "is_public": true
}
```

### GET /api/v1/feedback
List feedback (paginated)

```
?skip=0&limit=20&type=feature_request&status=new
```

### POST /api/v1/feedback/{id}/comments
Add comment to feedback

```json
{
  "comment": "Great suggestion, we're looking into this",
  "is_internal": false
}
```

### POST /api/v1/feedback/{id}/upvote
Upvote feedback

```
Status: 200
Response: { "upvote_count": 42 }
```

### PATCH /api/v1/feedback/{id}/status
Update feedback status (admin only)

```json
{
  "new_status": "in_progress"
}
```

### GET /api/v1/feedback/analytics/summary
Get analytics (admin only)

```
?days=7
```

---

## 6. Notification System

### Team Alerts

Team is notified when:
1. **New Bug Report** - Critical if "crash" or "broken"
2. **New Feature Request** - Weekly digest
3. **High Upvotes** - If feedback gets 50+ upvotes
4. **Urgent Complaint** - Immediate notification

### User Notifications

Users are notified when:
1. **Status Change** - Email when feedback status changes
2. **Comment Reply** - Notify when team/community replies
3. **Implemented** - When requested feature is released

---

## 7. Analytics & Insights

### Dashboard Metrics

```
Daily Metrics:
- New feedback count by type
- Sentiment distribution
- Average rating
- Response rate
- Resolution rate
- Top issues

Weekly Insights:
- Trending topics
- Feature request popularity
- Bug patterns
- User sentiment trend

Monthly Reports:
- Feedback trends
- Team performance
- Product roadmap alignment
- User satisfaction trends
```

### Sentiment Analysis

```
Rating Distribution:
- Very Poor: 😞
- Poor: 😟
- Neutral: 😐
- Good: 😊
- Excellent: 😄

Actions:
- Negative feedback: Flag for quick response
- Positive feedback: Share with team for morale
- Feature requests: Add to product backlog
```

---

## 8. Best Practices

### For Users
- Be specific and descriptive
- Include steps to reproduce (for bugs)
- Share screenshots/attachments
- Be constructive and respectful
- Vote on feedback you agree with

### For Team
- Acknowledge within 24 hours
- Provide updates on progress
- Ask clarifying questions
- Link related feedback
- Share implemented features
- Close when resolved

### For Product
- Track all feedback sources
- Prioritize by votes and impact
- Release notes for implemented feedback
- Public roadmap showing planned work
- Quarterly feature rollout based on feedback

---

## 9. Integration Checklist

- [ ] Add FeedbackButton to main app
- [ ] Create Feedback screen/modal
- [ ] Implement feedback API client
- [ ] Add feedback to admin dashboard
- [ ] Set up email notifications
- [ ] Configure feedback templates
- [ ] Create onboarding guide for team
- [ ] Document feedback workflow
- [ ] Set up analytics dashboard
- [ ] Train support team

---

## 10. Success Metrics

**Month 1**:
- 100+ feedback items collected
- <24 hour response time
- 50% community participation (comments/votes)

**Month 3**:
- 500+ feedback items
- 3+ features implemented from feedback
- 80% positive sentiment

**Month 6**:
- 1,500+ feedback items
- 10+ features implemented
- Public roadmap published
- Strong community engagement

---

**Last Updated**: 2024
**Owner**: Product Team
**Review Frequency**: Weekly
