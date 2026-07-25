import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { 
  Building2, 
  MapPin, 
  Phone, 
  Globe, 
  Mail, 
  Calendar, 
  GraduationCap,
  Award,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
  ExternalLink,
  BookOpen,
  Users,
  School,
  Scale
} from 'lucide-react'
import { getInstitutionBySlug, type Institution } from '../lib/api'
import CompareButton from '../components/CompareButton'
import { getComparisonCount } from '../lib/compareStore'
import { addToRecentlyViewed } from '../lib/recentlyViewed'
import { InstitutionDetailSkeleton } from '../components/Skeleton'
import SEO, { InstitutionSEO } from '../components/SEO'

export default function InstitutionDetail() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [institution, setInstitution] = useState<Institution | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [compareCount, setCompareCount] = useState(0)

  useEffect(() => {
    if (!slug) return

    const fetchInstitution = async () => {
      try {
        setLoading(true)
        const data = await getInstitutionBySlug(slug)
        setInstitution(data)
        
        // Add to recently viewed
        addToRecentlyViewed({
          id: data.id,
          slug: data.slug,
          name_en: data.name_en,
          name_bn: data.name_bn,
          type_name: data.type_name,
          short_name: data.short_name,
          division_name: data.division_name
        })
      } catch (err) {
        setError('Failed to load institution details')
      } finally {
        setLoading(false)
      }
    }

    fetchInstitution()
    setCompareCount(getComparisonCount())
  }, [slug])

  if (loading) {
    return <InstitutionDetailSkeleton />
  }

  if (error || !institution) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <h2 className="text-lg font-medium text-gray-900 mb-1">
            {error || 'Institution not found'}
          </h2>
          <button
            onClick={() => navigate('/')}
            className="mt-4 text-indigo-600 hover:text-indigo-700 font-medium"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <SEO {...(institution ? InstitutionSEO(institution) : {})} />
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back to Search</span>
            </button>
            {compareCount > 0 && (
              <Link
                to="/compare"
                className="flex items-center gap-2 px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium hover:bg-indigo-200 transition-colors"
              >
                <Scale className="w-4 h-4" />
                Compare ({compareCount})
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Institution Header */}
        <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-8 mb-6">
          <div className="flex items-start gap-6">
            {/* Icon */}
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center flex-shrink-0">
              <GraduationCap className="w-10 h-10 text-indigo-600" />
            </div>

            <div className="flex-1">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">
                    {institution.name_en}
                  </h1>
                  {institution.name_bn && (
                    <p className="text-xl text-gray-600 mt-1">
                      {institution.name_bn}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {institution.verification_status === 'verified' && (
                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-emerald-100 text-emerald-700">
                      <CheckCircle className="w-4 h-4" />
                      Verified
                    </span>
                  )}
                  {institution.is_featured && (
                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-700">
                      <Award className="w-4 h-4" />
                      Featured
                    </span>
                  )}
                  <CompareButton 
                    institution={institution}
                    size="md"
                    variant="button"
                    onToggle={() => setCompareCount(getComparisonCount())}
                  />
                </div>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-2 mt-4">
                {institution.type_name && (
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-100 text-blue-700">
                    <School className="w-4 h-4" />
                    {institution.type_name}
                  </span>
                )}
                {institution.established_year && (
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium bg-green-100 text-green-700">
                    <Calendar className="w-4 h-4" />
                    Est. {institution.established_year}
                  </span>
                )}
                <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700">
                  <Users className="w-4 h-4" />
                  {institution.view_count} views
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Overview Section */}
            <section className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-indigo-600" />
                Overview
              </h2>
              <div className="space-y-4">
                {institution.address && (
                  <div className="flex items-start gap-3">
                    <MapPin className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-gray-700">Address</p>
                      <p className="text-gray-600">{institution.address}</p>
                      {(institution.division_name || institution.district_name) && (
                        <p className="text-sm text-gray-500 mt-1">
                          {[institution.division_name, institution.district_name, institution.upazila_name]
                            .filter(Boolean)
                            .join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {institution.phone && (
                    <div className="flex items-center gap-3">
                      <Phone className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Phone</p>
                        <a 
                          href={`tel:${institution.phone}`}
                          className="text-gray-700 hover:text-indigo-600"
                        >
                          {institution.phone}
                        </a>
                      </div>
                    </div>
                  )}

                  {institution.email && (
                    <div className="flex items-center gap-3">
                      <Mail className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Email</p>
                        <a 
                          href={`mailto:${institution.email}`}
                          className="text-gray-700 hover:text-indigo-600 truncate max-w-[200px] inline-block"
                        >
                          {institution.email}
                        </a>
                      </div>
                    </div>
                  )}

                  {institution.website && (
                    <div className="flex items-center gap-3">
                      <Globe className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-500">Website</p>
                        <a 
                          href={institution.website.startsWith('http') ? institution.website : `https://${institution.website}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                        >
                          Visit Website
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Courses & Subjects Section */}
            <section className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-600" />
                Courses & Programs
              </h2>
              <p className="text-gray-500">
                Course information will be available soon. We're actively collecting data on programs offered by this institution.
              </p>
            </section>

            {/* Admission Requirements */}
            <section className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Award className="w-5 h-5 text-indigo-600" />
                Admission Requirements
              </h2>
              <p className="text-gray-500">
                Admission requirements and application process details will be added soon.
              </p>
            </section>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Info */}
            <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Quick Information</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Data Source</span>
                  <span className="font-medium text-gray-700">{institution.data_source || 'Manual Entry'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Last Updated</span>
                  <span className="font-medium text-gray-700">
                    {new Date(institution.last_updated).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Status</span>
                  <span className={`font-medium ${
                    institution.verification_status === 'verified' 
                      ? 'text-emerald-600' 
                      : 'text-amber-600'
                  }`}>
                    {institution.verification_status === 'verified' ? 'Verified' : 'Pending Verification'}
                  </span>
                </div>
              </div>
            </div>

            {/* Location Map Placeholder */}
            <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                Location
              </h3>
              <div className="aspect-video bg-gray-100 rounded-xl flex items-center justify-center">
                <p className="text-gray-400 text-sm">Map integration coming soon</p>
              </div>
            </div>

            {/* Affiliations */}
            <div className="bg-white rounded-2xl shadow-elevated border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Affiliations</h3>
              <div className="space-y-2">
                <p className="text-gray-500 text-sm">Affiliation information will be added soon.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
