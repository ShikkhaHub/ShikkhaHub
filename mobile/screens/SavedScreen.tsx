import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Image,
  Alert,
} from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { apiService, Institution } from '../services/api';

export default function SavedScreen() {
  const navigation = useNavigation();
  const [savedInstitutions, setSavedInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    React.useCallback(() => {
      loadSavedInstitutions();
    }, [])
  );

  const loadSavedInstitutions = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getSavedInstitutions();
      setSavedInstitutions(response.data);
    } catch (err: any) {
      setError(apiService.handleError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (institutionId: string) => {
    Alert.alert(
      'Remove Saved Institution',
      'Are you sure you want to remove this from your saved list?',
      [
        { text: 'Cancel', onPress: () => {}, style: 'cancel' },
        {
          text: 'Remove',
          onPress: async () => {
            try {
              await apiService.removeSavedInstitution(institutionId);
              setSavedInstitutions(
                savedInstitutions.filter((inst) => inst.id !== institutionId)
              );
            } catch (err: any) {
              Alert.alert('Error', apiService.handleError(err));
            }
          },
          style: 'destructive',
        },
      ]
    );
  };

  const handleInstitutionPress = (institution: Institution) => {
    navigation.navigate('InstitutionDetails', { institutionId: institution.id });
  };

  const renderInstitutionCard = ({ item }: { item: Institution }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => handleInstitutionPress(item)}
    >
      {item.logo_url && (
        <Image source={{ uri: item.logo_url }} style={styles.logo} />
      )}
      <View style={styles.cardContent}>
        <Text style={styles.institutionName} numberOfLines={2}>
          {item.name}
        </Text>
        <Text style={styles.institutionType}>{item.type}</Text>
        <Text style={styles.location}>
          {item.district}, {item.division}
        </Text>
        {item.rating && (
          <View style={styles.ratingRow}>
            <Text style={styles.rating}>⭐ {item.rating.toFixed(1)}</Text>
            <Text style={styles.reviews}>({item.review_count} reviews)</Text>
          </View>
        )}
      </View>
      <TouchableOpacity
        style={styles.removeButton}
        onPress={() => handleRemove(item.id)}
      >
        <Text style={styles.removeIcon}>✕</Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={loadSavedInstitutions}
          >
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {savedInstitutions.length > 0 ? (
        <FlatList
          data={savedInstitutions}
          renderItem={renderInstitutionCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      ) : (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>❤️</Text>
          <Text style={styles.emptyText}>No Saved Institutions</Text>
          <Text style={styles.emptySubtext}>
            Explore and save your favorite institutions
          </Text>
          <TouchableOpacity
            style={styles.exploreButton}
            onPress={() => navigation.navigate('Search')}
          >
            <Text style={styles.exploreButtonText}>Start Exploring</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
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
  },
  listContent: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  card: {
    flexDirection: 'row',
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    alignItems: 'center',
  },
  logo: {
    width: 70,
    height: 70,
    borderRadius: 8,
    marginRight: 12,
  },
  cardContent: {
    flex: 1,
  },
  institutionName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  institutionType: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 2,
  },
  location: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 4,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rating: {
    fontSize: 12,
    color: '#f59e0b',
    fontWeight: '600',
  },
  reviews: {
    fontSize: 12,
    color: '#9ca3af',
    marginLeft: 4,
  },
  removeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#fee2e2',
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeIcon: {
    fontSize: 18,
    color: '#dc2626',
    fontWeight: 'bold',
  },
  errorContainer: {
    margin: 16,
    padding: 12,
    backgroundColor: '#fee2e2',
    borderRadius: 8,
  },
  errorText: {
    color: '#dc2626',
    fontSize: 14,
    marginBottom: 8,
  },
  retryButton: {
    backgroundColor: '#dc2626',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  retryButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 12,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  emptyIcon: {
    fontSize: 56,
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
    marginBottom: 20,
  },
  exploreButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  exploreButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },
});
