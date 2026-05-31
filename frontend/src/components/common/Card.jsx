/**
 * Card — A minimal surface-1 card with a subtle border.
 */
import './Card.css';

export default function Card({ children, className = '', ...props }) {
  return (
    <div className={`card ${className}`} {...props}>
      {children}
    </div>
  );
}
