import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import Spinner from '../components/common/Spinner';
import ErrorBlock from '../components/common/ErrorBlock';
import './HistoryPage.css';

export default function HistoryPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [snapshots, setSnapshots] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.resume.history(sessionId)
      .then((data) => setSnapshots(data.snapshots || []))
      .catch((err) => setError(err))
      .finally(() => setIsLoading(false));
  }, [sessionId]);

  if (isLoading) return (
    <div className="page history-page loading-state"><Spinner size={28} /></div>
  );

  if (error) return (
    <div className="page history-page container">
      <ErrorBlock
        message={typeof error === 'string' ? error : error.message}
        retryAfter={error?.retryAfter}
      />
    </div>
  );

  return (
    <div className="page history-page">
      <div className="container">
        <div className="history-header">
          <h1 className="text-3xl">Session History</h1>
          <p className="text-secondary text-base">
            {snapshots.length} snapshot{snapshots.length !== 1 ? 's' : ''} saved
          </p>
        </div>

        {snapshots.length === 0 ? (
          <div className="history-empty">
            <p className="text-secondary">No history snapshots yet.</p>
            <p className="text-muted text-sm">
              Snapshots are saved when you click "Save &amp; Benchmark".
            </p>
          </div>
        ) : (
          <div className="history-list">
            {snapshots.map((snap, idx) => (
              <div
                key={snap._id || idx}
                className="history-card card stagger-item"
                style={{ '--stagger-delay': `${idx * 50}ms` }}
              >
                <div className="history-card__meta">
                  <span className="label">
                    {new Date(snap.timestamp).toLocaleDateString([], {
                      year: 'numeric', month: 'short', day: 'numeric'
                    })}
                  </span>
                  <span className="text-muted text-sm">
                    {new Date(snap.timestamp).toLocaleTimeString([], {
                      hour: '2-digit', minute: '2-digit'
                    })}
                  </span>
                </div>

                <div className="history-card__score">
                  <span
                    className="history-score"
                    style={{
                      color: snap.overall_score >= 70
                        ? 'var(--score-high)'
                        : snap.overall_score >= 40
                          ? 'var(--score-mid)'
                          : 'var(--score-low)',
                    }}
                  >
                    {snap.overall_score ?? '—'}
                  </span>
                  <span className="text-muted text-xs">/ 100</span>
                </div>

                <div className="history-card__tags">
                  {snap.mode && <span className="badge badge--idle">{snap.mode}</span>}
                  {snap.rewrite_result && <span className="badge badge--go">Rewritten</span>}
                  {snap.company_result && <span className="badge badge--idle">Company match</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="action-row mt-8 pt-8 border-t">
          <button className="btn btn-secondary" onClick={() => navigate(-1)}>
            &larr; Back
          </button>
        </div>
      </div>
    </div>
  );
}
