/**
 * Badge — Pill badge for status or labels.
 */
import './Badge.css';

export default function Badge({ children, variant = 'idle', className = '' }) {
  return (
    <span className={`badge badge--${variant} ${className}`}>
      {children}
    </span>
  );
}
