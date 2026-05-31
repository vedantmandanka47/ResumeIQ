import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAnalysis } from '../hooks/useAnalysis';

import ScoreRing from '../components/analysis/ScoreRing';
import DimensionCard from '../components/analysis/DimensionCard';
import StrengthsList from '../components/analysis/StrengthsList';
import CriticalFixes from '../components/analysis/CriticalFixes';
import CompanyInput from '../components/company/CompanyInput';
import SignalsPanel from '../components/company/SignalsPanel';
import GapList from '../components/company/GapList';
import VerdictBanner from '../components/company/VerdictBanner';
import BenchmarkChart from '../components/benchmark/BenchmarkChart';

import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import ErrorBlock from '../components/common/ErrorBlock';

import './AnalysisPage.css';

export default function AnalysisPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { 
    analysis, setAnalysis, 
    companyResult, setCompanyResult,
    benchmarkResult, setBenchmarkResult 
  } = useAnalysis();

  const [isLoading, setIsLoading] = useState(!analysis);
  const [error, setError] = useState(null);

  const [isResearching, setIsResearching] = useState(false);
  const [companyError, setCompanyError] = useState(null);

  const [isBenchmarking, setIsBenchmarking] = useState(false);
  const [benchmarkError, setBenchmarkError] = useState(null);

  const fetchAnalysis = useCallback(async () => {
    if (analysis) return; // Use cached context
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.resume.analyze(sessionId, { target_role: null });
      setAnalysis(data);
    } catch (err) {
      setError(err.message || 'Failed to analyze resume.');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, analysis, setAnalysis]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  const handleResearch = async (companyName) => {
    setIsResearching(true);
    setCompanyError(null);
    try {
      const data = await api.resume.analyzeCompany(sessionId, { target_company: companyName });
      setCompanyResult(data);
    } catch (err) {
      setCompanyError(err.message || 'Failed to research company.');
    } finally {
      setIsResearching(false);
    }
  };

  const handleBenchmark = async () => {
    setIsBenchmarking(true);
    setBenchmarkError(null);
    try {
      await api.resume.save(sessionId);
      const data = await api.resume.benchmark();
      setBenchmarkResult(data);
    } catch (err) {
      setBenchmarkError(err.message || 'Failed to generate benchmark.');
    } finally {
      setIsBenchmarking(false);
    }
  };

  if (isLoading) {
    return (
      <div className="page analysis-page loading-state">
        <Spinner size={32} />
        <p className="text-secondary mt-4">Analyzing your resume...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page analysis-page container">
        <ErrorBlock message={error} onRetry={fetchAnalysis} />
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="page analysis-page">
      <div className="container container--wide">
        
        {/* Top Section */}
        <div className="analysis-top">
          <ScoreRing score={analysis.overall_score} mode={analysis.mode} />
          <p className="analysis-summary text-secondary text-base">
            {analysis.summary}
          </p>
        </div>

        {/* Strengths */}
        <StrengthsList strengths={analysis.top_strengths} />

        {/* Dimensions */}
        <div className="dimensions-grid">
          {analysis.dimensions.map((dim, idx) => (
            <DimensionCard 
              key={idx}
              name={dim.name}
              score={dim.score}
              verdict={dim.verdict}
              finding={dim.finding}
            />
          ))}
        </div>

        {/* Critical Fixes */}
        <CriticalFixes fixes={analysis.critical_fixes} />

        {/* Company Match Section */}
        <div className="company-section mt-12 pt-8 border-t">
          <h3 className="label mb-4">Company Match</h3>
          {!companyResult ? (
            <CompanyInput onResearch={handleResearch} loading={isResearching} />
          ) : (
            <div className="company-result">
              <VerdictBanner 
                verdict={companyResult.verdict} 
                reason={companyResult.verdict_reason} 
                recommendation={companyResult.apply_recommendation} 
              />
              <div className="company-details">
                <SignalsPanel signals={companyResult.company_signals} />
                <GapList gaps={companyResult.gap_analysis} />
              </div>
            </div>
          )}
          {companyError && <ErrorBlock message={companyError} className="mt-4" />}
        </div>

        {/* Benchmark Section */}
        {benchmarkResult && (
          <div className="benchmark-section mt-12 pt-8 border-t">
            <BenchmarkChart benchmark={benchmarkResult} userDimensions={analysis.dimensions} />
          </div>
        )}
        {benchmarkError && <ErrorBlock message={benchmarkError} className="mt-4" />}

        {/* Action Row */}
        <div className="action-row mt-12 pt-8 border-t">
          <Button onClick={() => navigate(`/rewrite/${sessionId}`)}>Rewrite Resume &rarr;</Button>
          <Button variant="secondary" onClick={() => navigate(`/roadmap/${sessionId}`)}>Generate Roadmap &rarr;</Button>
          {!benchmarkResult && (
            <Button variant="secondary" onClick={handleBenchmark} loading={isBenchmarking}>
              Save &amp; Benchmark &rarr;
            </Button>
          )}
        </div>

      </div>
    </div>
  );
}
