/**
 * ErrorBlock — displays an API error or unexpected error.
 */
import './ErrorBlock.css';
import Button from './Button';

export default function ErrorBlock({ message, onRetry, className = '' }) {
  return (
    <div className={`error-block ${className}`}>
      <div className="error-block__content">
        <strong>Error</strong>
        <p>{message || 'Something went wrong. Please try again.'}</p>
      </div>
      {onRetry && (
        <div className="error-block__action">
          <Button variant="secondary" onClick={onRetry}>Try Again</Button>
        </div>
      )}
    </div>
  );
}
