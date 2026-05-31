export default function GapList({ gaps }) {
  if (!gaps || gaps.length === 0) return null;

  const getSeverityClass = (severity) => {
    if (severity === 'critical') return 'severity--critical';
    if (severity === 'moderate') return 'severity--moderate';
    return 'severity--minor';
  };

  return (
    <div className="gap-list">
      {gaps.map((gap, idx) => (
        <div key={idx} className="gap-item">
          <span className={`gap-item__dot ${getSeverityClass(gap.severity)}`} />
          <span className="gap-item__text">{gap.gap}</span>
          <span className="gap-item__severity">({gap.severity})</span>
        </div>
      ))}
    </div>
  );
}
