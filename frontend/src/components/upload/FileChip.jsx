export default function FileChip({ file, onRemove }) {
  // Convert size to nice format
  const formatSize = (bytes) => {
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // Truncate name
  const truncate = (name) => {
    if (name.length > 30) return name.substring(0, 27) + '...';
    return name;
  };

  return (
    <div className="file-chip">
      {/* Inline file icon */}
      <svg className="file-chip__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
        <polyline points="13 2 13 9 20 9"/>
      </svg>

      <div className="file-chip__info">
        <span className="file-chip__name">{truncate(file.name)}</span>
        <span className="file-chip__size">{formatSize(file.size)}</span>
      </div>

      <button className="file-chip__remove" onClick={onRemove} aria-label="Remove file">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  );
}
