import { Link } from 'react-router-dom'
import { Building2, MapPin, Phone, Globe, ExternalLink, GraduationCap } from 'lucide-react'
import type { Institution } from '../lib/api'
import { Skeleton } from './Skeleton'

interface SearchResultsProps {
  results: Institution[]
  query: string
  isLoading?: boolean
}

export default function SearchResults({ results, query, isLoading }: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50/50">
          <Skeleton className="h-5 w-48" />
        </div>
        <div className="divide-y divide-gray-100">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-5">
              <div className="flex items-start gap-4">
                <Skeleton className="w-12 h-12 rounded-xl flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="flex items-start justify-between">
                    <Skeleton className="h-6 w-48" />
                    <Skeleton className="w-5 h-5 rounded" />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Skeleton className="h-5 w-20 rounded-full" />
                    <Skeleton className="h-5 w-16 rounded-full" />
                  </div>
                  <div className="flex flex-wrap gap-4 pt-1">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (results.length === 0 && query) {
    return (
      <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-8">
        <div className="text-center">
          <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            No institutions found
          </h3>
          <p className="text-gray-500">
            Try adjusting your search terms or filters
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 overflow-hidden">
      <div className="p-4 border-b border-gray-100 bg-gray-50/50">
        <p className="text-sm text-gray-600">
          Found <span className="font-medium text-gray-900">{results.length}</span> results for "{query}"
        </p>
      </div>

      <div className="divide-y divide-gray-100">
        {results.map((institution) => (
          <div
            key={institution.id}
            className="p-5 hover:bg-gray-50/50 transition-colors duration-200"
          >
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center flex-shrink-0">
                <GraduationCap className="w-6 h-6 text-indigo-600" />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">
                      {institution.name_en}
                    </h3>
                    {institution.name_bn && (
                      <p className="text-sm text-gray-600 mt-0.5">
                        {institution.name_bn}
                      </p>
                    )}
                  </div>
                  <Link
                    to={`/institutions/${institution.slug}`}
                    className="text-indigo-600 hover:text-indigo-700 transition-colors"
                  >
                    <ExternalLink className="w-5 h-5" />
                  </Link>
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-2 mt-2">
                  {institution.type_name && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {institution.type_name}
                    </span>
                  )}
                  {institution.established_year && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Est. {institution.established_year}
                    </span>
                  )}
                  {institution.verification_status === 'verified' && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                      Verified
                    </span>
                  )}
                </div>

                {/* Contact Info */}
                <div className="flex flex-wrap gap-4 mt-3 text-sm text-gray-500">
                  {(institution.division_name || institution.district_name) && (
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-4 h-4" />
                      <span>
                        {[institution.division_name, institution.district_name]
                          .filter(Boolean)
                          .join(', ')}
                      </span>
                    </div>
                  )}
                  {institution.phone && (
                    <div className="flex items-center gap-1.5">
                      <Phone className="w-4 h-4" />
                      <span>{institution.phone}</span>
                    </div>
                  )}
                  {institution.website && (
                    <a
                      href={institution.website.startsWith('http') ? institution.website : `https://${institution.website}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 text-indigo-600 hover:text-indigo-700"
                    >
                      <Globe className="w-4 h-4" />
                      <span className="truncate max-w-[200px]">
                        {institution.website.replace(/^https?:\/\//, '')}
                      </span>
                    </a>
                  )}
                </div>

                {institution.address && (
                  <p className="text-sm text-gray-500 mt-2">
                    {institution.address}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
