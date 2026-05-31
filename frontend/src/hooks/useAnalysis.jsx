/**
 * useAnalysis — analysis state management via React Context
 * Stores all analysis results so they can be shared across pages
 * without re-fetching.
 */

import { createContext, useContext, useState, useCallback } from 'react';

const AnalysisContext = createContext(null);

export function AnalysisProvider({ children }) {
  const [analysis, setAnalysis] = useState(null);
  const [companyResult, setCompanyResult] = useState(null);
  const [rewriteResult, setRewriteResult] = useState(null);
  const [roadmapResult, setRoadmapResult] = useState(null);
  const [benchmarkResult, setBenchmarkResult] = useState(null);

  const clearAll = useCallback(() => {
    setAnalysis(null);
    setCompanyResult(null);
    setRewriteResult(null);
    setRoadmapResult(null);
    setBenchmarkResult(null);
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
  if (!ctx) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return ctx;
}
