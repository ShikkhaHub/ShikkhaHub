import { Sparkles, ChevronRight, MessageCircle, FileText, RefreshCw, TrendingUp } from 'lucide-react'

const aiPrompts = [
  'Best engineering colleges in Dhaka',
  'HSC admission process',
  'Career options after HSC',
]

const updates = [
  {
    id: 1,
    tag: 'New',
    tagColor: 'bg-emerald-100 text-emerald-700',
    title: 'HSC Admission 2024-25 Application has started',
    time: '2 hours ago',
    icon: FileText,
  },
  {
    id: 2,
    tag: 'Notice',
    tagColor: 'bg-blue-100 text-blue-700',
    title: 'DU Admission Circular Published',
    time: '5 hours ago',
    icon: FileText,
  },
  {
    id: 3,
    tag: 'Update',
    tagColor: 'bg-amber-100 text-amber-700',
    title: 'BUET Admission Test Date Announced',
    time: '1 day ago',
    icon: RefreshCw,
  },
]

const trendingCourses = [
  { name: 'Computer Science', students: '12,540 students', rank: 1 },
  { name: 'Electrical Engineering', students: '8,230 students', rank: 2 },
  { name: 'MBBS', students: '6,750 students', rank: 3 },
  { name: 'Business Administration', students: '5,480 students', rank: 4 },
]

export default function RightSidebar() {
  return (
    <aside className="space-y-5">
      {/* AI Study Assistant Card */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-card">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <h3 className="font-semibold text-gray-900">AI Study Assistant</h3>
        </div>

        {/* Chat Preview */}
        <div className="bg-gray-50 rounded-xl p-4 mb-4">
          <div className="flex items-start gap-3 mb-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center flex-shrink-0">
              <MessageCircle className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Hi Rafiul! 👋</p>
              <p className="text-xs text-gray-500 mt-0.5">How can I help you today?</p>
            </div>
          </div>
        </div>

        {/* Suggested Prompts */}
        <div className="space-y-2 mb-4">
          {aiPrompts.map((prompt) => (
            <button
              key={prompt}
              className="w-full flex items-center justify-between px-3 py-2.5 bg-white border border-gray-100 rounded-xl text-sm text-gray-700 hover:bg-gray-50 hover:border-gray-200 transition-all duration-200 group"
            >
              <span className="truncate pr-2">{prompt}</span>
              <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0 group-hover:text-gray-600" />
            </button>
          ))}
        </div>

        {/* CTA Button */}
        <button className="w-full py-2.5 px-4 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors duration-200 flex items-center justify-center gap-2 shadow-glow">
          <Sparkles className="w-4 h-4" />
          Ask Anything
        </button>
      </div>

      {/* Important Updates */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Important Updates</h3>
          <a href="#" className="text-xs font-medium text-indigo-600 hover:text-indigo-700">
            View All
          </a>
        </div>

        <div className="space-y-3">
          {updates.map((update) => (
            <a
              key={update.id}
              href="#"
              className="flex items-start gap-3 group hover:bg-gray-50 -mx-2 px-2 py-2 rounded-xl transition-colors duration-200"
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${update.tagColor.replace('text-', 'bg-').replace('700', '100')} ${update.tagColor.split(' ')[1]}`}>
                <update.icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${update.tagColor}`}>
                    {update.tag}
                  </span>
                </div>
                <p className="text-sm text-gray-900 leading-snug group-hover:text-indigo-600 transition-colors duration-200">
                  {update.title}
                </p>
                <p className="text-xs text-gray-400 mt-1">{update.time}</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300 flex-shrink-0 mt-3 group-hover:text-gray-400" />
            </a>
          ))}
        </div>
      </div>

      {/* Trending Courses */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">Trending Courses</h3>
          <a href="#" className="text-xs font-medium text-indigo-600 hover:text-indigo-700">
            View All
          </a>
        </div>

        <div className="space-y-3">
          {trendingCourses.map((course) => (
            <a
              key={course.name}
              href="#"
              className="flex items-center gap-3 group hover:bg-gray-50 -mx-2 px-2 py-2 rounded-xl transition-colors duration-200"
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-semibold text-sm ${
                course.rank === 1 ? 'bg-amber-100 text-amber-700' :
                course.rank === 2 ? 'bg-gray-200 text-gray-700' :
                course.rank === 3 ? 'bg-orange-100 text-orange-700' :
                'bg-gray-100 text-gray-600'
              }`}>
                {course.rank}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors duration-200 truncate">
                  {course.name}
                </p>
                <div className="flex items-center gap-1 mt-0.5">
                  <TrendingUp className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-gray-500">{course.students}</span>
                </div>
              </div>
            </a>
          ))}
        </div>
      </div>
    </aside>
  )
}
