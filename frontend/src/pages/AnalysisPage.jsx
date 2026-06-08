import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
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
import StepProgress from '../components/common/StepProgress';

import './AnalysisPage.css';

const ANALYSIS_STEPS = [
  { key: 'extract',   label: 'Extracting resume content…'      },
  { key: 'structure', label: 'Parsing resume structure…'        },
  { key: 'ats',       label: 'Running ATS compatibility check…' },
  { key: 'score',     label: 'Scoring 7 dimensions…'           },
  { key: 'insights',  label: 'Generating actionable insights…'  },
];

export default function AnalysisPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const targetRole = location.state?.targetRole ?? null;
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

  const [jdUrl, setJdUrl]           = useState('');
  const [isJdAnalyzing, setIsJdAnalyzing] = useState(false);
  const [jdError, setJdError]       = useState(null);

  const handleJdAnalyze = async () => {
    if (!jdUrl.trim()) return;
    setIsJdAnalyzing(true);
    setJdError(null);
    try {
      const data = await api.resume.analyzeJdUrl(sessionId, { job_url: jdUrl.trim() });
      setAnalysis(data);  // refresh analysis with JD-calibrated scores
    } catch (err) {
      setJdError(err);
    } finally {
      setIsJdAnalyzing(false);
    }
  };

  const fetchAnalysis = useCallback(async () => {
    if (analysis) return; // Use cached context
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.resume.analyze(sessionId, { target_role: targetRole });
      setAnalysis(data);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, analysis, setAnalysis, targetRole]);

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
      setCompanyError(err);
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
      setBenchmarkError(err);
    } finally {
      setIsBenchmarking(false);
    }
  };

  if (isLoading) {
    return (
      <div className="page analysis-page loading-state">
        <StepProgress steps={ANALYSIS_STEPS} intervalMs={2400} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page analysis-page container">
        <ErrorBlock
          message={typeof error === 'string' ? error : error.message}
          retryAfter={error?.retryAfter}
          onRetry={fetchAnalysis}
        />
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
            <div
              key={idx}
              className="stagger-item"
              style={{ '--stagger-delay': `${idx * 60}ms` }}
            >
              <DimensionCard 
                name={dim.name}
                score={dim.score}
                verdict={dim.verdict}
                finding={dim.finding}
              />
            </div>
          ))}
        </div>

        {/* Critical Fixes */}
        <CriticalFixes fixes={analysis.critical_fixes} />

        {/* JD URL Analyzer Section */}
        <div className="jd-url-section mt-12 pt-8 border-t">
          <h3 className="label mb-4">Grade Against a Job Posting</h3>
          <p className="text-secondary text-sm" style={{ marginBottom: 16 }}>
            Paste a job posting URL to re-score your resume against exact JD requirements.
          </p>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            <input
              className="input-base"
              type="url"
              placeholder="https://jobs.example.com/senior-engineer"
              value={jdUrl}
              onChange={(e) => setJdUrl(e.target.value)}
              style={{ flex: 1 }}
              disabled={isJdAnalyzing}
            />
            <Button onClick={handleJdAnalyze} loading={isJdAnalyzing} disabled={!jdUrl.trim()}>
              Analyze →
            </Button>
          </div>
          {jdError && (
            <ErrorBlock
              message={typeof jdError === 'string' ? jdError : jdError.message}
              retryAfter={jdError?.retryAfter}
              className="mt-4"
            />
          )}
        </div>

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
          {companyError && (
            <ErrorBlock
              message={typeof companyError === 'string' ? companyError : companyError.message}
              retryAfter={companyError?.retryAfter}
              className="mt-4"
            />
          )}
        </div>

        {/* Benchmark Section */}
        {benchmarkResult && (
          <div className="benchmark-section mt-12 pt-8 border-t">
            <BenchmarkChart benchmark={benchmarkResult} userDimensions={analysis.dimensions} />
          </div>
        )}
        {benchmarkError && (
          <ErrorBlock
            message={typeof benchmarkError === 'string' ? benchmarkError : benchmarkError.message}
            retryAfter={benchmarkError?.retryAfter}
            className="mt-4"
          />
        )}

        {/* Action Row */}
        <div className="action-row mt-12 pt-8 border-t">
          <Button onClick={() => navigate(`/rewrite/${sessionId}`)}>Rewrite Resume &rarr;</Button>
          <Button variant="secondary" onClick={() => navigate(`/roadmap/${sessionId}`)}>Generate Roadmap &rarr;</Button>
          <Button onClick={() => navigate(`/cover-letter/${sessionId}`)}>
            ✦ Generate Cover Letter
          </Button>
          <Button variant="secondary" onClick={() => navigate(`/history/${sessionId}`)}>
            View History
          </Button>
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
