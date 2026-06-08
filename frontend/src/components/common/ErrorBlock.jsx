import { useState, useEffect } from 'react';
import './ErrorBlock.css';

export default function ErrorBlock({ message, onRetry, retryAfter, className = '' }) {
  const [countdown, setCountdown] = useState(
    retryAfter != null ? Math.ceil(retryAfter) : null
  );

  useEffect(() => {
    if (countdown == null || countdown <= 0) return;
    const t = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) { clearInterval(t); return 0; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [countdown]);

  const isRateLimited = countdown != null;

  return (
    <div className={`error-block ${className}`} role="alert">
      <div style={{ flex: 1 }}>
        <p className="error-block__message">{message || 'Something went wrong. Please try again.'}</p>

        {isRateLimited && countdown > 0 && (
          <p className="error-block__countdown text-sm text-secondary" style={{ marginTop: 4 }}>
            Rate limit reached — retry in{' '}
            <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{countdown}s</strong>
          </p>
        )}
      </div>

      {onRetry && (
        <button
          className="btn btn-text error-block__retry"
          onClick={onRetry}
          disabled={isRateLimited && countdown > 0}
        >
          {isRateLimited && countdown > 0 ? `Wait ${countdown}s…` : 'Try again'}
        </button>
      )}
    </div>
  );
}
