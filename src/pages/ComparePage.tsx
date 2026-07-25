import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { 
  Scale, 
  X, 
  ArrowLeft, 
  Building2, 
  MapPin, 
  Phone, 
  Globe, 
  Mail,
  Calendar,
  GraduationCap,
  CheckCircle,
  Plus
} from 'lucide-react'
import { getComparisonList, removeFromComparison, clearComparison } from '../lib/compareStore'
import type { Institution } from '../lib/api'

export default function ComparePage() {
  const navigate = useNavigate()
  const [institutions, setInstitutions] = useState<Institution[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const list = getComparisonList()
    setInstitutions(list)
    setLoading(false)
  }, [])

  const handleRemove = (id: number) => {
    removeFromComparison(id)
    setInstitutions(prev => prev.filter(i => i.id !== id))
  }

  const handleClear = () => {
    clearComparison()
    setInstitutions([])
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex items-center gap-3 text-gray-500">
          <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

  if (institutions.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
                <Building2 className="w-6 h-6 text-indigo-600" />
                <span className="font-bold text-xl text-gray-900">ShikkhaHub</span>
              </Link>
            </div>
          </div>
        </header>

        <main className="max-w-4xl mx-auto px-6 py-16">
          <div className="text-center">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Scale className="w-10 h-10 text-gray-400" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-3">
              No Institutions to Compare
            </h1>
            <p className="text-gray-500 mb-8 max-w-md mx-auto">
              Add institutions to your comparison list to see them side by side and compare their features.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                to="/institutions"
                className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                Browse Institutions
              </Link>
              <Link
                to="/"
                className="px-6 py-3 text-gray-700 font-medium hover:text-gray-900 transition-colors"
              >
                Go Home
              </Link>
            </div>
          </div>
        </main>
      </div>
    )
  }

  const compareFields = [
    { key: 'name_en', label: 'Name', icon: Building2 },
    { key: 'type_name', label: 'Type', icon: GraduationCap },
    { key: 'established_year', label: 'Established', icon: Calendar },
    { key: 'division_name', label: 'Division', icon: MapPin },
    { key: 'district_name', label: 'District', icon: MapPin },
    { key: 'address', label: 'Address', icon: MapPin },
    { key: 'phone', label: 'Phone', icon: Phone },
    { key: 'email', label: 'Email', icon: Mail },
    { key: 'website', label: 'Website', icon: Globe },
    { key: 'verification_status', label: 'Status', icon: CheckCircle },
  ]

  const getValue = (institution: Institution, key: string): string => {
    const value = institution[key as keyof Institution]
    if (value === null || value === undefined) return '-'
    if (key === 'verification_status') {
      return value === 'verified' ? 'Verified' : 'Pending'
    }
    if (key === 'website' && typeof value === 'string') {
      return value.replace(/^https?:\/\//, '').replace(/\/$/, '')
    }
    return String(value)
  }

  const isDifferent = (key: string): boolean => {
    if (institutions.length < 2) return false
    const values = institutions.map(i => getValue(i, key))
    return new Set(values).size > 1
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-gray-900">
                <Building2 className="w-6 h-6 text-indigo-600" />
                <span className="font-bold text-xl text-gray-900">ShikkhaHub</span>
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500">
                Comparing {institutions.length} institution{institutions.length > 1 ? 's' : ''}
              </span>
              {institutions.length > 0 && (
                <button
                  onClick={handleClear}
                  className="text-sm text-red-600 hover:text-red-700 font-medium"
                >
                  Clear All
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Back Link */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back</span>
        </button>

        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Scale className="w-8 h-8 text-indigo-600" />
            Compare Institutions
          </h1>
          <p className="text-gray-600 mt-2">
            Side-by-side comparison to help you make the right choice
          </p>
        </div>

        {/* Add More Button (if less than 3) */}
        {institutions.length < 3 && (
          <div className="mb-6">
            <Link
              to="/institutions"
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Add {3 - institutions.length} more to compare
            </Link>
          </div>
        )}

        {/* Comparison Table */}
        <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 overflow-hidden">
          {/* Institution Headers */}
          <div className="grid border-b border-gray-100" style={{ gridTemplateColumns: `200px repeat(${institutions.length}, 1fr)` }}>
            <div className="p-6 bg-gray-50/50 border-r border-gray-100 flex items-end">
              <span className="text-sm font-medium text-gray-500">Features</span>
            </div>
            {institutions.map((institution) => (
              <div key={institution.id} className="p-6 border-r border-gray-100 last:border-r-0 relative">
                <button
                  onClick={() => handleRemove(institution.id)}
                  className="absolute top-4 right-4 w-6 h-6 rounded-full bg-gray-100 text-gray-400 hover:bg-red-100 hover:text-red-500 flex items-center justify-center transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center mb-4">
                  <GraduationCap className="w-7 h-7 text-indigo-600" />
                </div>
                <h3 className="font-semibold text-gray-900 text-lg pr-8">
                  {institution.name_en}
                </h3>
                {institution.short_name && (
                  <p className="text-sm text-gray-500">{institution.short_name}</p>
                )}
                <Link
                  to={`/institutions/${institution.slug}`}
                  className="mt-3 inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700"
                >
                  View Details →
                </Link>
              </div>
            ))}
          </div>

          {/* Comparison Rows */}
          {compareFields.map((field) => {
            const different = isDifferent(field.key)
            return (
              <div 
                key={field.key}
                className={`grid border-b border-gray-100 last:border-b-0 ${different ? 'bg-amber-50/30' : ''}`}
                style={{ gridTemplateColumns: `200px repeat(${institutions.length}, 1fr)` }}
              >
                <div className="p-4 bg-gray-50/50 border-r border-gray-100 flex items-center gap-2">
                  <field.icon className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">{field.label}</span>
                  {different && (
                    <span className="ml-auto text-xs text-amber-600 font-medium">Diff</span>
                  )}
                </div>
                {institutions.map((institution) => {
                  const value = getValue(institution, field.key)
                  const isLink = field.key === 'website' && value !== '-'
                  const isEmail = field.key === 'email' && value !== '-'
                  
                  return (
                    <div 
                      key={institution.id} 
                      className={`p-4 border-r border-gray-100 last:border-r-0 ${different ? 'bg-amber-50/50' : ''}`}
                    >
                      {isLink ? (
                        <a 
                          href={value.startsWith('http') ? value : `https://${value}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-700 text-sm break-all"
                        >
                          {value}
                        </a>
                      ) : isEmail ? (
                        <a 
                          href={`mailto:${value}`}
                          className="text-indigo-600 hover:text-indigo-700 text-sm break-all"
                        >
                          {value}
                        </a>
                      ) : (
                        <span className={`text-sm ${value === '-' ? 'text-gray-400' : 'text-gray-700'}`}>
                          {value}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="mt-6 flex items-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-amber-50 border border-amber-200 rounded" />
            <span>Highlighted rows show differences</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">-</span>
            <span>Data not available</span>
          </div>
        </div>
      </main>
    </div>
  )
}
