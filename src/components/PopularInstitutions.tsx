import { Link } from 'react-router-dom'
import { Star, BadgeCheck, ChevronRight } from 'lucide-react'

const institutions = [
  {
    id: 1,
    slug: 'dhaka-university',
    name: 'University of Dhaka',
    location: 'Dhaka, Dhaka',
    type: 'Public University',
    rating: 4.8,
    reviews: '2.1K reviews',
    image: 'https://images.unsplash.com/photo-1592280771190-3e2e4d571952?w=400&h=300&fit=crop',
    verified: true,
  },
  {
    id: 2,
    slug: 'buet',
    name: 'BUET',
    location: 'Dhaka, Dhaka',
    type: 'Public University',
    rating: 4.9,
    reviews: '1.8K reviews',
    image: 'https://images.unsplash.com/photo-1581094794329-c8112a89af12?w=400&h=300&fit=crop',
    verified: true,
  },
  {
    id: 3,
    slug: 'dhaka-college',
    name: 'Dhaka College',
    location: 'Dhaka, Dhaka',
    type: 'Govt. College',
    rating: 4.5,
    reviews: '856 reviews',
    image: 'https://images.unsplash.com/photo-1564981797816-1043664bf78d?w=400&h=300&fit=crop',
    verified: true,
  },
  {
    id: 4,
    slug: 'north-south-university',
    name: 'North South University',
    location: 'Dhaka, Dhaka',
    type: 'Private University',
    rating: 4.6,
    reviews: '1.2K reviews',
    image: 'https://images.unsplash.com/photo-1562774053-701939374585?w=400&h=300&fit=crop',
    verified: true,
  },
]

export default function PopularInstitutions() {
  return (
    <section>
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-semibold text-gray-900">Popular Institutions</h2>
        <Link
          to="/institutions"
          className="flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors duration-200"
        >
          View All
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {institutions.map((institution) => (
          <Link
            key={institution.id}
            to={`/institutions/${institution.slug}`}
            className="group block bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-card hover:shadow-elevated transition-all duration-300 hover:-translate-y-1"
          >
            {/* Image */}
            <div className="relative h-36 overflow-hidden">
              <img
                src={institution.image}
                alt={institution.name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
              
              {/* Verified Badge */}
              {institution.verified && (
                <div className="absolute top-3 right-3 flex items-center gap-1 px-2 py-1 bg-white/95 backdrop-blur-sm rounded-full">
                  <BadgeCheck className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-xs font-medium text-gray-700">Verified</span>
                </div>
              )}
            </div>

            {/* Content */}
            <div className="p-4">
              <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors duration-200">
                {institution.name}
              </h3>
              <p className="text-xs text-gray-500 mb-2">{institution.location}</p>
              
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 text-xs font-medium">
                  {institution.type}
                </span>
                
                <div className="flex items-center gap-1">
                  <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                  <span className="text-xs font-medium text-gray-700">{institution.rating}</span>
                  <span className="text-xs text-gray-400">({institution.reviews})</span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}
