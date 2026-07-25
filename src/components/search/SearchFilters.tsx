import { useEffect, useState } from 'react';
import { Filter, X } from 'lucide-react';
import { Button } from '../common/Button';
import { Card, CardContent } from '../common/Card';
import { useSearchStore } from '../../stores';
import { getInstitutionTypes, getDivisions, getDistricts } from '../../api';
import type { InstitutionType, Division, District } from '../../types';

interface SearchFiltersProps {
  onApplyFilters?: () => void;
}

export function SearchFilters({ onApplyFilters }: SearchFiltersProps) {
  const { filters, setFilters } = useSearchStore();
  const [types, setTypes] = useState<InstitutionType[]>([]);
  const [divisions, setDivisions] = useState<Division[]>([]);
  const [districts, setDistricts] = useState<District[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  // Load filter options
  useEffect(() => {
    Promise.all([getInstitutionTypes(), getDivisions()]).then(
      ([typesData, divisionsData]) => {
        setTypes(typesData);
        setDivisions(divisionsData);
      }
    );
  }, []);

  // Load districts when division changes
  useEffect(() => {
    if (filters.division_id) {
      getDistricts(filters.division_id).then(setDistricts);
    } else {
      setDistricts([]);
    }
  }, [filters.division_id]);

  const handleTypeChange = (typeId: string) => {
    setFilters({
      ...filters,
      type_id: typeId ? parseInt(typeId) : undefined,
    });
  };

  const handleDivisionChange = (divisionId: string) => {
    setFilters({
      ...filters,
      division_id: divisionId ? parseInt(divisionId) : undefined,
      district_id: undefined, // Reset district when division changes
    });
  };

  const handleDistrictChange = (districtId: string) => {
    setFilters({
      ...filters,
      district_id: districtId ? parseInt(districtId) : undefined,
    });
  };

  const handleClearFilters = () => {
    setFilters({});
  };

  const hasActiveFilters = Object.keys(filters).length > 0;

  return (
    <div>
      {/* Toggle Button */}
      <Button
        variant={hasActiveFilters ? 'primary' : 'outline'}
        size="sm"
        onClick={() => setShowFilters(!showFilters)}
        leftIcon={<Filter className="h-4 w-4" />}
      >
        Filters {hasActiveFilters && `(${Object.keys(filters).length})`}
      </Button>

      {/* Filters Panel */}
      {showFilters && (
        <Card className="mt-3">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium">Filter Results</h3>
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearFilters}
                  leftIcon={<X className="h-4 w-4" />}
                >
                  Clear all
                </Button>
              )}
            </div>

            <div className="grid sm:grid-cols-3 gap-4">
              {/* Institution Type */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Institution Type
                </label>
                <select
                  value={filters.type_id || ''}
                  onChange={(e) => handleTypeChange(e.target.value)}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">All Types</option>
                  {types.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Division */}
              <div>
                <label className="block text-sm font-medium mb-2">Division</label>
                <select
                  value={filters.division_id || ''}
                  onChange={(e) => handleDivisionChange(e.target.value)}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">All Divisions</option>
                  {divisions.map((division) => (
                    <option key={division.id} value={division.id}>
                      {division.name_en}
                    </option>
                  ))}
                </select>
              </div>

              {/* District */}
              <div>
                <label className="block text-sm font-medium mb-2">District</label>
                <select
                  value={filters.district_id || ''}
                  onChange={(e) => handleDistrictChange(e.target.value)}
                  disabled={!filters.division_id}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                >
                  <option value="">
                    {filters.division_id ? 'All Districts' : 'Select Division first'}
                  </option>
                  {districts.map((district) => (
                    <option key={district.id} value={district.id}>
                      {district.name_en}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {onApplyFilters && (
              <div className="mt-4 flex justify-end">
                <Button onClick={onApplyFilters} size="sm">
                  Apply Filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
