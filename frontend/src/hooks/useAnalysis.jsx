import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const STORAGE_KEY = 'resumeiq:analysis';

function loadFromStorage() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

const AnalysisContext = createContext(null);

export function AnalysisProvider({ children }) {
  const persisted = loadFromStorage();

  const [analysis,        setAnalysis]        = useState(persisted.analysis        ?? null);
  const [companyResult,   setCompanyResult]   = useState(persisted.companyResult   ?? null);
  const [rewriteResult,   setRewriteResult]   = useState(persisted.rewriteResult   ?? null);
  const [roadmapResult,   setRoadmapResult]   = useState(persisted.roadmapResult   ?? null);
  const [benchmarkResult, setBenchmarkResult] = useState(persisted.benchmarkResult ?? null);

  // Persist to sessionStorage on every state change
  useEffect(() => {
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ analysis, companyResult, rewriteResult, roadmapResult, benchmarkResult })
      );
    } catch {
      // sessionStorage full or unavailable — continue silently
    }
  }, [analysis, companyResult, rewriteResult, roadmapResult, benchmarkResult]);

  const clearAll = useCallback(() => {
    setAnalysis(null);
    setCompanyResult(null);
    setRewriteResult(null);
    setRoadmapResult(null);
    setBenchmarkResult(null);
    try { sessionStorage.removeItem(STORAGE_KEY); } catch {}
  }, []);

  return (
    <AnalysisContext.Provider
      value={{
        analysis, setAnalysis,
        companyResult, setCompanyResult,
        rewriteResult, setRewriteResult,
        roadmapResult, setRoadmapResult,
        benchmarkResult, setBenchmarkResult,
        clearAll,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error('useAnalysis must be used within an AnalysisProvider');
  return ctx;
}
