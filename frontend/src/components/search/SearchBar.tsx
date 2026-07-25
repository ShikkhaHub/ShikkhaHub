import { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, Loader2 } from 'lucide-react';
import { Input } from '../common/Input';
import { useSearchStore } from '../../stores';
import { getAutocompleteSuggestions } from '../../api';
import { useDebounce } from '../../hooks';
import type { AutocompleteSuggestion } from '../../types';

interface SearchBarProps {
  initialQuery?: string;
  onSearch?: (query: string) => void;
  showAutocomplete?: boolean;
  size?: 'sm' | 'md' | 'lg';
  placeholder?: string;
  className?: string;
}

export function SearchBar({
  initialQuery = '',
  onSearch,
  showAutocomplete = true,
  size = 'md',
  placeholder = 'Search institutions, universities, colleges...',
  className = '',
}: SearchBarProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState(initialQuery);
  const [isFocused, setIsFocused] = useState(false);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { addToHistory } = useSearchStore();
  const debouncedQuery = useDebounce(query, 200);

  // Fetch autocomplete suggestions
  useEffect(() => {
    if (!showAutocomplete || debouncedQuery.length < 2) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    getAutocompleteSuggestions(debouncedQuery, 5)
      .then((data) => {
        setSuggestions(data);
        setSelectedIndex(-1);
      })
      .catch(() => setSuggestions([]))
      .finally(() => setLoading(false));
  }, [debouncedQuery, showAutocomplete]);

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev > -1 ? prev - 1 : prev));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedIndex >= 0 && suggestions[selectedIndex]) {
          handleSelectSuggestion(suggestions[selectedIndex]);
        } else {
          handleSearch();
        }
      } else if (e.key === 'Escape') {
        setIsFocused(false);
        inputRef.current?.blur();
      }
    },
    [suggestions, selectedIndex]
  );

  const handleSearch = () => {
    if (!query.trim()) return;

    addToHistory(query);
    setIsFocused(false);

    if (onSearch) {
      onSearch(query);
    } else {
      navigate(`/institutions?q=${encodeURIComponent(query)}`);
    }
  };

  const handleSelectSuggestion = (suggestion: AutocompleteSuggestion) => {
    setQuery(suggestion.name);
    setIsFocused(false);
    navigate(`/institutions/${suggestion.slug}`);
  };

  const handleClear = () => {
    setQuery('');
    setSuggestions([]);
    inputRef.current?.focus();
  };

  const sizes = {
    sm: 'h-9 text-sm',
    md: 'h-12 text-base',
    lg: 'h-14 text-lg',
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="relative">
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={`w-full ${sizes[size]} pr-20`}
          leftIcon={<Search className="h-5 w-5 text-muted-foreground" />}
        />

        {/* Right side actions */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {loading && <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />}
          {query && (
            <button
              onClick={handleClear}
              className="p-1 hover:bg-secondary rounded-full transition-colors"
              aria-label="Clear search"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          )}
          <button
            onClick={handleSearch}
            className="px-4 py-1.5 bg-primary text-primary-foreground rounded-md hover:bg-primary-hover transition-colors text-sm font-medium"
          >
            Search
          </button>
        </div>
      </div>

      {/* Autocomplete dropdown */}
      {isFocused && suggestions.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-card border border-border rounded-lg shadow-elevated overflow-hidden">
          <ul className="py-2">
            {suggestions.map((suggestion, index) => (
              <li
                key={suggestion.id}
                onClick={() => handleSelectSuggestion(suggestion)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`px-4 py-3 cursor-pointer flex items-center justify-between ${
                  index === selectedIndex ? 'bg-primary-light' : 'hover:bg-secondary'
                }`}
              >
                <div className="flex flex-col">
                  <span className="font-medium text-foreground">{suggestion.name}</span>
                  {suggestion.short_name && (
                    <span className="text-sm text-muted-foreground">{suggestion.short_name}</span>
                  )}
                </div>
                {suggestion.type && (
                  <span className="text-xs bg-secondary px-2 py-1 rounded-full text-muted-foreground">
                    {suggestion.type}
                  </span>
                )}
              </li>
            ))}
          </ul>

          {/* Search all option */}
          <div className="border-t border-border px-4 py-3 bg-muted/50">
            <button
              onClick={handleSearch}
              className="text-sm text-primary hover:text-primary-hover font-medium"
            >
              Search all institutions for &quot;{query}&quot;
            </button>
          </div>
        </div>
      )}

      {/* Keyboard shortcut hint */}
      <div className="absolute right-4 -bottom-6 text-xs text-muted-foreground hidden sm:block">
        Press <kbd className="px-1.5 py-0.5 bg-secondary rounded text-xs">Enter</kbd> to search
      </div>
    </div>
  );
}
