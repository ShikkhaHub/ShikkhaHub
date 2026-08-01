import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { apiService, Institution } from '../services/api';

const { width } = Dimensions.get('window');

export default function HomeScreen() {
  const navigation = useNavigation();
  const [suggestions, setSuggestions] = useState<Institution[]>([]);
  const [divisions, setDivisions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [suggestionsRes, divisionsRes] = await Promise.all([
        apiService.getSuggestions(),
        apiService.getDivisions(),
      ]);

      setSuggestions(suggestionsRes.data);
      setDivisions(divisionsRes.data);
    } catch (err: any) {
      setError(apiService.handleError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleInstitutionPress = (institution: Institution) => {
    navigation.navigate('InstitutionDetails', { institutionId: institution.id });
  };

  const handleDivisionPress = (division: string) => {
    navigation.navigate('SearchTab', { 
      screen: 'SearchTab',
      params: { division } 
    });
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#2563eb" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.greeting}>Welcome to ShikkhaHub</Text>
        <Text style={styles.subGreeting}>Find your perfect institution</Text>
      </View>

      {/* Quick Search */}
      <TouchableOpacity
        style={styles.searchButton}
        onPress={() => navigation.navigate('Search')}
      >
        <Text style={styles.searchIcon}>🔍</Text>
        <Text style={styles.searchText}>Search institutions</Text>
      </TouchableOpacity>

      {/* Divisions Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Browse by Division</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {divisions.map((division) => (
            <TouchableOpacity
              key={division.id}
              style={styles.divisionCard}
              onPress={() => handleDivisionPress(division.name)}
            >
              <Text style={styles.divisionEmoji}>📍</Text>
              <Text style={styles.divisionName}>{division.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Suggested Institutions */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Popular Institutions</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Search')}>
            <Text style={styles.viewAll}>View All</Text>
          </TouchableOpacity>
        </View>

        {suggestions.map((institution) => (
          <TouchableOpacity
            key={institution.id}
            style={styles.institutionCard}
            onPress={() => handleInstitutionPress(institution)}
          >
            {institution.logo_url && (
              <Image
                source={{ uri: institution.logo_url }}
                style={styles.institutionLogo}
              />
            )}
            <View style={styles.institutionInfo}>
              <Text style={styles.institutionName} numberOfLines={2}>
                {institution.name}
              </Text>
              <Text style={styles.institutionType}>{institution.type}</Text>
              <View style={styles.ratingContainer}>
                <Text style={styles.rating}>⭐ {institution.rating?.toFixed(1) || 'N/A'}</Text>
                <Text style={styles.reviewCount}>
                  ({institution.review_count || 0} reviews)
                </Text>
              </View>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {/* Quick Links */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Links</Text>
        <View style={styles.quickLinksGrid}>
          <TouchableOpacity style={styles.quickLink}>
            <Text style={styles.quickLinkIcon}>💡</Text>
            <Text style={styles.quickLinkText}>AI Assistant</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickLink}>
            <Text style={styles.quickLinkIcon}>❓</Text>
            <Text style={styles.quickLinkText}>FAQs</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickLink}>
            <Text style={styles.quickLinkIcon}>📚</Text>
            <Text style={styles.quickLinkText}>Categories</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.quickLink}>
            <Text style={styles.quickLinkIcon}>⚙️</Text>
            <Text style={styles.quickLinkText}>Settings</Text>
          </TouchableOpacity>
        </View>
      </View>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity 
            style={styles.retryButton}
            onPress={loadHomeData}
          >
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}
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
  },
  header: {
    padding: 20,
    paddingTop: 16,
  },
  greeting: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  subGreeting: {
    fontSize: 14,
    color: '#6b7280',
  },
  searchButton: {
    margin: 16,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  searchIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  searchText: {
    fontSize: 16,
    color: '#6b7280',
  },
  section: {
    marginVertical: 16,
    paddingHorizontal: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  viewAll: {
    fontSize: 14,
    color: '#2563eb',
    fontWeight: '500',
  },
  divisionCard: {
    alignItems: 'center',
    marginRight: 16,
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    minWidth: 100,
  },
  divisionEmoji: {
    fontSize: 28,
    marginBottom: 8,
  },
  divisionName: {
    fontSize: 12,
    color: '#374151',
    fontWeight: '500',
    textAlign: 'center',
  },
  institutionCard: {
    flexDirection: 'row',
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    alignItems: 'center',
  },
  institutionLogo: {
    width: 60,
    height: 60,
    borderRadius: 8,
    marginRight: 12,
  },
  institutionInfo: {
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
    marginBottom: 4,
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rating: {
    fontSize: 12,
    color: '#f59e0b',
    fontWeight: '600',
  },
  reviewCount: {
    fontSize: 12,
    color: '#9ca3af',
    marginLeft: 4,
  },
  quickLinksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickLink: {
    width: '48%',
    aspectRatio: 1,
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  quickLinkIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  quickLinkText: {
    fontSize: 12,
    color: '#374151',
    fontWeight: '500',
    textAlign: 'center',
  },
  errorContainer: {
    margin: 16,
    padding: 12,
    backgroundColor: '#fee2e2',
    borderRadius: 8,
    marginBottom: 24,
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
  retryText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 12,
  },
});
