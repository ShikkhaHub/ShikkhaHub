import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  GraduationCap,
  Sparkles,
  TrendingUp,
  Clock,
  Target,
  BookOpen,
  Award,
  Globe2,
  ShieldCheck,
  ShieldAlert,
  RefreshCw,
  ChevronRight,
  Briefcase,
  Heart,
  AlertTriangle,
  Building2,
} from 'lucide-react'
import { studentAnalyticsApi } from '../api'
import type {
  Student360,
  StudentProfile,
  Recommendations,
  AIStudentProfile,
} from '../types'

const learningStyleColors: Record<string, string> = {
  visual: 'bg-indigo-50 text-indigo-700',
  auditory: 'bg-amber-50 text-amber-700',
  reading: 'bg-sky-50 text-sky-700',
  kinesthetic: 'bg-emerald-50 text-emerald-700',
}

const riskColors: Record<string, string> = {
  low: 'text-emerald-600 bg-emerald-50',
  medium: 'text-amber-600 bg-amber-50',
  high: 'text-red-600 bg-red-50',
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType
  label: string
  value: string | number
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-center gap-2 text-gray-400 mb-2">
        <Icon className="w-4 h-4" />
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

function RecommendationCard({
  institution_id,
  name_en,
  score,
  tier,
  match_reasons,
  type,
}: {
  institution_id: number
  name_en: string
  score: number
  tier: string
  match_reasons: string[]
  type?: string
}) {
  const tierColors: Record<string, string> = {
    best: 'bg-indigo-50 text-indigo-700',
    safety: 'bg-emerald-50 text-emerald-700',
    competitive: 'bg-amber-50 text-amber-700',
    dream: 'bg-violet-50 text-violet-700',
  }
  const reasons = match_reasons || []
  return (
    <div key={institution_id} className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900 truncate">{name_en}</p>
          {type && <p className="text-xs text-gray-400 mt-0.5">{type}</p>}
          {reasons.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {reasons.map((r) => (
                <span
                  key={r}
                  className="px-2 py-0.5 text-[11px] bg-gray-50 text-gray-600 rounded-full"
                >
                  {r}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span
            className={`px-2 py-0.5 text-[11px] font-semibold rounded-full capitalize ${
              tierColors[tier] || 'bg-gray-50 text-gray-600'
            }`}
          >
            {tier}
          </span>
          <span className="text-sm font-bold text-indigo-600">{score}%</span>
        </div>
      </div>
    </div>
  )
}

export default function StudentDashboard() {
  const [data, setData] = useState<Student360 | null>(null)
  const [recommendations, setRecommendations] = useState<Recommendations | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showProfileForm, setShowProfileForm] = useState(false)
  const [saved, setSaved] = useState(false)
  const [profileForm, setProfileForm] = useState<Partial<StudentProfile>>({})

  const load = async () => {
    try {
      setLoading(true)
      const [dash, recs] = await Promise.all([
        studentAnalyticsApi.getStudent360(),
        studentAnalyticsApi.getRecommendations(),
      ])
      setData(dash)
      setRecommendations(recs)
      setProfileForm(dash.profile)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const handleRefreshAIProfile = async () => {
    setRefreshing(true)
    try {
      await studentAnalyticsApi.getAIProfile(true)
      await load()
    } finally {
      setRefreshing(false)
    }
  }

  const handleToggleConsent = async (granted: boolean) => {
    await studentAnalyticsApi.setConsent(granted)
    await load()
  }

  const handleSaveProfile = async () => {
    await studentAnalyticsApi.updateProfile(profileForm)
    setShowProfileForm(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
    await load()
  }

  if (loading && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex items-center gap-3 text-gray-500">
          <RefreshCw className="w-5 h-5 animate-spin" />
          Loading your student analytics...
        </div>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="bg-white rounded-2xl shadow-card p-8 max-w-md text-center">
          <ShieldAlert className="w-12 h-12 text-amber-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Unable to load analytics</h2>
          <p className="text-sm text-gray-500 mb-4">{error}</p>
          <button
            onClick={() => load()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const profile = data?.profile
  const ai: AIStudentProfile = data?.ai_profile || {}
  const learning = data?.learning

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-br from-indigo-600 via-violet-600 to-purple-700 text-white">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-indigo-200 text-sm font-medium mb-1">
                <Sparkles className="w-4 h-4" />
                My Student Analytics
              </div>
              <h1 className="text-2xl font-bold">
                {profile?.full_name || 'Student'} Dashboard
              </h1>
              <p className="text-indigo-100 text-sm mt-1">
                {profile?.current_level || 'Learner'}
                {profile?.current_institution ? ` at ${profile.current_institution}` : ''}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="bg-white/10 backdrop-blur rounded-xl px-4 py-3 text-center">
                <p className="text-2xl font-bold">
                  {ai.recommendation_score ?? 0}%
                </p>
                <p className="text-xs text-indigo-100">Recommendation</p>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-xl px-4 py-3 text-center">
                <p className="text-2xl font-bold capitalize">{ai.risk_score || '—'}</p>
                <p className="text-xs text-indigo-100">Risk Score</p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 mt-4">
            <button
              onClick={handleRefreshAIProfile}
              disabled={refreshing}
              className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh AI Profile
            </button>
            <button
              onClick={() => setShowProfileForm((v) => !v)}
              className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
            >
              {showProfileForm ? 'Close Editor' : 'Edit Profile'}
            </button>
            {profile?.analytics_consent ? (
              <button
                onClick={() => handleToggleConsent(false)}
                className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
              >
                <ShieldCheck className="w-4 h-4" /> Analytics On
              </button>
            ) : (
              <button
                onClick={() => handleToggleConsent(true)}
                className="flex items-center gap-2 px-3 py-1.5 bg-emerald-400/20 hover:bg-emerald-400/30 rounded-lg text-sm transition-colors"
              >
                <ShieldAlert className="w-4 h-4" /> Enable Analytics
              </button>
            )}
          </div>
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {saved && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-xl text-sm">
            Profile saved successfully.
          </div>
        )}

        {/* Profile editor */}
        {showProfileForm && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-indigo-600" /> Edit My Profile
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                ['full_name', 'Full Name'],
                ['age', 'Age'],
                ['gender', 'Gender'],
                ['current_level', 'Current Level (SSC/HSC/University)'],
                ['education_board', 'Education Board'],
                ['current_institution', 'Current Institution'],
                ['department', 'Department'],
                ['expected_graduation', 'Expected Graduation Year'],
                ['division', 'Division'],
                ['district', 'District'],
                ['upazila', 'Upazila'],
                ['dream_career', 'Dream Career'],
                ['preferred_university', 'Preferred University'],
                ['preferred_subject', 'Preferred Subject'],
              ].map(([key, label]) => (
                <div key={key}>
                  <label className="text-xs font-medium text-gray-500">{label}</label>
                  <input
                    type="text"
                    value={(profileForm[key as keyof StudentProfile] as string) || ''}
                    onChange={(e) =>
                      setProfileForm((f) => ({ ...f, [key]: e.target.value }))
                    }
                    className="mt-1 w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={!!profileForm.scholarship_interest}
                  onChange={(e) =>
                    setProfileForm((f) => ({ ...f, scholarship_interest: e.target.checked }))
                  }
                  className="rounded border-gray-300"
                />
                Interested in scholarships
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={!!profileForm.abroad_interest}
                  onChange={(e) =>
                    setProfileForm((f) => ({ ...f, abroad_interest: e.target.checked }))
                  }
                  className="rounded border-gray-300"
                />
                Interested in studying abroad
              </label>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowProfileForm(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveProfile}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg"
              >
                Save Profile
              </button>
            </div>
          </div>
        )}

        {/* AI Student Profile */}
        <section className="bg-white rounded-2xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-violet-600" /> AI Student Profile
            </h2>
            <span className="text-xs text-gray-400">
              {data?.profile.ai_profile_generated_at
                ? `Updated ${new Date(data.profile.ai_profile_generated_at).toLocaleDateString()}`
                : ''}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-400 font-medium uppercase mb-1">Student Type</p>
              <p className="font-semibold text-gray-900">{ai.student_type || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium uppercase mb-1">Learning Style</p>
              <span
                className={`inline-block px-2 py-0.5 rounded-full text-sm ${
                  learningStyleColors[(ai.learning_style || '').toLowerCase()] ||
                  'bg-gray-50 text-gray-700'
                }`}
              >
                {ai.learning_style || '—'}
              </span>
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium uppercase mb-1">Career Goal</p>
              <p className="font-semibold text-gray-900">{ai.career_goal || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium uppercase mb-1">Risk Score</p>
              <span
                className={`inline-block px-2 py-0.5 rounded-full text-sm ${
                  riskColors[(ai.risk_score || '').toLowerCase()] || 'bg-gray-50 text-gray-700'
                }`}
              >
                {ai.risk_score || '—'}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <p className="text-xs text-gray-400 font-medium uppercase mb-2 flex items-center gap-1">
                <Heart className="w-3 h-3" /> Strong Subjects
              </p>
              <div className="flex flex-wrap gap-1.5">
                {(ai.strong_subjects || []).map((s) => (
                  <span key={s} className="px-2 py-1 text-xs bg-emerald-50 text-emerald-700 rounded-lg">
                    {s}
                  </span>
                ))}
                {(ai.strong_subjects || []).length === 0 && (
                  <span className="text-sm text-gray-400">Not enough data yet</span>
                )}
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium uppercase mb-2 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Weak Subjects
              </p>
              <div className="flex flex-wrap gap-1.5">
                {(ai.weak_subjects || []).map((s) => (
                  <span key={s} className="px-2 py-1 text-xs bg-red-50 text-red-700 rounded-lg">
                    {s}
                  </span>
                ))}
                {(ai.weak_subjects || []).length === 0 && (
                  <span className="text-sm text-gray-400">Not enough data yet</span>
                )}
              </div>
            </div>
            <div className="md:col-span-2">
              <p className="text-xs text-gray-400 font-medium uppercase mb-2">Interested Universities</p>
              <div className="flex flex-wrap gap-1.5">
                {(ai.interested_universities || []).map((u) => (
                  <span key={u} className="px-2 py-1 text-xs bg-violet-50 text-violet-700 rounded-lg">
                    {u}
                  </span>
                ))}
                {(ai.interested_universities || []).length === 0 && (
                  <span className="text-sm text-gray-400">No university signals yet</span>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Learning Analytics */}
        <section>
          <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-indigo-600" /> Learning Analytics
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={Clock} label="Study Hours" value={`${learning?.total_hours ?? 0}h`} />
            <StatCard icon={BookOpen} label="Lessons" value={learning?.total_lessons ?? 0} />
            <StatCard icon={Target} label="Quiz Accuracy" value={`${learning?.avg_quiz_accuracy ?? 0}%`} />
            <StatCard icon={Award} label="Day Streak" value={learning?.learning_streak ?? 0} />
          </div>

          {learning && learning.subject_performance.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-200 p-6 mt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">Subject Performance</h3>
              <div className="space-y-3">
                {learning.subject_performance.map((sp) => (
                  <div key={sp.subject}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700 font-medium">{sp.subject}</span>
                      <span className="text-gray-400">
                        {sp.minutes} min · {sp.lessons} lessons · {sp.avg_accuracy}% accuracy
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full"
                        style={{ width: `${Math.min(100, (sp.minutes / 300) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Segments */}
        {data?.segments && data.segments.length > 0 && (
          <section>
            <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <GraduationCap className="w-5 h-5 text-indigo-600" /> Your Segments
            </h2>
            <div className="flex flex-wrap gap-2">
              {data.segments.map((s) => (
                <span
                  key={s.key}
                  className="px-3 py-1.5 bg-white border border-indigo-100 text-indigo-700 text-sm rounded-full"
                  title={s.description}
                >
                  {s.label}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Institution Recommendations */}
        {recommendations?.institutions && (
          <section>
            <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <Building2 className="w-5 h-5 text-indigo-600" /> Recommended Institutions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-xs font-medium text-emerald-600 uppercase mb-2">Safety Choices</p>
                <div className="space-y-2">
                  {recommendations.institutions.safety.map((r) => (
                    <RecommendationCard key={r.institution_id} {...r} tier="safety" />
                  ))}
                  {recommendations.institutions.safety.length === 0 && (
                    <p className="text-sm text-gray-400">No matches yet</p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-amber-600 uppercase mb-2">Competitive Choices</p>
                <div className="space-y-2">
                  {recommendations.institutions.competitive.map((r) => (
                    <RecommendationCard key={r.institution_id} {...r} tier="competitive" />
                  ))}
                  {recommendations.institutions.competitive.length === 0 && (
                    <p className="text-sm text-gray-400">No matches yet</p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-violet-600 uppercase mb-2">Dream Choices</p>
                <div className="space-y-2">
                  {recommendations.institutions.dream.map((r) => (
                    <RecommendationCard key={r.institution_id} {...r} tier="dream" />
                  ))}
                  {recommendations.institutions.dream.length === 0 && (
                    <p className="text-sm text-gray-400">No matches yet</p>
                  )}
                </div>
              </div>
            </div>

            {recommendations.institutions.best_matches.length > 0 && (
              <div className="mt-4">
                <p className="text-xs font-medium text-indigo-600 uppercase mb-2">Best Matches</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {recommendations.institutions.best_matches.slice(0, 6).map((r) => (
                    <RecommendationCard key={r.institution_id} {...r} tier="best" />
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Courses & Scholarships */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="bg-white rounded-2xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5 text-indigo-600" /> Recommended Courses
            </h2>
            <div className="space-y-2">
              {recommendations?.courses.courses?.map((c) => (
                <div
                  key={c.course_id}
                  className="flex items-center justify-between p-3 border border-gray-100 rounded-xl"
                >
                  <div>
                    <p className="text-sm font-semibold text-gray-800">{c.name}</p>
                    <p className="text-xs text-gray-400">
                      {c.institution_name}
                      {c.degree_awarded ? ` · ${c.degree_awarded}` : ''}
                    </p>
                  </div>
                  <span className="text-sm font-bold text-indigo-600">{c.score}%</span>
                </div>
              ))}
              {(!recommendations?.courses.courses ||
                recommendations.courses.courses.length === 0) && (
                <p className="text-sm text-gray-400">Complete your profile for course picks.</p>
              )}
            </div>
          </section>

          <section className="bg-white rounded-2xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <Award className="w-5 h-5 text-indigo-600" /> Scholarship Matches
            </h2>
            <div className="space-y-2">
              {recommendations?.scholarships.scholarships?.map((s) => (
                <div
                  key={s.scholarship_id}
                  className="p-3 border border-gray-100 rounded-xl"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-800">{s.institution_name}</p>
                    <span className="text-sm font-bold text-indigo-600">{s.score}%</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    {s.level}
                    {s.min_gpa ? ` · Min GPA ${s.min_gpa}` : ''}
                  </p>
                  {s.match_reasons.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {s.match_reasons.map((r) => (
                        <span
                          key={r}
                          className="px-2 py-0.5 text-[11px] bg-emerald-50 text-emerald-700 rounded-full"
                        >
                          {r}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {(!recommendations?.scholarships.scholarships ||
                recommendations.scholarships.scholarships.length === 0) && (
                <p className="text-sm text-gray-400">No scholarship matches yet.</p>
              )}
            </div>
          </section>
        </div>

        {/* Career */}
        {profile?.dream_career && (
          <section className="bg-gradient-to-br from-indigo-50 to-violet-50 rounded-2xl border border-indigo-100 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Briefcase className="w-8 h-8 text-indigo-600" />
                <div>
                  <p className="text-sm text-gray-500">Your Dream Career</p>
                  <p className="text-xl font-bold text-gray-900">{profile.dream_career}</p>
                </div>
              </div>
              <Link
                to="/"
                className="flex items-center gap-1 text-sm text-indigo-600 font-medium hover:text-indigo-700"
              >
                Explore institutions <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
            {profile.interested_sectors && profile.interested_sectors.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {profile.interested_sectors.map((s) => (
                  <span key={s} className="px-2 py-1 text-xs bg-white text-indigo-700 rounded-lg">
                    {s}
                  </span>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Privacy note */}
        <section className="bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" /> Privacy & Consent
          </h2>
          <p className="text-sm text-gray-500 leading-relaxed">
            Your analytics data is collected only with your explicit consent and used to power
            your personalized recommendations. Reports shared with institutions use only
            aggregated, anonymized data. You can revoke consent at any time — events are then
            stored without your identity.
          </p>
          <div className="flex items-center gap-2 mt-3">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 text-sm rounded-full ${
                profile?.analytics_consent
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              Analytics {profile?.analytics_consent ? 'Enabled' : 'Disabled'}
            </span>
            <Globe2 className="w-4 h-4 text-gray-300" />
            <span className="text-xs text-gray-400">Bangla & English privacy policy available</span>
          </div>
        </section>
      </main>
    </div>
  )
}
