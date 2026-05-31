import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAnalysis } from '../hooks/useAnalysis';
import { useSession } from '../hooks/useSession';
import DropZone from '../components/upload/DropZone';
import FileChip from '../components/upload/FileChip';
import TextPreview from '../components/upload/TextPreview';
import ErrorBlock from '../components/common/ErrorBlock';
import Button from '../components/common/Button';
import './UploadPage.css';

export default function UploadPage() {
  const navigate = useNavigate();
  const { clearAll } = useAnalysis();
  const { setSessionId } = useSession();
  
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState(null);
  
  // Upload state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null); // { session_id, preview, filename }
  
  // Analyze state
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // --- Drag events ---
  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  }, [isDragging]);

  const handleDrop = useCallback((droppedFile) => {
    setIsDragging(false);
    setError(null);
    setUploadResult(null);

    const extension = droppedFile.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx'].includes(extension)) {
      setFile(null);
      setError('Unsupported file type. Upload a PDF or DOCX resume.');
      return;
    }

    // Validate size (5MB = 5 * 1024 * 1024 bytes)
    if (droppedFile.size > 5 * 1024 * 1024) {
      setFile(null);
      setError('File is too large. Maximum size is 5 MB.');
      return;
    }

    setFile(droppedFile);
  }, []);

  // --- Actions ---
  const handleReset = () => {
    setFile(null);
    setError(null);
    setUploadResult(null);
  };

  const handleUploadSubmit = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);

    try {
      const data = await api.resume.upload(file);
      clearAll();
      setUploadResult(data);
      setSessionId(data.session_id);
    } catch (err) {
      setError(err.message || 'Failed to upload and parse resume.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleAnalyzeSubmit = async () => {
    if (!uploadResult?.session_id) return;
    setIsAnalyzing(true);
    // Note: We don't call analyze here, we just navigate to the analysis page.
    // The analysis page calls it on mount.
    navigate(`/analysis/${uploadResult.session_id}`);
  };

  return (
    <div className="page upload-page">
      <div className="container">
        
        <div className="upload-header">
          <h1 className="text-3xl">Analyze Your Resume</h1>
          <p className="text-secondary text-lg">Upload your resume to get an AI-powered multidimensional score and improvement roadmap.</p>
        </div>

        <div className="upload-container card">
          {!file && (
            <DropZone 
              onDrop={handleDrop}
              isDragging={isDragging}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
            />
          )}

          {file && !uploadResult && (
            <div className="upload-file-state">
              <FileChip file={file} onRemove={handleReset} />
              <Button 
                onClick={handleUploadSubmit} 
                loading={isUploading}
                style={{ width: '100%', marginTop: '24px' }}
              >
                Upload &amp; Extract Text
              </Button>
            </div>
          )}

          {uploadResult && (
            <TextPreview 
              text={uploadResult.preview} 
              onConfirm={handleAnalyzeSubmit} 
              onReset={handleReset}
              isAnalyzing={isAnalyzing}
            />
          )}
        </div>

        {error && (
          <ErrorBlock message={error} className="upload-error" />
        )}

      </div>
    </div>
  );
}
