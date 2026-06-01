export default function VerdictBanner({ verdict, reason, recommendation }) {
  if (!verdict) return null;

  const getVerdictClass = (v) => {
    if (v === 'GO') return 'verdict--go';
    if (v === 'HOLD') return 'verdict--hold';
    return 'verdict--rework';
  };

  return (
    <div className={`verdict-banner ${getVerdictClass(verdict)}`}>
      <h2 className="verdict-banner__title">{verdict}</h2>
      <p className="verdict-banner__reason">{reason}</p>
      {recommendation && (
        <p className="verdict-banner__recommendation">{recommendation}</p>
      )}
    </div>
  );
}
