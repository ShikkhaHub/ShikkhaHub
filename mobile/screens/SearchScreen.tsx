import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Image,
  ScrollView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { apiService, Institution } from '../services/api';

export default function SearchScreen() {
  const navigation = useNavigation();
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<Institution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [divisions, setDivisions] = useState<any[]>([]);
  const [selectedDivision, setSelectedDivision] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    loadDivisions();
  }, []);

  useEffect(() => {
    if (searchQuery.length > 2) {
      loadSuggestions();
    }
  }, [searchQuery]);

  const loadDivisions = async () => {
    try {
      const response = await apiService.getDivisions();
      setDivisions(response.data);
    } catch (err) {
      console.log('[v0] Error loading divisions:', err);
    }
  };

  const loadSuggestions = async () => {
    try {
      const response = await apiService.autocomplete(searchQuery, 5);
      setSuggestions(response.data);
    } catch (err) {
      console.log('[v0] Error loading suggestions:', err);
    }
  };

  const handleSearch = async (query: string = searchQuery) => {
    if (!query && !selectedDivision && !selectedType) {
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await apiService.searchInstitutions({
        query: query || undefined,
        division: selectedDivision || undefined,
        type: selectedType || undefined,
        limit: 50,
      });

      setResults(response.data);
      setSuggestions([]);
    } catch (err: any) {
      setError(apiService.handleError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionPress = (suggestion: string) => {
    setSearchQuery(suggestion);
    setSuggestions([]);
    handleSearch(suggestion);
  };

  const handleInstitutionPress = (institution: Institution) => {
    navigation.navigate('InstitutionDetails', { institutionId: institution.id });
  };

  const renderInstitutionCard = ({ item }: { item: Institution }) => (
    <TouchableOpacity
      style={styles.resultCard}
      onPress={() => handleInstitutionPress(item)}
    >
      {item.logo_url && (
        <Image
          source={{ uri: item.logo_url }}
          style={styles.logo}
        />
      )}
      <View style={styles.resultInfo}>
        <Text style={styles.resultName} numberOfLines={2}>
          {item.name}
        </Text>
        <Text style={styles.resultType}>{item.type}</Text>
        <Text style={styles.resultLocation}>
          {item.district}, {item.division}
        </Text>
        {item.rating && (
          <View style={styles.ratingRow}>
            <Text style={styles.resultRating}>⭐ {item.rating.toFixed(1)}</Text>
            <Text style={styles.resultReviews}>({item.review_count} reviews)</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Search Header */}
      <View style={styles.searchHeader}>
        <View style={styles.searchInputContainer}>
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            style={styles.searchInput}
            placeholder="Search institutions..."
            placeholderTextColor="#d1d5db"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
          {searchQuery ? (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Text style={styles.clearIcon}>✕</Text>
            </TouchableOpacity>
          ) : null}
        </View>
        <TouchableOpacity
          style={styles.searchButton}
          onPress={() => handleSearch()}
        >
          <Text style={styles.searchButtonText}>Search</Text>
        </TouchableOpacity>
      </View>

      {/* Suggestions Dropdown */}
      {suggestions.length > 0 && (
        <View style={styles.suggestionsContainer}>
          {suggestions.map((suggestion, index) => (
            <TouchableOpacity
              key={index}
              style={styles.suggestionItem}
              onPress={() => handleSuggestionPress(suggestion)}
            >
              <Text style={styles.suggestionText}>{suggestion}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Filters */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filtersContainer}
      >
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {divisions.map((division) => (
            <TouchableOpacity
              key={division.id}
              style={[
                styles.filterChip,
                selectedDivision === division.name && styles.filterChipActive,
              ]}
              onPress={() => {
                setSelectedDivision(
                  selectedDivision === division.name ? null : division.name
                );
              }}
            >
              <Text
                style={[
                  styles.filterChipText,
                  selectedDivision === division.name && styles.filterChipTextActive,
                ]}
              >
                {division.name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </ScrollView>

      {/* Results */}
      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#2563eb" />
        </View>
      ) : error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={() => handleSearch()}
          >
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : results.length > 0 ? (
        <FlatList
          data={results}
          renderItem={renderInstitutionCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.resultsList}
          showsVerticalScrollIndicator={false}
        />
      ) : searchQuery || selectedDivision || selectedType ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🔍</Text>
          <Text style={styles.emptyText}>No institutions found</Text>
          <Text style={styles.emptySubtext}>
            Try different search terms or filters
          </Text>
        </View>
      ) : (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🔎</Text>
          <Text style={styles.emptyText}>Start Searching</Text>
          <Text style={styles.emptySubtext}>
            Search for institutions by name, type, or location
          </Text>
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
  searchHeader: {
    padding: 16,
    backgroundColor: '#f9fafb',
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  searchIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 14,
    color: '#1f2937',
  },
  clearIcon: {
    fontSize: 18,
    color: '#d1d5db',
  },
  searchButton: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  searchButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14,
  },
  suggestionsContainer: {
    position: 'absolute',
    top: 80,
    left: 16,
    right: 16,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    zIndex: 100,
    maxHeight: 200,
  },
  suggestionItem: {
    paddingHorizontal: 12,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  suggestionText: {
    color: '#374151',
    fontSize: 14,
  },
  filtersContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
    marginRight: 8,
  },
  filterChipActive: {
    backgroundColor: '#2563eb',
  },
  filterChipText: {
    fontSize: 12,
    color: '#6b7280',
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: '#ffffff',
  },
  resultsList: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  resultCard: {
    flexDirection: 'row',
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  logo: {
    width: 60,
    height: 60,
    borderRadius: 8,
    marginRight: 12,
  },
  resultInfo: {
    flex: 1,
  },
  resultName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  resultType: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 2,
  },
  resultLocation: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 4,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  resultRating: {
    fontSize: 12,
    color: '#f59e0b',
    fontWeight: '600',
  },
  resultReviews: {
    fontSize: 12,
    color: '#9ca3af',
    marginLeft: 4,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  errorText: {
    color: '#dc2626',
    fontSize: 14,
    marginBottom: 12,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#dc2626',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  emptyIcon: {
    fontSize: 64,
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
  },
});
