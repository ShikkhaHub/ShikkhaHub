import { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { 
  Building2, 
  MapPin, 
  Filter,
  ChevronDown,
  GraduationCap,
  Search,
  ChevronLeft,
  ChevronRight,
  Scale
} from 'lucide-react'
import { getInstitutions, getDivisions, type Institution, type InstitutionListResponse, type Division } from '../lib/api'
import CompareButton from '../components/CompareButton'
import { getComparisonCount } from '../lib/compareStore'
import { InstitutionCardSkeleton } from '../components/Skeleton'

const INSTITUTION_TYPES = [
  { id: 1, name: 'University', slug: 'university' },
  { id: 2, name: 'College', slug: 'college' },
  { id: 3, name: 'Polytechnic', slug: 'polytechnic' },
  { id: 4, name: 'School', slug: 'school' },
  { id: 5, name: 'Institute', slug: 'institute' },
  { id: 6, name: 'Madrasa', slug: 'madrasa' }
]

const VERIFICATION_STATUSES = [
  { value: 'verified', label: 'Verified' },
  { value: 'pending', label: 'Pending' },
  { value: 'all', label: 'All' }
]

export default function InstitutionListing() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0
  })
  const [divisions, setDivisions] = useState<Division[]>([])
  const [compareCount, setCompareCount] = useState(0)

  // Filter states from URL params
  const [filters, setFilters] = useState({
    type_id: searchParams.get('type') ? parseInt(searchParams.get('type')!) : undefined,
    division_id: searchParams.get('division') ? parseInt(searchParams.get('division')!) : undefined,
    verification_status: searchParams.get('status') || 'pending',
    page: searchParams.get('page') ? parseInt(searchParams.get('page')!) : 1
  })

  // Fetch divisions on mount and update compare count
  useEffect(() => {
    const fetchDivisions = async () => {
      try {
        console.log('Fetching divisions...')
        const data = await getDivisions()
        console.log('Divisions loaded:', data)
        setDivisions(data)
      } catch (err) {
        console.error('Failed to load divisions:', err)
        // Set empty divisions array to prevent UI breaking
        setDivisions([])
      }
    }
    fetchDivisions()
    setCompareCount(getComparisonCount())
  }, [])

  // Fetch institutions when filters change
  const fetchInstitutions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const status = filters.verification_status === 'all' ? undefined : filters.verification_status
      const response: InstitutionListResponse = await getInstitutions({
        type_id: filters.type_id,
        division_id: filters.division_id,
        verification_status: status,
        page: filters.page,
        page_size: 20
      })
      setInstitutions(response.items)
      setPagination({
        page: response.page,
        page_size: response.page_size,
        total: response.total,
        pages: response.pages
      })
    } catch (err) {
      setError('Failed to load institutions')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchInstitutions()
  }, [fetchInstitutions])

  // Update URL when filters change
  const updateFilter = (key: string, value: string | number | undefined) => {
    const newFilters = { ...filters, [key]: value, page: 1 }
    setFilters(newFilters)
    
    const params = new URLSearchParams()
    if (newFilters.type_id) params.set('type', newFilters.type_id.toString())
    if (newFilters.division_id) params.set('division', newFilters.division_id.toString())
    if (newFilters.verification_status && newFilters.verification_status !== 'all') {
      params.set('status', newFilters.verification_status)
    }
    if (newFilters.page > 1) params.set('page', newFilters.page.toString())
    setSearchParams(params)
  }

  const goToPage = (page: number) => {
    if (page < 1 || page > pagination.pages) return
    setFilters({ ...filters, page })
    
    const params = new URLSearchParams(searchParams)
    if (page > 1) {
      params.set('page', page.toString())
    } else {
      params.delete('page')
    }
    setSearchParams(params)
  }

  const clearFilters = () => {
    setFilters({
      type_id: undefined,
      division_id: undefined,
      verification_status: 'pending',
      page: 1
    })
    setSearchParams(new URLSearchParams())
  }

  const hasActiveFilters = filters.type_id || filters.division_id || filters.verification_status !== 'pending'

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
                <Building2 className="w-6 h-6 text-indigo-600" />
                <span className="font-bold text-xl text-gray-900">ShikkhaHub</span>
              </Link>
            </div>
            <div className="flex items-center gap-4">
              {compareCount > 0 && (
                <Link
                  to="/compare"
                  className="flex items-center gap-2 px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium hover:bg-indigo-200 transition-colors"
                >
                  <Scale className="w-4 h-4" />
                  Compare ({compareCount})
                </Link>
              )}
              <Link 
                to="/"
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
              >
                <Search className="w-5 h-5" />
                <span>Search</span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-6 py-6 md:py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Institutions</h1>
          <p className="text-gray-600 mt-2">
            Browse {pagination.total.toLocaleString()} educational institutions across Bangladesh
          </p>
        </div>

        {/* Filters Bar */}
        <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-5 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-indigo-600" />
            <h2 className="font-semibold text-gray-900">Filters</h2>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="ml-auto text-sm text-indigo-600 hover:text-indigo-700"
              >
                Clear all
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Institution Type Filter */}
            <div className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Institution Type
              </label>
              <div className="relative">
                <select
                  value={filters.type_id || ''}
                  onChange={(e) => updateFilter('type_id', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full h-11 pl-4 pr-10 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">All Types</option>
                  {INSTITUTION_TYPES.map((type) => (
                    <option key={type.id} value={type.id}>{type.name}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Division Filter */}
            <div className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Division
              </label>
              <div className="relative">
                <select
                  value={filters.division_id || ''}
                  onChange={(e) => updateFilter('division_id', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full h-11 pl-4 pr-10 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">All Divisions</option>
                  {divisions.map((div) => (
                    <option key={div.id} value={div.id}>{div.name_en}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Verification Status Filter */}
            <div className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Status
              </label>
              <div className="relative">
                <select
                  value={filters.verification_status}
                  onChange={(e) => updateFilter('verification_status', e.target.value)}
                  className="w-full h-11 pl-4 pr-10 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer"
                >
                  {VERIFICATION_STATUSES.map((status) => (
                    <option key={status.value} value={status.value}>{status.label}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>
          </div>
        </div>

        {/* Results Count */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-gray-600">
            Showing <span className="font-medium text-gray-900">{institutions.length}</span> of{' '}
            <span className="font-medium text-gray-900">{pagination.total}</span> institutions
          </p>
          {pagination.pages > 1 && (
            <p className="text-sm text-gray-500">
              Page {pagination.page} of {pagination.pages}
            </p>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 9 }).map((_, i) => (
              <InstitutionCardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-100 rounded-xl p-6 text-center">
            <p className="text-red-600">{error}</p>
            <button
              onClick={fetchInstitutions}
              className="mt-3 text-sm text-red-600 hover:text-red-700 font-medium"
            >
              Try again
            </button>
          </div>
        )}

        {/* Institution Cards Grid */}
        {!loading && !error && (
          <>
            {institutions.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-12 text-center">
                <Building2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No institutions found
                </h3>
                <p className="text-gray-500 mb-4">
                  Try adjusting your filters to see more results
                </p>
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="text-indigo-600 hover:text-indigo-700 font-medium"
                  >
                    Clear all filters
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {institutions.map((institution) => (
                  <div
                    key={institution.id}
                    className="group bg-white rounded-2xl shadow-elevated border border-gray-100 p-6 hover:shadow-lg hover:border-indigo-200 transition-all duration-200"
                  >
                    {/* Card Header */}
                    <div className="flex items-start gap-4 mb-4">
                      <Link 
                        to={`/institutions/${institution.slug}`}
                        className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center flex-shrink-0 group-hover:from-indigo-200 group-hover:to-violet-200 transition-colors"
                      >
                        <GraduationCap className="w-7 h-7 text-indigo-600" />
                      </Link>
                      <div className="flex-1 min-w-0">
                        <Link to={`/institutions/${institution.slug}`}>
                          <h3 className="font-semibold text-gray-900 text-lg leading-tight group-hover:text-indigo-600 transition-colors">
                            {institution.name_en}
                          </h3>
                        </Link>
                        {institution.short_name && (
                          <p className="text-sm text-gray-500 mt-0.5">
                            {institution.short_name}
                          </p>
                        )}
                      </div>
                      <CompareButton 
                        institution={institution} 
                        size="sm" 
                        variant="icon"
                        onToggle={() => setCompareCount(getComparisonCount())}
                      />
                    </div>

                    {/* Badges */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {institution.type_name && (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-100 text-blue-700">
                          {institution.type_name}
                        </span>
                      )}
                      {institution.established_year && (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-green-100 text-green-700">
                          Est. {institution.established_year}
                        </span>
                      )}
                      {institution.verification_status === 'verified' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-emerald-100 text-emerald-700">
                          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          Verified
                        </span>
                      )}
                    </div>

                    {/* Location & Contact */}
                    <div className="space-y-2 text-sm">
                      {(institution.division_name || institution.district_name) && (
                        <div className="flex items-center gap-2 text-gray-500">
                          <MapPin className="w-4 h-4 flex-shrink-0" />
                          <span className="truncate">
                            {[institution.division_name, institution.district_name]
                              .filter(Boolean)
                              .join(', ')}
                          </span>
                        </div>
                      )}
                      {institution.address && (
                        <p className="text-gray-500 line-clamp-2 pl-6">
                          {institution.address}
                        </p>
                      )}
                    </div>

                    {/* View Link */}
                    <Link 
                      to={`/institutions/${institution.slug}`}
                      className="mt-4 pt-4 border-t border-gray-100 block"
                    >
                      <span className="text-sm font-medium text-indigo-600 group-hover:text-indigo-700 flex items-center gap-1">
                        View Details
                        <ChevronRight className="w-4 h-4" />
                      </span>
                    </Link>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => goToPage(pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                    // Show pages around current page
                    let pageNum = i + 1
                    if (pagination.pages > 5) {
                      if (pagination.page > 3) {
                        pageNum = pagination.page - 2 + i
                      }
                      if (pageNum > pagination.pages) {
                        pageNum = pagination.pages - (4 - i)
                      }
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => goToPage(pageNum)}
                        className={`w-10 h-10 rounded-lg text-sm font-medium transition-colors ${
                          pageNum === pagination.page
                            ? 'bg-indigo-600 text-white'
                            : 'text-gray-700 hover:bg-gray-100'
                        }`}
                      >
                        {pageNum}
                      </button>
                    )
                  })}
                </div>

                <button
                  onClick={() => goToPage(pagination.page + 1)}
                  disabled={pagination.page === pagination.pages}
                  className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
