import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import ErrorBoundary from './components/common/ErrorBoundary';
import StatusPage from './pages/StatusPage';
import UploadPage from './pages/UploadPage';
import AnalysisPage from './pages/AnalysisPage';
import RewritePage from './pages/RewritePage';
import RoadmapPage from './pages/RoadmapPage';
import { AnalysisProvider } from './hooks/useAnalysis';

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="app-main" id="main-content">
        <ErrorBoundary>
          <AnalysisProvider>
            <Routes>
              <Route path="/" element={<UploadPage />} />
              <Route path="/status" element={<StatusPage />} />
              <Route path="/analysis/:sessionId" element={<AnalysisPage />} />
              <Route path="/rewrite/:sessionId" element={<RewritePage />} />
              <Route path="/roadmap/:sessionId" element={<RoadmapPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </AnalysisProvider>
        </ErrorBoundary>
      </main>
    </BrowserRouter>
  );
}
