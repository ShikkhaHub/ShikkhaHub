import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock, X, Building2, Trash2 } from 'lucide-react'
import { getRecentlyViewed, clearRecentlyViewed, type RecentlyViewedItem } from '../lib/recentlyViewed'

export default function RecentlyViewed() {
  const [items, setItems] = useState<RecentlyViewedItem[]>([])
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    setItems(getRecentlyViewed())
  }, [])

  const handleClear = () => {
    clearRecentlyViewed()
    setItems([])
  }

  const handleDismiss = () => {
    setIsVisible(false)
  }

  if (!isVisible || items.length === 0) {
    return null
  }

  return (
    <section className="bg-white rounded-2xl shadow-elevated border border-gray-100 overflow-hidden">
      <div className="p-5 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-amber-50">
              <Clock className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Recently Viewed</h3>
              <p className="text-sm text-gray-500">Continue where you left off</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleClear}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="Clear history"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleDismiss}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="p-3">
        <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
          {items.map((item) => (
            <Link
              key={item.id}
              to={`/institutions/${item.slug}`}
              className="flex-shrink-0 group w-64 p-4 rounded-xl border border-gray-200 hover:border-indigo-300 hover:shadow-md transition-all duration-200 bg-white"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center flex-shrink-0">
                  <Building2 className="w-5 h-5 text-indigo-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 text-sm line-clamp-1 group-hover:text-indigo-600 transition-colors">
                    {item.short_name || item.name_en}
                  </h4>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {item.type_name}
                    {item.division_name && ` • ${item.division_name}`}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Viewed {new Date(item.viewed_at).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    })}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}
