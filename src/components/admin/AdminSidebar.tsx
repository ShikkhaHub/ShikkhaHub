import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '../../lib/utils';
import {
  LayoutDashboard,
  Building2,
  Users,
  BookOpen,
  GraduationCap,
  Award,
  FileText,
  BookMarked,
  Megaphone,
  MessageSquare,
  Bell,
  Mail,
  BarChart3,
  PieChart,
  ScrollText,
  Settings,
  Shield,
  ChevronDown,
  ChevronRight,
  Menu,
  X,
  School,
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    title: '',
    items: [
      { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
    ],
  },
  {
    title: 'MANAGEMENT',
    items: [
      { name: 'Institutions', href: '/admin/institutions', icon: Building2 },
      { name: 'Users', href: '/admin/users', icon: Users },
      { name: 'Courses', href: '/admin/courses', icon: BookOpen },
      { name: 'Admissions', href: '/admin/admissions', icon: GraduationCap },
      { name: 'Scholarships', href: '/admin/scholarships', icon: Award },
      { name: 'Applications', href: '/admin/applications', icon: FileText },
      { name: 'Study Materials', href: '/admin/materials', icon: BookMarked },
      { name: 'Banners & Announcements', href: '/admin/banners', icon: Megaphone },
    ],
  },
  {
    title: 'COMMUNICATION',
    items: [
      { name: 'Messages', href: '/admin/messages', icon: MessageSquare, badge: 3 },
      { name: 'Notifications', href: '/admin/notifications', icon: Bell, badge: 8 },
      { name: 'Contact Messages', href: '/admin/contacts', icon: Mail },
    ],
  },
  {
    title: 'REPORTS & ANALYTICS',
    items: [
      { name: 'Reports', href: '/admin/reports', icon: BarChart3 },
      { name: 'Analytics', href: '/admin/analytics', icon: PieChart },
      { name: 'System Logs', href: '/admin/logs', icon: ScrollText },
    ],
  },
  {
    title: 'SETTINGS',
    items: [
      { name: 'General Settings', href: '/admin/settings', icon: Settings },
      { name: 'Roles & Permissions', href: '/admin/roles', icon: Shield },
    ],
  },
];

interface AdminSidebarProps {
  isMobileOpen: boolean;
  onClose: () => void;
}

export default function AdminSidebar({ isMobileOpen, onClose }: AdminSidebarProps) {
  const location = useLocation();

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 h-screen w-64 bg-white border-r border-gray-200 overflow-y-auto z-50',
          'transition-transform duration-300 ease-in-out',
          'lg:translate-x-0',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center">
              <School className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
                ShikkhaHub
              </span>
              <span className="text-xs text-gray-500">Admin</span>
            </div>
          </div>
          
          {/* Mobile close button */}
          <button
            onClick={onClose}
            className="lg:hidden ml-auto p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-6">
          {navigation.map((section, sectionIndex) => (
            <div key={sectionIndex}>
              {section.title && (
                <h3 className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  {section.title}
                </h3>
              )}
              <ul className="space-y-1">
                {section.items.map((item) => {
                  const isActive = location.pathname === item.href ||
                    (item.href !== '/admin' && location.pathname.startsWith(item.href));
                  
                  return (
                    <li key={item.name}>
                      <NavLink
                        to={item.href}
                        onClick={() => onClose()}
                        className={cn(
                          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                          isActive
                            ? 'bg-indigo-50 text-indigo-700 border-l-2 border-indigo-600'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        )}
                      >
                        <item.icon className={cn(
                          'w-5 h-5 flex-shrink-0',
                          isActive ? 'text-indigo-600' : 'text-gray-400'
                        )} />
                        <span className="flex-1">{item.name}</span>
                        {item.badge && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-600 rounded-full">
                            {item.badge}
                          </span>
                        )}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-white">
          <p className="text-xs text-gray-400 text-center">
            © 2024 ShikkhaHub. All rights reserved.
          </p>
        </div>
      </aside>
    </>
  );
}
