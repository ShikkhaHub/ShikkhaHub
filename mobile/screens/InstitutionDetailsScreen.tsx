import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Image,
  Linking,
  Alert,
  Share,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { apiService, Institution } from '../services/api';

export default function InstitutionDetailsScreen() {
  const navigation = useNavigation();
  const route = useRoute<any>();
  const { institutionId } = route.params;

  const [institution, setInstitution] = useState<Institution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState(false);
  const [reviews, setReviews] = useState<any[]>([]);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [rating, setRating] = useState(5);
  const [reviewText, setReviewText] = useState('');

  useEffect(() => {
    loadInstitutionDetails();
  }, [institutionId]);

  const loadInstitutionDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      const [instRes, reviewsRes] = await Promise.all([
        apiService.getInstitution(institutionId),
        apiService.getInstitutionReviews(institutionId),
      ]);

      setInstitution(instRes.data);
      setReviews(reviewsRes.data);
    } catch (err: any) {
      setError(apiService.handleError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await apiService.saveInstitution(institutionId);
      setIsSaved(true);
      Alert.alert('Success', 'Institution saved to your list');
    } catch (err: any) {
      Alert.alert('Error', apiService.handleError(err));
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `Check out ${institution?.name} on ShikkhaHub`,
        title: institution?.name,
      });
    } catch (error) {
      console.log('[v0] Share error:', error);
    }
  };

  const handleCall = () => {
    if (institution?.phone) {
      Linking.openURL(`tel:${institution.phone}`);
    }
  };

  const handleEmail = () => {
    if (institution?.email) {
      Linking.openURL(`mailto:${institution.email}`);
    }
  };

  const handleWebsite = () => {
    if (institution?.website) {
      Linking.openURL(institution.website);
    }
  };

  const submitReview = async () => {
    if (!reviewText.trim()) {
      Alert.alert('Error', 'Please enter a review');
      return;
    }

    try {
      await apiService.submitReview(institutionId, rating, reviewText);
      setReviewText('');
      setRating(5);
      setShowReviewForm(false);
      loadInstitutionDetails();
      Alert.alert('Success', 'Review submitted successfully');
    } catch (err: any) {
      Alert.alert('Error', apiService.handleError(err));
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  if (error || !institution) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>{error || 'Institution not found'}</Text>
        <TouchableOpacity
          style={styles.retryButton}
          onPress={() => {
            navigation.goBack();
          }}
        >
          <Text style={styles.retryButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header with image */}
      {institution.logo_url && (
        <Image source={{ uri: institution.logo_url }} style={styles.headerImage} />
      )}

      {/* Title and actions */}
      <View style={styles.titleSection}>
        <View style={styles.titleContent}>
          <Text style={styles.title}>{institution.name}</Text>
          <Text style={styles.type}>{institution.type}</Text>
        </View>
        <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
          <Text style={styles.actionIcon}>↗️</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, isSaved && styles.actionButtonActive]}
          onPress={handleSave}
        >
          <Text style={styles.actionIcon}>❤️</Text>
        </TouchableOpacity>
      </View>

      {/* Rating and reviews */}
      {institution.rating && (
        <View style={styles.ratingSection}>
          <Text style={styles.ratingValue}>⭐ {institution.rating.toFixed(1)}</Text>
          <Text style={styles.ratingText}>
            ({institution.review_count} reviews)
          </Text>
        </View>
      )}

      {/* Location and contact */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Location & Contact</Text>
        <Text style={styles.locationText}>
          📍 {institution.district}, {institution.division}
        </Text>
        {institution.phone && (
          <TouchableOpacity
            style={styles.contactItem}
            onPress={handleCall}
          >
            <Text style={styles.contactIcon}>📞</Text>
            <Text style={styles.contactText}>{institution.phone}</Text>
          </TouchableOpacity>
        )}
        {institution.email && (
          <TouchableOpacity
            style={styles.contactItem}
            onPress={handleEmail}
          >
            <Text style={styles.contactIcon}>📧</Text>
            <Text style={styles.contactText}>{institution.email}</Text>
          </TouchableOpacity>
        )}
        {institution.website && (
          <TouchableOpacity
            style={styles.contactItem}
            onPress={handleWebsite}
          >
            <Text style={styles.contactIcon}>🌐</Text>
            <Text style={styles.contactText}>{institution.website}</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* About */}
      {institution.description && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          <Text style={styles.description}>{institution.description}</Text>
        </View>
      )}

      {/* Quick info */}
      {institution.established_year && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Founded</Text>
          <Text style={styles.infoText}>{institution.established_year}</Text>
        </View>
      )}

      {/* Reviews section */}
      <View style={styles.section}>
        <View style={styles.reviewsHeader}>
          <Text style={styles.sectionTitle}>Reviews</Text>
          <TouchableOpacity
            style={styles.writeReviewButton}
            onPress={() => setShowReviewForm(!showReviewForm)}
          >
            <Text style={styles.writeReviewText}>✍️ Write</Text>
          </TouchableOpacity>
        </View>

        {showReviewForm && (
          <View style={styles.reviewForm}>
            <Text style={styles.formLabel}>Rating</Text>
            <View style={styles.ratingSelector}>
              {[1, 2, 3, 4, 5].map((r) => (
                <TouchableOpacity
                  key={r}
                  onPress={() => setRating(r)}
                  style={[
                    styles.starButton,
                    rating >= r && styles.starButtonActive,
                  ]}
                >
                  <Text style={styles.star}>⭐</Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.selectedRating}>{rating} stars</Text>

            <Text style={styles.formLabel}>Your Review</Text>
            <View style={styles.reviewInput}>
              {/* Note: Using a placeholder since TextInput is problematic in ScrollView */}
              <Text style={styles.reviewPlaceholder}>Write your review...</Text>
            </View>

            <View style={styles.reviewFormButtons}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowReviewForm(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.submitButton}
                onPress={submitReview}
              >
                <Text style={styles.submitButtonText}>Submit</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {reviews.length > 0 ? (
          reviews.map((review, index) => (
            <View key={index} style={styles.reviewCard}>
              <View style={styles.reviewHeader}>
                <Text style={styles.reviewerName}>{review.author_name}</Text>
                <Text style={styles.reviewRating}>⭐ {review.rating}</Text>
              </View>
              <Text style={styles.reviewContent}>{review.content}</Text>
              <Text style={styles.reviewDate}>
                {new Date(review.created_at).toLocaleDateString()}
              </Text>
            </View>
          ))
        ) : (
          <Text style={styles.noReviews}>No reviews yet. Be the first to review!</Text>
        )}
      </View>

      <View style={styles.spacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  headerImage: {
    width: '100%',
    height: 200,
  },
  titleSection: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    paddingBottom: 12,
  },
  titleContent: {
    flex: 1,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  type: {
    fontSize: 14,
    color: '#6b7280',
  },
  actionButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  actionButtonActive: {
    backgroundColor: '#fee2e2',
  },
  actionIcon: {
    fontSize: 20,
  },
  ratingSection: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  ratingValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#f59e0b',
    marginRight: 8,
  },
  ratingText: {
    fontSize: 14,
    color: '#6b7280',
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 12,
  },
  locationText: {
    fontSize: 14,
    color: '#374151',
    marginBottom: 8,
  },
  contactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  contactIcon: {
    fontSize: 18,
    marginRight: 12,
  },
  contactText: {
    fontSize: 14,
    color: '#2563eb',
    flex: 1,
  },
  description: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  infoText: {
    fontSize: 14,
    color: '#374151',
  },
  reviewsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  writeReviewButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
  },
  writeReviewText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  reviewForm: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  formLabel: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  ratingSelector: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  starButton: {
    marginRight: 8,
    opacity: 0.3,
  },
  starButtonActive: {
    opacity: 1,
  },
  star: {
    fontSize: 24,
  },
  selectedRating: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 12,
  },
  reviewInput: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 6,
    padding: 12,
    minHeight: 80,
    marginBottom: 12,
  },
  reviewPlaceholder: {
    color: '#d1d5db',
    fontSize: 14,
  },
  reviewFormButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#e5e7eb',
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
  },
  cancelButtonText: {
    color: '#374151',
    fontWeight: '600',
    fontSize: 12,
  },
  submitButton: {
    flex: 1,
    backgroundColor: '#2563eb',
    paddingVertical: 10,
    borderRadius: 6,
    alignItems: 'center',
  },
  submitButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 12,
  },
  reviewCard: {
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  reviewerName: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  reviewRating: {
    fontSize: 12,
    color: '#f59e0b',
  },
  reviewContent: {
    fontSize: 13,
    color: '#374151',
    lineHeight: 18,
    marginBottom: 8,
  },
  reviewDate: {
    fontSize: 11,
    color: '#9ca3af',
  },
  noReviews: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
    paddingVertical: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#dc2626',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  spacer: {
    height: 32,
  },
});
