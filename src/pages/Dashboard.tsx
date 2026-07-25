import { useState } from 'react'
import LeftSidebar from '../components/LeftSidebar'
import TopHeader from '../components/TopHeader'
import HeroSection from '../components/HeroSection'
import StatsSection from '../components/StatsSection'
import PopularInstitutions from '../components/PopularInstitutions'
import SearchResults from '../components/SearchResults'
import RightSidebar from '../components/RightSidebar'
import RecentlyViewed from '../components/RecentlyViewed'
import type { Institution } from '../lib/api'

export default function Dashboard() {
  const [searchResults, setSearchResults] = useState<Institution[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleSearchResults = (results: Institution[], query: string) => {
    setSearchResults(results)
    setSearchQuery(query)
    setIsSearching(false)
  }

  const handleSearchStart = () => {
    setIsSearching(true)
  }

  const hasSearchResults = searchResults.length > 0 || searchQuery !== ''

  return (
    <div className="min-h-screen bg-background">
      {/* Left Sidebar - Responsive */}
      <LeftSidebar 
        isMobileOpen={isMobileMenuOpen} 
        onClose={() => setIsMobileMenuOpen(false)} 
      />

      {/* Main Content Area - Responsive margins */}
      <div className="lg:ml-64 xl:mr-80">
        {/* Top Header */}
        <TopHeader 
          onMenuClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          isMobileMenuOpen={isMobileMenuOpen}
        />

        {/* Main Content */}
        <main className="p-4 md:p-6">
          <div className="max-w-6xl mx-auto space-y-6">
            {/* Hero Section */}
            <HeroSection 
              onSearchResults={handleSearchResults}
              onSearchStart={handleSearchStart}
            />

            {/* Recently Viewed - show when not searching */}
            {!hasSearchResults && <RecentlyViewed />}

            {/* Stats Section - hide when searching */}
            {!hasSearchResults && <StatsSection />}

            {/* Search Results or Popular Institutions */}
            {hasSearchResults ? (
              <SearchResults 
                results={searchResults} 
                query={searchQuery}
                isLoading={isSearching}
              />
            ) : (
              <PopularInstitutions />
            )}
          </div>
        </main>
      </div>

      {/* Right Sidebar - Hidden on smaller screens */}
      <aside className="hidden xl:block fixed right-0 top-0 h-screen w-80 bg-white border-l border-gray-100 overflow-y-auto z-40">
        <div className="pt-16 p-5">
          <RightSidebar />
        </div>
      </aside>
    </div>
  )
}
