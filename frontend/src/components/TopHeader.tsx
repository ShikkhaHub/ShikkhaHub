import { Search, Bell, ChevronDown, Menu, X } from 'lucide-react'
import { useState } from 'react'

interface TopHeaderProps {
  onMenuClick?: () => void
  isMobileMenuOpen?: boolean
}

export default function TopHeader({ onMenuClick, isMobileMenuOpen }: TopHeaderProps) {
  const [isSearchFocused, setIsSearchFocused] = useState(false)

  return (
    <header className="sticky top-0 z-40 bg-background/80 backdrop-blur-xl border-b border-gray-100">
      <div className="flex items-center justify-between h-16 px-4 md:px-6">
        {/* Mobile Menu Button */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-xl hover:bg-gray-100 transition-colors duration-200 mr-2"
          aria-label="Toggle menu"
        >
          {isMobileMenuOpen ? (
            <X className="w-5 h-5 text-gray-600" />
          ) : (
            <Menu className="w-5 h-5 text-gray-600" />
          )}
        </button>

        {/* Search Bar - Centered */}
        <div className={`flex-1 max-w-2xl mx-auto transition-all duration-300 ${isSearchFocused ? 'scale-105' : ''}`}>
          <div className="relative">
            <Search className="absolute left-3 md:left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search colleges, courses..."
              className="w-full h-10 md:h-11 pl-9 md:pl-11 pr-4 md:pr-20 bg-white border border-gray-200 rounded-xl text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all duration-200"
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setIsSearchFocused(false)}
            />
            <div className="hidden md:flex absolute right-3 top-1/2 -translate-y-1/2 items-center gap-1 text-xs text-gray-400">
              <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500 font-medium">Ctrl</kbd>
              <span>K</span>
            </div>
          </div>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-2 md:gap-3 ml-4 md:ml-6">
          {/* Notification */}
          <button className="relative p-2 md:p-2.5 rounded-xl hover:bg-gray-100 transition-colors duration-200">
            <Bell className="w-5 h-5 text-gray-600" />
            <span className="absolute top-1 right-1 md:top-1.5 md:right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white" />
          </button>

          {/* User Profile - Hidden on smallest screens */}
          <button className="hidden sm:flex items-center gap-2 md:gap-3 pl-2 md:pl-3 pr-2 py-1.5 rounded-xl hover:bg-gray-100 transition-all duration-200">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center text-white text-sm font-semibold">
              R
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-medium text-gray-900">Hi, Rafiul!</p>
              <p className="text-xs text-gray-500">Student</p>
            </div>
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>
    </header>
  )
}
