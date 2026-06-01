export default function CriticalFixes({ fixes }) {
  if (!fixes || fixes.length === 0) return null;

  // Sort by priority (1 is highest)
  const sortedFixes = [...fixes].sort((a, b) => a.priority - b.priority);

  const getPriorityClass = (priority) => {
    if (priority <= 2) return 'priority--high';
    if (priority <= 4) return 'priority--medium';
    return 'priority--low';
  };

  return (
    <div className="fixes-section">
      <h3 className="label">Critical Fixes</h3>
      <ol className="fixes-list">
        {sortedFixes.map((fix, idx) => (
          <li key={idx} className="fix-item">
            <span className={`fix-item__badge ${getPriorityClass(fix.priority)}`} />
            <div className="fix-item__content">
              <p className="fix-item__issue">{fix.issue}</p>
              <p className="fix-item__fix">{fix.fix}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
