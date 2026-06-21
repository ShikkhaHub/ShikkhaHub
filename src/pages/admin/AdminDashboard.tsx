import { useState } from 'react';
import AdminSidebar from '../../components/admin/AdminSidebar';
import AdminHeader from '../../components/admin/AdminHeader';
import {
  Building2,
  GraduationCap,
  BookOpen,
  FileText,
  Users,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  CheckCircle2,
  Server,
  Database,
  Activity,
  HardDrive,
  Bell,
  UserPlus,
  Award,
  MessageSquare,
  School,
} from 'lucide-react';
import { cn } from '../../lib/utils';

// Stats Card Component
interface StatCardProps {
  title: string;
  value: string;
  change: string;
  changeType: 'up' | 'down';
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
}

function StatCard({ title, value, change, changeType, icon: Icon, iconBg, iconColor }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className={cn('p-3 rounded-xl', iconBg)}>
          <Icon className={cn('w-6 h-6', iconColor)} />
        </div>
        <div className="flex items-center gap-1 text-sm">
          {changeType === 'up' ? (
            <>
              <TrendingUp className="w-4 h-4 text-emerald-500" />
              <span className="text-emerald-600 font-medium">{change}</span>
            </>
          ) : (
            <>
              <TrendingDown className="w-4 h-4 text-red-500" />
              <span className="text-red-600 font-medium">{change}</span>
            </>
          )}
          <span className="text-gray-400 text-xs">vs last 30 days</span>
        </div>
      </div>
      <div className="mt-4">
        <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
        <p className="text-sm text-gray-500 mt-1">{title}</p>
      </div>
    </div>
  );
}

// Chart Components
function ApplicationsChart() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-gray-900">Applications Overview</h3>
        <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 bg-gray-50 rounded-lg hover:bg-gray-100">
          Last 30 days
          <ChevronDown className="w-4 h-4" />
        </button>
      </div>
      
      <div className="h-64 relative">
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-indigo-500"></div>
            <span className="text-sm text-gray-600">Applications</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
            <span className="text-sm text-gray-600">Admissions</span>
          </div>
        </div>

        <svg className="w-full h-48" viewBox="0 0 500 150" preserveAspectRatio="none">
          {[0, 1, 2, 3, 4].map((i) => (
            <line key={i} x1="0" y1={i * 37.5} x2="500" y2={i * 37.5} stroke="#e5e7eb" strokeWidth="1" strokeDasharray="4" />
          ))}
          <polyline fill="none" stroke="#6366f1" strokeWidth="2" points="0,112.5 125,37.5 250,56.25 375,18.75 500,25" />
          <polyline fill="none" stroke="#10b981" strokeWidth="2" points="0,112.5 125,75 250,93.75 375,56.25 500,37.5" />
        </svg>

        <div className="flex justify-between text-xs text-gray-400 mt-2">
          <span>May 20</span>
          <span>May 27</span>
          <span>Jun 3</span>
          <span>Jun 10</span>
          <span>Jun 17</span>
        </div>

        <div className="absolute left-0 top-8 flex flex-col justify-between h-40 text-xs text-gray-400">
          <span>4K</span>
          <span>3K</span>
          <span>2K</span>
          <span>1K</span>
          <span>0</span>
        </div>
      </div>
    </div>
  );
}

function StatusDonutChart() {
  const data = [
    { label: 'Pending', value: 12540, percentage: 52.3, color: 'bg-blue-500' },
    { label: 'Reviewed', value: 6240, percentage: 26.0, color: 'bg-emerald-500' },
    { label: 'Accepted', value: 3240, percentage: 13.5, color: 'bg-amber-500' },
    { label: 'Rejected', value: 2980, percentage: 8.2, color: 'bg-red-500' },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Applications by Status</h3>
      
      <div className="flex items-center justify-center">
        <div className="relative w-40 h-40">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#3b82f6" strokeWidth="12" strokeDasharray="132 251" />
            <circle cx="50" cy="50" r="40" fill="none" stroke="#10b981" strokeWidth="12" strokeDasharray="66 251" strokeDashoffset="-132" />
            <circle cx="50" cy="50" r="40" fill="none" stroke="#f59e0b" strokeWidth="12" strokeDasharray="34 251" strokeDashoffset="-198" />
            <circle cx="50" cy="50" r="40" fill="none" stroke="#ef4444" strokeWidth="12" strokeDasharray="19 251" strokeDashoffset="-232" />
          </svg>
          
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold text-gray-900">24,000</span>
            <span className="text-xs text-gray-500">Total</span>
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {data.map((item) => (
          <div key={item.label} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className={cn('w-3 h-3 rounded-full', item.color)}></div>
              <span className="text-gray-600">{item.label}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-medium text-gray-900">{item.value.toLocaleString()}</span>
              <span className="text-gray-400 text-xs">({item.percentage}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TopInstitutionsTable() {
  const institutions = [
    { rank: 1, name: 'University of Dhaka', location: 'Dhaka, Dhaka', students: 18542, courses: 452, applications: 2450, status: 'verified' },
    { rank: 2, name: 'BUET', location: 'Dhaka, Dhaka', students: 12845, courses: 316, applications: 1890, status: 'verified' },
    { rank: 3, name: 'Dhaka College', location: 'Dhaka, Dhaka', students: 9876, courses: 210, applications: 1256, status: 'verified' },
    { rank: 4, name: 'North South University', location: 'Dhaka, Dhaka', students: 8753, courses: 245, applications: 1102, status: 'verified' },
    { rank: 5, name: 'BRAC University', location: 'Dhaka, Dhaka', students: 7654, courses: 198, applications: 987, status: 'pending' },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Top Institutions</h3>
        <button className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">View All →</button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="pb-3">#</th>
              <th className="pb-3">Institution</th>
              <th className="pb-3">Students</th>
              <th className="pb-3">Courses</th>
              <th className="pb-3">Applications</th>
              <th className="pb-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {institutions.map((inst) => (
              <tr key={inst.rank} className="hover:bg-gray-50">
                <td className="py-3 text-sm font-medium text-gray-900">{inst.rank}</td>
                <td className="py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs">
                      {inst.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{inst.name}</p>
                      <p className="text-xs text-gray-500">{inst.location}</p>
                    </div>
                  </div>
                </td>
                <td className="py-3 text-sm text-gray-900">{inst.students.toLocaleString()}</td>
                <td className="py-3 text-sm text-gray-900">{inst.courses}</td>
                <td className="py-3 text-sm text-gray-900">{inst.applications.toLocaleString()}</td>
                <td className="py-3">
                  <span className={cn(
                    'px-2 py-1 text-xs font-medium rounded-full',
                    inst.status === 'verified' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                  )}>
                    {inst.status === 'verified' ? 'Verified' : 'Pending'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DivisionStats() {
  const divisions = [
    { name: 'Dhaka Division', value: 8450, percentage: 35.2, color: 'bg-indigo-500' },
    { name: 'Chattogram Division', value: 5620, percentage: 23.4, color: 'bg-blue-500' },
    { name: 'Rajshahi Division', value: 3250, percentage: 13.5, color: 'bg-cyan-500' },
    { name: 'Khulna Division', value: 2850, percentage: 11.9, color: 'bg-teal-500' },
    { name: 'Barishal Division', value: 2100, percentage: 8.8, color: 'bg-emerald-500' },
    { name: 'Sylhet Division', value: 1730, percentage: 7.2, color: 'bg-green-500' },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Applications by Division</h3>
        <button className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">View All →</button>
      </div>

      <div className="space-y-4">
        {divisions.map((div) => (
          <div key={div.name}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-700">{div.name}</span>
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900">{div.value.toLocaleString()}</span>
                <span className="text-xs text-gray-500">({div.percentage}%)</span>
              </div>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className={cn('h-full rounded-full', div.color)} style={{ width: `${div.percentage}%` }}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RecentNotifications() {
  const notifications = [
    { icon: Building2, iconBg: 'bg-blue-100', iconColor: 'text-blue-600', text: 'New institution "Greenfield University" has been registered.', time: '2 min ago' },
    { icon: GraduationCap, iconBg: 'bg-emerald-100', iconColor: 'text-emerald-600', text: 'HSC Admission 2024-25 application deadline updated.', time: '15 min ago' },
    { icon: Award, iconBg: 'bg-amber-100', iconColor: 'text-amber-600', text: 'New scholarship "Merit Scholarship" has been published.', time: '1 hour ago' },
    { icon: UserPlus, iconBg: 'bg-indigo-100', iconColor: 'text-indigo-600', text: 'New user "radia.islam@example.com" has registered.', time: '2 hours ago' },
    { icon: MessageSquare, iconBg: 'bg-pink-100', iconColor: 'text-pink-600', text: 'New contact message received from "Rahim Uddin".', time: '3 hours ago' },
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Recent Notifications</h3>
        <button className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">View All →</button>
      </div>

      <div className="space-y-3">
        {notifications.map((notif, i) => (
          <div key={i} className="flex gap-3 p-2 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer">
            <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', notif.iconBg)}>
              <notif.icon className={cn('w-5 h-5', notif.iconColor)} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-700">{notif.text}</p>
              <p className="text-xs text-gray-400 mt-1">{notif.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SystemOverview() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">System Overview</h3>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Users className="w-4 h-4" />
            Total Users
          </div>
          <span className="font-medium text-gray-900">245,314</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Activity className="w-4 h-4 text-emerald-500" />
            Active Users
          </div>
          <span className="font-medium text-emerald-600">1,245</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Building2 className="w-4 h-4" />
            Total Institutions
          </div>
          <span className="font-medium text-gray-900">10,245</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <BookOpen className="w-4 h-4" />
            Total Courses
          </div>
          <span className="font-medium text-gray-900">2,450</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <FileText className="w-4 h-4" />
            Total Applications
          </div>
          <span className="font-medium text-gray-900">24,000</span>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Server className="w-4 h-4" />
              Server Status
            </div>
            <span className="px-2 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full">Operational</span>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <HardDrive className="w-4 h-4" />
            Last Backup
          </div>
          <span className="text-xs text-gray-500">June 19, 2024 02:00 AM</span>
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminSidebar isMobileOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />
      
      <div className="lg:ml-64">
        <AdminHeader onMenuClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} isMobileMenuOpen={isMobileMenuOpen} />
        
        <main className="p-4 lg:p-6">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-gray-500">Welcome back! Here's what's happening on ShikkhaHub.</p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
              <StatCard
                title="Total Institutions"
                value="10,245"
                change="12.5%"
                changeType="up"
                icon={Building2}
                iconBg="bg-indigo-100"
                iconColor="text-indigo-600"
              />
              <StatCard
                title="Total Students"
                value="183,542"
                change="18.7%"
                changeType="up"
                icon={GraduationCap}
                iconBg="bg-emerald-100"
                iconColor="text-emerald-600"
              />
              <StatCard
                title="Total Courses"
                value="2,450"
                change="8.4%"
                changeType="up"
                icon={BookOpen}
                iconBg="bg-amber-100"
                iconColor="text-amber-600"
              />
              <StatCard
                title="Total Applications"
                value="24,000"
                change="15.3%"
                changeType="up"
                icon={FileText}
                iconBg="bg-pink-100"
                iconColor="text-pink-600"
              />
              <StatCard
                title="Active Users"
                value="1,245"
                change="10.1%"
                changeType="up"
                icon={Users}
                iconBg="bg-blue-100"
                iconColor="text-blue-600"
              />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              <div className="lg:col-span-2">
                <ApplicationsChart />
              </div>
              <div>
                <StatusDonutChart />
              </div>
            </div>

            {/* Tables Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              <div className="lg:col-span-2">
                <TopInstitutionsTable />
              </div>
              <div>
                <DivisionStats />
              </div>
            </div>

            {/* Bottom Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <RecentNotifications />
              </div>
              <div>
                <SystemOverview />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
