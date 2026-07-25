import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Building2, 
  BookOpen, 
  FileText, 
  GraduationCap, 
  Library, 
  Briefcase, 
  Users, 
  Sparkles,
  Crown,
  X
} from 'lucide-react'

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/', active: true },
  { icon: Building2, label: 'Institutions', path: '/institutions', active: false },
  { icon: BookOpen, label: 'Courses', path: '#', active: false },
  { icon: FileText, label: 'Admission Guide', path: '#', active: false },
  { icon: GraduationCap, label: 'Scholarships', path: '#', active: false },
  { icon: Library, label: 'Study Materials', path: '#', active: false },
  { icon: Briefcase, label: 'Career & Jobs', path: '#', active: false },
  { icon: Users, label: 'Community', path: '#', active: false },
  { icon: Sparkles, label: 'AI Assistant', path: '#', active: false },
]

const quickLinks = [
  'HSC Corner',
  'University Corner',
  'BCS Corner',
  'Medical Corner',
  'Engineering Corner',
]

interface LeftSidebarProps {
  isMobileOpen?: boolean
  onClose?: () => void
}

export default function LeftSidebar({ isMobileOpen = false, onClose }: LeftSidebarProps) {
  const location = useLocation()
  
  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      
      {/* Sidebar - Desktop: fixed, Mobile: slide-out */}
      <aside 
        className={`fixed left-0 top-0 h-screen w-64 bg-white border-r border-gray-100 flex flex-col z-50 transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}>
        {/* Mobile Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl hover:bg-gray-100 transition-colors lg:hidden"
          aria-label="Close menu"
        >
          <X className="w-5 h-5 text-gray-600" />
        </button>
      {/* Logo */}
      <Link to="/" className="px-6 py-5 flex items-center gap-3 lg:mt-0 mt-2" onClick={onClose}>
        <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
          <GraduationCap className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-semibold text-gray-900">ShikkhaHub</span>
      </Link>

      {/* Main Navigation */}
      <nav className="flex-1 px-4 py-4">
        <ul className="space-y-1">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path || 
              (item.path !== '/' && location.pathname.startsWith(item.path))
            
            return (
              <li key={item.label}>
                <Link
                  to={item.path}
                  onClick={onClose}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-600'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <item.icon className={`w-5 h-5 ${isActive ? 'text-indigo-600' : 'text-gray-500'}`} />
                  {item.label}
                </Link>
              </li>
            )
          })}
        </ul>

        {/* Quick Links */}
        <div className="mt-8">
          <p className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Quick Links
          </p>
          <ul className="space-y-1">
            {quickLinks.map((link) => (
              <li key={link}>
                <a
                  href="#"
                  className="flex items-center gap-3 px-4 py-2 rounded-xl text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-all duration-200"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
                  {link}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      {/* Go Premium Card */}
      <div className="p-4 mt-auto">
        <div className="relative overflow-hidden rounded-2xl p-5 bg-gradient-to-br from-indigo-500 via-violet-500 to-purple-600">
          <div className="absolute inset-0 bg-white/10" />
          <div className="absolute -top-10 -right-10 w-24 h-24 bg-white/20 rounded-full blur-2xl" />
          
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-2">
              <Crown className="w-5 h-5 text-yellow-300" />
              <span className="text-sm font-semibold text-white">Go Premium</span>
            </div>
            <p className="text-xs text-indigo-100 mb-4 leading-relaxed">
              Unlock unlimited access to all features and premium content.
            </p>
            <button className="w-full py-2.5 px-4 bg-white text-indigo-600 text-sm font-semibold rounded-xl hover:bg-indigo-50 transition-colors duration-200 shadow-soft">
              Upgrade Now
            </button>
          </div>
        </div>
      </div>
    </aside>
    </>
  )
}
