/**
 * Button — generic button component matching the design system.
 */
import Spinner from './Spinner';

export default function Button({ 
  children, 
  variant = 'primary', 
  loading = false, 
  disabled = false, 
  className = '', 
  ...props 
}) {
  const baseClass = `btn btn-${variant}`;
  return (
    <button 
      className={`${baseClass} ${className}`} 
      disabled={disabled || loading} 
      {...props}
    >
      {loading && <Spinner size={14} />}
      {!loading && children}
    </button>
  );
}
