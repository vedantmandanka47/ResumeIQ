import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAnalysis } from '../hooks/useAnalysis';

import SideBySide from '../components/rewrite/SideBySide';
import ChangeLog from '../components/rewrite/ChangeLog';

import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import ErrorBlock from '../components/common/ErrorBlock';

import './RewritePage.css';

export default function RewritePage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { rewriteResult, setRewriteResult } = useAnalysis();

  const [isLoading, setIsLoading] = useState(!rewriteResult);
  const [error, setError] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const fetchRewrite = useCallback(async () => {
    if (rewriteResult) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.resume.rewrite(sessionId, { model: 'gemini-1.5-pro' });
      setRewriteResult(data);
    } catch (err) {
      setError(err.message || 'Failed to rewrite resume.');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, rewriteResult, setRewriteResult]);

  useEffect(() => {
    fetchRewrite();
  }, [fetchRewrite]);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      await api.resume.rewriteDownload(sessionId);
    } catch (err) {
      alert(err.message || 'Failed to download.');
    } finally {
      setIsDownloading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="page rewrite-page loading-state">
        <Spinner size={32} />
        <p className="text-secondary mt-4">Rewriting your resume with ATS optimization...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page rewrite-page container">
        <ErrorBlock message={error} onRetry={fetchRewrite} />
      </div>
    );
  }

  if (!rewriteResult) return null;

  return (
    <div className="page rewrite-page">
      <div className="container container--wide">
        
        <div className="rewrite-header">
          <h1 className="text-3xl">Rewritten Resume</h1>
          <p className="text-secondary text-base max-w-600">
            We&apos;ve optimized your resume for ATS parsers and improved impact statements. 
            Review the changes below and download the final DOCX.
          </p>
        </div>

        {/* Change Log */}
        <div className="mt-8 mb-8">
          <ChangeLog changes={rewriteResult.change_log} />
        </div>

        {/* Side by Side Comparison */}
        <SideBySide 
          oldText={rewriteResult.original_text_preview} 
          newText={rewriteResult.rewritten_text_preview} 
        />

        {/* Action Row */}
        <div className="action-row mt-12 pt-8 border-t">
          <Button onClick={handleDownload} loading={isDownloading}>
            Download DOCX
          </Button>
          <Button variant="secondary" onClick={() => navigate(`/analysis/${sessionId}`)}>
            &larr; Back to Analysis
          </Button>
        </div>

      </div>
    </div>
  );
}
