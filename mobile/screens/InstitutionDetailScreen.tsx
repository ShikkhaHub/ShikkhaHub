import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Linking,
} from 'react-native';
import { apiService, Institution } from '../services/api';
import { useSavedStore } from '../hooks/useStore';

const InstitutionDetailScreen = ({ route }: any) => {
  const { institution: initialInstitution, id } = route.params;
  const [institution, setInstitution] = useState<Institution | null>(initialInstitution || null);
  const [isLoading, setIsLoading] = useState(!initialInstitution);
  const [reviews, setReviews] = useState<any[]>([]);
  const [newReview, setNewReview] = useState('');
  const [rating, setRating] = useState(5);
  const { isSaved, saveInstitution, removeSavedInstitution } = useSavedStore();

  useEffect(() => {
    if (!initialInstitution && id) {
      loadInstitution(id);
    }
    loadReviews();
  }, [id, initialInstitution]);

  const loadInstitution = async (institutionId: string) => {
    try {
      setIsLoading(true);
      const response = await apiService.getInstitution(institutionId);
      setInstitution(response.data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load institution details');
    } finally {
      setIsLoading(false);
    }
  };

  const loadReviews = async () => {
    try {
      const institutionId = initialInstitution?.id || id;
      if (institutionId) {
        const response = await apiService.getInstitutionReviews(institutionId);
        setReviews(response.data);
      }
    } catch (error) {
      console.error('Failed to load reviews:', error);
    }
  };

  const handleSaveToggle = async () => {
    if (!institution) return;
    try {
      if (isSaved(institution.id)) {
        await removeSavedInstitution(institution.id);
      } else {
        await saveInstitution(institution.id);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to update saved institutions');
    }
  };

  const handleSubmitReview = async () => {
    if (!institution || !newReview.trim()) {
      Alert.alert('Error', 'Please enter a review');
      return;
    }

    try {
      await apiService.submitReview(institution.id, rating, newReview);
      setNewReview('');
      setRating(5);
      await loadReviews();
      Alert.alert('Success', 'Review submitted successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to submit review');
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

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  if (!institution) {
    return (
      <View style={styles.centerContainer}>
        <Text>Institution not found</Text>
      </View>
    );
  }

  const saved = isSaved(institution.id);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.name}>{institution.name}</Text>
        <Text style={styles.type}>{institution.type}</Text>
        <Text style={styles.location}>
          {institution.district}, {institution.division}
        </Text>
      </View>

      <View style={styles.actionBar}>
        <TouchableOpacity style={styles.actionButton} onPress={handleSaveToggle}>
          <Text style={styles.actionIcon}>{saved ? '💾' : '🔖'}</Text>
          <Text style={styles.actionText}>{saved ? 'Saved' : 'Save'}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={handleCall}>
          <Text style={styles.actionIcon}>📞</Text>
          <Text style={styles.actionText}>Call</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={handleEmail}>
          <Text style={styles.actionIcon}>📧</Text>
          <Text style={styles.actionText}>Email</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton} onPress={handleWebsite}>
          <Text style={styles.actionIcon}>🌐</Text>
          <Text style={styles.actionText}>Website</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Information</Text>
        {institution.description && (
          <Text style={styles.description}>{institution.description}</Text>
        )}
        {institution.established_year && (
          <Text style={styles.info}>Established: {institution.established_year}</Text>
        )}
      </View>

      <View style={styles.section}>
        <View style={styles.ratingHeader}>
          <Text style={styles.sectionTitle}>Reviews</Text>
          <Text style={styles.rating}>
            ⭐ {institution.rating?.toFixed(1) || 'N/A'} ({institution.review_count || 0})
          </Text>
        </View>

        {reviews.map((review, index) => (
          <View key={index} style={styles.review}>
            <View style={styles.reviewHeader}>
              <Text style={styles.reviewAuthor}>{review.user_name}</Text>
              <Text style={styles.reviewRating}>⭐ {review.rating}</Text>
            </View>
            <Text style={styles.reviewText}>{review.review}</Text>
          </View>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Add Your Review</Text>
        <View style={styles.ratingSelector}>
          {[1, 2, 3, 4, 5].map((star) => (
            <TouchableOpacity
              key={star}
              onPress={() => setRating(star)}
              style={styles.starButton}
            >
              <Text style={star <= rating ? styles.starFilled : styles.starEmpty}>
                ⭐
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Your Review:</Text>
        <View style={styles.reviewInput}>
          {/* TextInput component would go here - simplified for stub */}
          <Text style={styles.placeholder}>Write your review...</Text>
        </View>

        <TouchableOpacity style={styles.submitButton} onPress={handleSubmitReview}>
          <Text style={styles.submitText}>Submit Review</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  type: {
    fontSize: 14,
    color: '#2563eb',
    fontWeight: '500',
    marginBottom: 4,
  },
  location: {
    fontSize: 14,
    color: '#666',
  },
  actionBar: {
    flexDirection: 'row',
    paddingHorizontal: 8,
    paddingVertical: 12,
    backgroundColor: '#fff',
    justifyContent: 'space-around',
  },
  actionButton: {
    alignItems: 'center',
    flex: 1,
  },
  actionIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  actionText: {
    fontSize: 12,
    color: '#374151',
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    marginVertical: 8,
    backgroundColor: '#fff',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  description: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
    marginBottom: 12,
  },
  info: {
    fontSize: 13,
    color: '#666',
    marginVertical: 6,
  },
  ratingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  rating: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#f59e0b',
  },
  review: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  reviewAuthor: {
    fontWeight: 'bold',
    color: '#1f2937',
  },
  reviewRating: {
    color: '#f59e0b',
  },
  reviewText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  ratingSelector: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  starButton: {
    marginRight: 8,
  },
  starFilled: {
    fontSize: 28,
  },
  starEmpty: {
    fontSize: 28,
    opacity: 0.3,
  },
  label: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  reviewInput: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    minHeight: 100,
    marginBottom: 12,
    backgroundColor: '#f9fafb',
  },
  placeholder: {
    color: '#999',
    fontSize: 14,
  },
  submitButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  submitText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
});

export default InstitutionDetailScreen;
