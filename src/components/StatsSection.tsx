import { Building2, GraduationCap, Landmark, BookOpen, School } from 'lucide-react'

const stats = [
  {
    icon: Building2,
    value: '10,200+',
    label: 'Colleges',
    color: 'bg-blue-50 text-blue-600',
    iconBg: 'bg-blue-100',
  },
  {
    icon: GraduationCap,
    value: '183+',
    label: 'Universities',
    color: 'bg-green-50 text-green-600',
    iconBg: 'bg-green-100',
  },
  {
    icon: Landmark,
    value: '356+',
    label: 'Polytechnics',
    color: 'bg-orange-50 text-orange-600',
    iconBg: 'bg-orange-100',
  },
  {
    icon: BookOpen,
    value: '2,450+',
    label: 'Institutes',
    color: 'bg-pink-50 text-pink-600',
    iconBg: 'bg-pink-100',
  },
  {
    icon: School,
    value: '24,000+',
    label: 'Schools',
    color: 'bg-purple-50 text-purple-600',
    iconBg: 'bg-purple-100',
  },
]

export default function StatsSection() {
  return (
    <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="group relative bg-white rounded-2xl p-5 border border-gray-100 shadow-card hover:shadow-elevated transition-all duration-300 hover:-translate-y-1"
        >
          <div className="flex items-start gap-4">
            <div className={`w-12 h-12 rounded-xl ${stat.iconBg} ${stat.color} flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300`}>
              <stat.icon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 group-hover:text-indigo-600 transition-colors duration-300">
                {stat.value}
              </p>
              <p className="text-sm text-gray-500 mt-0.5">{stat.label}</p>
            </div>
          </div>
        </div>
      ))}
    </section>
  )
}
