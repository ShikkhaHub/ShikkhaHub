import { cn } from '../lib/utils'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-gray-200',
        className
      )}
    />
  )
}

// Institution Card Skeleton
export function InstitutionCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
      {/* Header */}
      <div className="flex items-start gap-4 mb-4">
        <Skeleton className="w-14 h-14 rounded-xl flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-2 mb-4">
        <Skeleton className="h-6 w-24 rounded-lg" />
        <Skeleton className="h-6 w-20 rounded-lg" />
      </div>

      {/* Location */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Skeleton className="w-4 h-4 rounded" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <Skeleton className="h-4 w-3/4 ml-6" />
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <Skeleton className="h-4 w-24" />
      </div>
    </div>
  )
}

// Institution Detail Skeleton
export function InstitutionDetailSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <Skeleton className="h-5 w-32" />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Main Header Card */}
        <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-8 mb-6">
          <div className="flex items-start gap-6">
            <Skeleton className="w-20 h-20 rounded-2xl flex-shrink-0" />
            <div className="flex-1 space-y-3">
              <div className="flex items-start justify-between">
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-8 w-2/3" />
                  <Skeleton className="h-6 w-1/3" />
                </div>
                <Skeleton className="h-8 w-24 rounded-full" />
              </div>
              <div className="flex flex-wrap gap-2 pt-2">
                <Skeleton className="h-7 w-28 rounded-lg" />
                <Skeleton className="h-7 w-24 rounded-lg" />
                <Skeleton className="h-7 w-32 rounded-lg" />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Overview Section */}
            <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <Skeleton className="h-6 w-32 mb-4" />
              <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/6" />
              </div>
            </div>

            {/* Courses Section */}
            <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <Skeleton className="h-6 w-40 mb-4" />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-24 rounded-xl" />
                ))}
              </div>
            </div>

            {/* Admission Section */}
            <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <Skeleton className="h-6 w-48 mb-4" />
              <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-5/6" />
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Contact Card */}
            <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <Skeleton className="h-6 w-24 mb-4" />
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="flex items-center gap-3">
                    <Skeleton className="w-10 h-10 rounded-lg" />
                    <div className="flex-1 space-y-1">
                      <Skeleton className="h-3 w-16" />
                      <Skeleton className="h-4 w-32" />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Location Card */}
            <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <Skeleton className="h-6 w-20 mb-4" />
              <Skeleton className="h-48 rounded-xl" />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

// Search Results Skeleton
export function SearchResultsSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-5 w-24" />
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: count }).map((_, i) => (
          <InstitutionCardSkeleton key={i} />
        ))}
      </div>
    </div>
  )
}

// Listing Page Skeleton
export function InstitutionListingSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Skeleton className="w-6 h-6 rounded" />
              <Skeleton className="h-6 w-32" />
            </div>
            <Skeleton className="h-5 w-24" />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Page Title */}
        <div className="mb-8 space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-5 w-64" />
        </div>

        {/* Filters Bar */}
        <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-5 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Skeleton className="w-5 h-5 rounded" />
            <Skeleton className="h-5 w-16" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="space-y-1">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-11 w-full rounded-xl" />
              </div>
            ))}
          </div>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 9 }).map((_, i) => (
            <InstitutionCardSkeleton key={i} />
          ))}
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-center gap-2 mt-8">
          <Skeleton className="h-10 w-24 rounded-lg" />
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="w-10 h-10 rounded-lg" />
            ))}
          </div>
          <Skeleton className="h-10 w-20 rounded-lg" />
        </div>
      </main>
    </div>
  )
}

// Hero Section Skeleton
export function HeroSectionSkeleton() {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700">
      <div className="relative z-10 px-8 py-12 md:px-12 md:py-16">
        <div className="max-w-3xl mx-auto text-center space-y-6">
          {/* Title */}
          <div className="space-y-3">
            <Skeleton className="h-10 w-3/4 mx-auto bg-white/20" />
            <Skeleton className="h-6 w-1/2 mx-auto bg-white/20" />
          </div>

          {/* Search Input */}
          <Skeleton className="h-14 w-full max-w-xl mx-auto rounded-2xl bg-white/20" />

          {/* Stats */}
          <div className="flex items-center justify-center gap-8 pt-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="text-center space-y-1">
                <Skeleton className="h-8 w-16 mx-auto bg-white/20" />
                <Skeleton className="h-4 w-20 mx-auto bg-white/20" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// Stats Section Skeleton
export function StatsSectionSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="bg-white rounded-2xl shadow-soft border border-gray-100 p-5">
          <div className="flex items-center gap-4">
            <Skeleton className="w-12 h-12 rounded-xl" />
            <div className="space-y-1">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// Popular Institutions Skeleton
export function PopularInstitutionsSkeleton() {
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-5 w-20" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-card">
            <Skeleton className="h-36 w-full" />
            <div className="p-4 space-y-2">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <div className="flex items-center justify-between pt-2">
                <Skeleton className="h-6 w-20 rounded-md" />
                <Skeleton className="h-4 w-16" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
