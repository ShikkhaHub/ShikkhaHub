import { useState } from 'react';
import { Search, Bell, ChevronDown, Menu, User, Settings, LogOut } from 'lucide-react';
import { cn } from '../../lib/utils';

interface AdminHeaderProps {
  onMenuClick: () => void;
  isMobileMenuOpen: boolean;
}

export default function AdminHeader({ onMenuClick }: AdminHeaderProps) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);

  return (
    <header className="h-16 bg-white border-b border-gray-200 sticky top-0 z-30">
      <div className="h-full px-4 lg:px-6 flex items-center justify-between gap-4">
        {/* Left: Menu button + Search */}
        <div className="flex items-center gap-4 flex-1">
          {/* Mobile menu button */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Search */}
          <div className="relative flex-1 max-w-xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search for colleges, users, courses..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 hidden sm:inline-flex items-center gap-1 px-2 py-0.5 text-xs text-gray-400 bg-white border border-gray-200 rounded">
              <span>⌘</span><span>K</span>
            </kbd>
          </div>
        </div>

        {/* Right: Notifications + Profile */}
        <div className="flex items-center gap-3">
          {/* Date Range Selector */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
            <span>May 20 - June 19, 2024</span>
            <ChevronDown className="w-4 h-4" />
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
              className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
            </button>

            {/* Notifications Dropdown */}
            {isNotificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">
                <div className="px-4 py-2 border-b border-gray-100">
                  <h3 className="font-semibold text-gray-900">Notifications</h3>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {[
                    { icon: '🔔', text: 'New institution "Greenfield University" has been registered', time: '2 min ago' },
                    { icon: '📋', text: 'HSC Admission 2024-25 application deadline updated', time: '15 min ago' },
                    { icon: '🎓', text: 'New scholarship "Merit Scholarship" has been published', time: '1 hour ago' },
                  ].map((notif, i) => (
                    <div key={i} className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-50 last:border-0">
                      <div className="flex gap-3">
                        <span className="text-lg">{notif.icon}</span>
                        <div>
                          <p className="text-sm text-gray-700">{notif.text}</p>
                          <p className="text-xs text-gray-400 mt-1">{notif.time}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="px-4 py-2 border-t border-gray-100">
                  <button className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                    View all notifications →
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Profile */}
          <div className="relative">
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="flex items-center gap-3 pl-2 pr-3 py-1.5 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <img
                src="https://ui-avatars.com/api/?name=Rafidul+Islam&background=6366f1&color=fff"
                alt="Admin"
                className="w-8 h-8 rounded-full"
              />
              <div className="hidden md:flex flex-col items-start">
                <span className="text-sm font-semibold text-gray-900">Hi, Rafidul</span>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  Super Admin
                  <span className="text-amber-500">👑</span>
                </span>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>

            {/* Profile Dropdown */}
            {isProfileOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="font-semibold text-gray-900">Rafidul Islam</p>
                  <p className="text-xs text-gray-500">rafidul@shikkhahub.com</p>
                </div>
                <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                  <User className="w-4 h-4" />
                  Profile
                </button>
                <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">
                  <Settings className="w-4 h-4" />
                  Settings
                </button>
                <div className="border-t border-gray-100 mt-1 pt-1">
                  <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                    <LogOut className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
