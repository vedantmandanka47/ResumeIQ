import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import SystemStatus from './pages/SystemStatus'
import './App.css'

/**
 * Root application component.
 * Routing is defined here. Every phase adds its routes in this file.
 */
export default function App() {
  return (
    <BrowserRouter>
      {/* Ambient gradient mesh — decorative, pointer-events: none */}
      <div className="gradient-mesh" aria-hidden="true" />

      {/* Sticky top navigation */}
      <Navbar />

      {/* Page content */}
      <main className="app-main" id="main-content">
        <Routes>
          {/* Phase 0 — System Status (home for now) */}
          <Route path="/"       element={<Navigate to="/status" replace />} />
          <Route path="/status" element={<SystemStatus />} />

          {/* Phase 1+ routes added below as they are built */}
          {/* <Route path="/upload"   element={<UploadPage />} /> */}
          {/* <Route path="/analysis/:sessionId" element={<AnalysisPage />} /> */}

          {/* 404 fallback */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

function NotFound() {
  return (
    <div className="not-found page">
      <div className="container not-found__inner">
        <span className="not-found__code" aria-hidden="true">404</span>
        <h1>Page not found</h1>
        <p>This route doesn't exist yet — it may be added in a future phase.</p>
        <a href="/status" className="btn btn-primary" style={{ marginTop: '1.5rem' }}>
          Back to Status
        </a>
      </div>
    </div>
  )
}
