import '../../pages/UploadPage.css';

export default function DropZone({ onDrop, isDragging, onDragOver, onDragLeave, onDragEnter }) {
  const handleClick = () => {
    document.getElementById('resume-upload-input').click();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onDrop(e.target.files[0]);
    }
  };

  return (
    <div 
      className={`dropzone${isDragging ? ' dropzone--dragging' : ''}`}
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onDragOver={onDragOver}
      onDragEnter={onDragEnter}
      onDragLeave={onDragLeave}
      onDrop={(e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
          onDrop(e.dataTransfer.files[0]);
        }
      }}
    >
      <input 
        type="file" 
        id="resume-upload-input" 
        accept=".pdf,.docx" 
        onChange={handleFileChange} 
        style={{ display: 'none' }} 
      />
      
      {/* Inline fallback for upload icon since SVG is complex */}
      <svg className="dropzone__icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>

      <p className="dropzone__title">Drop your resume here</p>
      <p className="dropzone__caption">PDF or DOCX &middot; max 5 MB</p>
    </div>
  );
}
