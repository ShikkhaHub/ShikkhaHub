import { useState } from 'react'
import { Search, ChevronDown, Loader2 } from 'lucide-react'
import { searchInstitutions, type Institution, type SearchFilters } from '../lib/api'

const tabs = ['All', 'College', 'University', 'Polytechnic', 'School', 'Institute']


interface HeroSectionProps {
  onSearchResults?: (results: Institution[], query: string) => void
  onSearchStart?: () => void
}

export default function HeroSection({ onSearchResults, onSearchStart }: HeroSectionProps) {
  const [activeTab, setActiveTab] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDivision, setSelectedDivision] = useState('')
  const [isSearching, setIsSearching] = useState(false)

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    setIsSearching(true)
    onSearchStart?.()
    try {
      const filters: SearchFilters = {
        q: searchQuery,
        verification_status: 'pending',
        page: 1,
        page_size: 20
      }

      if (activeTab !== 'All') {
        // Map tab to institution type
        const typeMap: Record<string, number> = {
          'University': 1,
          'College': 2,
          'Polytechnic': 3,
          'School': 4,
          'Institute': 5
        }
        if (typeMap[activeTab]) {
          filters.type_id = typeMap[activeTab]
        }
      }

      const results = await searchInstitutions(filters)
      onSearchResults?.(results.items, searchQuery)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <section className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-slate-50 via-white to-blue-50 border border-gray-100">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100/50 via-transparent to-transparent" />
      
      <div className="relative flex flex-col lg:flex-row">
        {/* Left Content */}
        <div className="flex-1 p-8 lg:p-10">
          <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 leading-tight mb-4">
            Your Future,
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">
              Our Guidance
            </span>
          </h1>
          <p className="text-lg text-gray-600 mb-8 max-w-md">
            All education information in Bangladesh at your fingertips.
          </p>

          {/* Search Filter Card */}
          <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-5">
            {/* Tabs */}
            <div className="flex flex-wrap gap-2 mb-4">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                    activeTab === tab
                      ? 'bg-indigo-600 text-white shadow-glow'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative mb-4">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search for institutions, courses..."
                className="w-full h-12 pl-11 pr-4 bg-gray-50 border border-gray-200 rounded-xl text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all duration-200"
              />
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div className="relative">
                <select 
                  value={selectedDivision}
                  onChange={(e) => setSelectedDivision(e.target.value)}
                  className="w-full h-11 pl-4 pr-10 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer"
                >
                  <option value="">All Divisions</option>
                  <option value="dhaka">Dhaka</option>
                  <option value="chittagong">Chittagong</option>
                  <option value="rajshahi">Rajshahi</option>
                  <option value="khulna">Khulna</option>
                  <option value="barisal">Barisal</option>
                  <option value="sylhet">Sylhet</option>
                  <option value="rangpur">Rangpur</option>
                  <option value="mymensingh">Mymensingh</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>

              <div className="relative">
                <select className="w-full h-11 pl-4 pr-10 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer">
                  <option>All Districts</option>
                  <option>Dhaka</option>
                  <option>Gazipur</option>
                  <option>Narayanganj</option>
                  <option>Tangail</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>

              <div className="relative">
                <select className="w-full h-11 pl-4 pr-10 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-700 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 cursor-pointer">
                  <option>All Types</option>
                  <option>Public</option>
                  <option>Private</option>
                  <option>Government</option>
                  <option>Autonomous</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>

              <button 
                onClick={handleSearch}
                disabled={isSearching}
                className="h-11 px-6 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-colors duration-200 flex items-center justify-center gap-2 shadow-glow disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSearching ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                {isSearching ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Image */}
        <div className="hidden lg:block w-[420px] relative">
          <div className="absolute inset-0 bg-gradient-to-l from-transparent via-white/20 to-white z-10" />
          <img
            src="https://images.unsplash.com/photo-1562774053-701939374585?w=600&h=800&fit=crop"
            alt="University Building"
            className="w-full h-full object-cover"
          />
        </div>
      </div>
    </section>
  )
}
