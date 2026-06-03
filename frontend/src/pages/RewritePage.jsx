import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAnalysis } from '../hooks/useAnalysis';

import SideBySide from '../components/rewrite/SideBySide';
import ChangeLog from '../components/rewrite/ChangeLog';
import { ResumeDocxPreview } from '../components/ResumeDocxPreview';
import { TemplateSwitcher } from '../components/TemplateSwitcher';

import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import ErrorBlock from '../components/common/ErrorBlock';

import './RewritePage.css';

async function loadStructuredResumeData(sessionId) {
  try {
    const cached = await api.resume.structuredResume(sessionId);
    return cached.resume_data;
  } catch (err) {
    const cacheMiss =
      err.code === 'STRUCTURED_RESUME_NOT_FOUND' || err.code === '404';
    if (!cacheMiss) {
      throw err;
    }
  }

  try {
    await api.generation.generate({ session_id: sessionId });
  } catch (err) {
    if (err.code === 'STRUCTURED_RESUME_SCHEMA_MISSING') {
      throw new Error(
        'Database migration required. From the backend folder run: alembic upgrade head',
      );
    }
    throw err;
  }

  const generated = await api.resume.structuredResume(sessionId);
  return generated.resume_data;
}

export default function RewritePage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { rewriteResult, setRewriteResult } = useAnalysis();

  const [isLoading, setIsLoading] = useState(!rewriteResult);
  const [error, setError] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [resumeData, setResumeData] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState('minimalist');
  const [previewError, setPreviewError] = useState(null);

  const fetchRewrite = useCallback(async () => {
    if (rewriteResult) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.resume.rewrite(sessionId, {});
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

  useEffect(() => {
    if (!rewriteResult) return undefined;

    let cancelled = false;
    setPreviewError(null);

    loadStructuredResumeData(sessionId)
      .then((data) => {
        if (!cancelled) setResumeData(data);
      })
      .catch((err) => {
        if (!cancelled) {
          const message =
            err.message ||
            (err.code === 'GENERATION_FAILED'
              ? 'Failed to build structured resume for DOCX preview. Check backend logs and Gemini configuration.'
              : 'Failed to load structured resume for preview.');
          setPreviewError(message);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [rewriteResult, sessionId]);

  const handleDownload = async () => {
    if (!resumeData) return;
    setIsDownloading(true);
    try {
      const buffer = await api.resume.renderDocxDownload(resumeData, selectedTemplate);
      const blob = new Blob([buffer], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'resume.docx';
      anchor.click();
      URL.revokeObjectURL(url);
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
            Review the changes below, preview formatted DOCX output, and download when ready.
          </p>
        </div>

        <div className="mt-8 mb-8">
          <ChangeLog changes={rewriteResult.change_log} />
        </div>

        <SideBySide
          oldText={rewriteResult.original_text_preview}
          newText={rewriteResult.rewritten_text_preview}
        />

        <section className="rewrite-preview mt-12 pt-8 border-t">
          <div className="rewrite-preview__header">
            <h2 className="text-xl">Your Rewritten Resume</h2>
            {resumeData && (
              <button
                type="button"
                className="rewrite-preview__download"
                onClick={handleDownload}
                disabled={isDownloading}
              >
                {isDownloading ? 'Downloading…' : 'Download .docx'}
              </button>
            )}
          </div>

          {previewError && (
            <ErrorBlock message={previewError} />
          )}

          {resumeData && (
            <>
              <TemplateSwitcher
                selectedId={selectedTemplate}
                onChange={setSelectedTemplate}
              />
              <ResumeDocxPreview
                resumeData={resumeData}
                templateId={selectedTemplate}
              />
            </>
          )}

          {!resumeData && !previewError && (
            <div className="rewrite-preview__loading">
              <Spinner size={24} />
              <p className="text-secondary">Preparing DOCX preview…</p>
            </div>
          )}
        </section>

        <div className="action-row mt-12 pt-8 border-t">
          <Button variant="secondary" onClick={() => navigate(`/analysis/${sessionId}`)}>
            &larr; Back to Analysis
          </Button>
        </div>

      </div>
    </div>
  );
}
