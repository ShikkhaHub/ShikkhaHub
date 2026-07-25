import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import InstitutionListing from './pages/InstitutionListing'
import InstitutionDetail from './pages/InstitutionDetail'
import ComparePage from './pages/ComparePage'
import AdminDashboard from './pages/admin/AdminDashboard'
import GoogleAnalytics from './components/GoogleAnalytics'

function App() {
  return (
    <BrowserRouter>
      <GoogleAnalytics />
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/institutions" element={<InstitutionListing />} />
        <Route path="/institutions/:slug" element={<InstitutionDetail />} />
        <Route path="/compare" element={<ComparePage />} />
        
        {/* Admin Routes */}
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/institutions" element={<AdminDashboard />} />
        <Route path="/admin/users" element={<AdminDashboard />} />
        <Route path="/admin/courses" element={<AdminDashboard />} />
        <Route path="/admin/admissions" element={<AdminDashboard />} />
        <Route path="/admin/scholarships" element={<AdminDashboard />} />
        <Route path="/admin/applications" element={<AdminDashboard />} />
        <Route path="/admin/materials" element={<AdminDashboard />} />
        <Route path="/admin/banners" element={<AdminDashboard />} />
        <Route path="/admin/messages" element={<AdminDashboard />} />
        <Route path="/admin/notifications" element={<AdminDashboard />} />
        <Route path="/admin/contacts" element={<AdminDashboard />} />
        <Route path="/admin/reports" element={<AdminDashboard />} />
        <Route path="/admin/analytics" element={<AdminDashboard />} />
        <Route path="/admin/logs" element={<AdminDashboard />} />
        <Route path="/admin/settings" element={<AdminDashboard />} />
        <Route path="/admin/roles" element={<AdminDashboard />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
