export default function ChangeLog({ changes }) {
  if (!changes || changes.length === 0) return null;

  const getTypeClass = (type) => {
    if (type === 'addition') return 'type--addition';
    if (type === 'deletion') return 'type--deletion';
    if (type === 'modification') return 'type--modification';
    return '';
  };

  return (
    <div className="change-log">
      <h3 className="label mb-4">Change Log</h3>
      <div className="change-list">
        {changes.map((change, idx) => (
          <div key={idx} className="change-item">
            <span className={`change-badge ${getTypeClass(change.type)}`}>
              {change.type}
            </span>
            <span className="change-desc">{change.description}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
