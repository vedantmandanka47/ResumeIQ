import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import Button from '../components/common/Button';
import ErrorBlock from '../components/common/ErrorBlock';
import StepProgress from '../components/common/StepProgress';
import './CoverLetterPage.css';

const TONE_OPTIONS = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly',     label: 'Friendly'     },
  { value: 'concise',      label: 'Concise'      },
];

const CL_STEPS = [
  { key: 'context',  label: 'Reading resume context…'     },
  { key: 'research', label: 'Analysing company signals…'  },
  { key: 'draft',    label: 'Drafting cover letter…'      },
  { key: 'polish',   label: 'Polishing tone and flow…'   },
];

export default function CoverLetterPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [targetRole,   setTargetRole]   = useState('');
  const [companyName,  setCompanyName]  = useState('');
  const [tone,         setTone]         = useState('professional');
  const [isLoading,    setIsLoading]    = useState(false);
  const [result,       setResult]       = useState(null);
  const [error,        setError]        = useState(null);
  const [copied,       setCopied]       = useState(false);

  const handleGenerate = async () => {
    if (!targetRole.trim() || !companyName.trim()) return;
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.resume.coverLetter(sessionId, {
        target_role: targetRole.trim(),
        company_name: companyName.trim(),
        tone,
      });
      setResult(data);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!result?.cover_letter_text) return;
    await navigator.clipboard.writeText(result.cover_letter_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="page cover-letter-page">
      <div className="container">
        <div className="cl-header">
          <h1 className="text-3xl">Cover Letter Generator</h1>
          <p className="text-secondary text-base">
            One click generates a fully tailored cover letter using your resume context
            and any company signals already in this session.
          </p>
        </div>

        {!result && !isLoading && (
          <div className="cl-form card">
            <div className="cl-form__field">
              <label className="label" htmlFor="cl-role">Target role <span style={{color:'var(--rework)'}}>*</span></label>
              <input
                id="cl-role"
                className="input-base"
                placeholder="e.g. Senior Software Engineer"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                maxLength={120}
              />
            </div>

            <div className="cl-form__field">
              <label className="label" htmlFor="cl-company">Company <span style={{color:'var(--rework)'}}>*</span></label>
              <input
                id="cl-company"
                className="input-base"
                placeholder="e.g. Stripe"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                maxLength={100}
              />
            </div>

            <div className="cl-form__field">
              <span className="label">Tone</span>
              <div className="cl-tone-buttons">
                {TONE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    className={`btn ${tone === opt.value ? 'btn-primary' : 'btn-secondary'} btn--sm`}
                    onClick={() => setTone(opt.value)}
                    style={{ fontSize: 13, padding: '7px 16px' }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <ErrorBlock
                message={typeof error === 'string' ? error : error.message}
                retryAfter={error?.retryAfter}
              />
            )}

            <Button
              onClick={handleGenerate}
              disabled={!targetRole.trim() || !companyName.trim()}
              style={{ marginTop: 8 }}
            >
              Generate Cover Letter →
            </Button>
          </div>
        )}

        {isLoading && (
          <div className="cl-loading">
            <StepProgress steps={CL_STEPS} intervalMs={3000} />
          </div>
        )}

        {result && (
          <div className="cl-result">
            <div className="cl-result__meta">
              <span className="label">{result.word_count} words</span>
              <button className="btn btn-secondary" onClick={() => setResult(null)} style={{fontSize: 13, padding: '7px 16px'}}>
                Regenerate
              </button>
              <button className="btn btn-primary" onClick={handleCopy} style={{fontSize: 13, padding: '7px 16px'}}>
                {copied ? '✓ Copied' : 'Copy to clipboard'}
              </button>
            </div>

            {result.key_selling_points?.length > 0 && (
              <div className="cl-selling-points card">
                <p className="label" style={{marginBottom: 10}}>Key selling points</p>
                {result.key_selling_points.map((pt, i) => (
                  <p key={i} className="text-sm text-secondary" style={{marginBottom: 4}}>
                    — {pt}
                  </p>
                ))}
              </div>
            )}

            <div className="cl-text card">
              <pre className="cl-text__content">{result.cover_letter_text}</pre>
            </div>
          </div>
        )}

        <div className="action-row mt-8 pt-8 border-t">
          <button className="btn btn-secondary" onClick={() => navigate(`/analysis/${sessionId}`)}>
            ← Back to Analysis
          </button>
        </div>
      </div>
    </div>
  );
}
