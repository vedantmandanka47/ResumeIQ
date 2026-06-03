import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import Button from '../components/common/Button';
import ErrorBlock from '../components/common/ErrorBlock';
import Spinner from '../components/common/Spinner';
import './GeneratePage.css';

export default function GeneratePage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const requestInFlight = useRef(false);
  const initialGenerationStarted = useRef(false);

  const [generation, setGeneration] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSwitching, setIsSwitching] = useState(false);
  const [isDownloadingDocx, setIsDownloadingDocx] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [error, setError] = useState(null);

  const generate = useCallback(async () => {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.generation.generate({
        session_id: sessionId,
        template_id: selectedTemplate || null,
        job_description: null,
        rewrite_instructions: null,
      });
      setGeneration(data);
      setTemplates(data.templates || []);
      setSelectedTemplate(data.template_id);
    } catch (err) {
      setError(err.message || 'Failed to generate resume.');
    } finally {
      requestInFlight.current = false;
      setIsLoading(false);
    }
  }, [sessionId, selectedTemplate]);

  useEffect(() => {
    if (initialGenerationStarted.current) return;
    initialGenerationStarted.current = true;
    generate();
  }, [generate]);

  const handleTemplateChange = async (event) => {
    const templateId = event.target.value;
    setSelectedTemplate(templateId);
    if (!generation || templateId === generation.template_id || isSwitching) return;

    setIsSwitching(true);
    setError(null);
    try {
      const data = await api.generation.changeTemplate({
        generation_id: generation.id,
        template_id: templateId,
      });
      setGeneration(data);
      setTemplates(data.templates || templates);
      setSelectedTemplate(data.template_id);
    } catch (err) {
      setError(err.message || 'Failed to switch template.');
      setSelectedTemplate(generation.template_id);
    } finally {
      setIsSwitching(false);
    }
  };

  const downloadDocx = async () => {
    if (!generation || isDownloadingDocx) return;
    setIsDownloadingDocx(true);
    try {
      await api.generation.downloadDocx(generation.id);
    } catch (err) {
      setError(err.message || 'Failed to download DOCX.');
    } finally {
      setIsDownloadingDocx(false);
    }
  };

  const downloadPdf = async () => {
    if (!generation || !generation.pdf_available || isDownloadingPdf) return;
    setIsDownloadingPdf(true);
    try {
      await api.generation.downloadPdf(generation.id);
    } catch (err) {
      setError(err.message || 'Failed to download PDF.');
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  if (isLoading) {
    return (
      <div className="page generate-page generate-page--loading">
        <Spinner size={32} />
        <p className="text-secondary mt-4">Generating your template-ready resume...</p>
      </div>
    );
  }

  return (
    <div className="page generate-page">
      <div className="container container--wide">
        <div className="generate-header">
          <div>
            <h1 className="text-3xl">Generated Resume</h1>
            <p className="text-secondary">
              Choose a template, preview the PDF when available, and download DOCX or PDF.
            </p>
          </div>
          <Button variant="secondary" onClick={() => navigate(`/analysis/${sessionId}`)}>
            Analyze Instead
          </Button>
        </div>

        {error && <ErrorBlock message={error} onRetry={generate} />}

        {generation && (
          <>
            <div className="generate-toolbar card">
              <label className="template-picker">
                <span>Template</span>
                <select value={selectedTemplate} onChange={handleTemplateChange} disabled={isSwitching}>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="generate-status">
                {generation.template_switch
                  ? 'Re-rendered DOCX/PDF with the selected template'
                  : generation.structured_cache_hit
                    ? 'Used cached structured resume'
                    : 'Created new structured resume'}
                {isSwitching && ' · switching template...'}
              </div>
              <div className="generate-actions">
                <Button
                  onClick={downloadDocx}
                  loading={isDownloadingDocx || isSwitching}
                  disabled={!generation.docx_available}
                >
                  Download DOCX
                </Button>
                <Button
                  variant="secondary"
                  onClick={downloadPdf}
                  loading={isDownloadingPdf || isSwitching}
                  disabled={!generation.pdf_available}
                >
                  Download PDF
                </Button>
              </div>
            </div>

            {generation.files_expired && (
              <ErrorBlock
                message="Generated files have expired. Regenerate the resume to download or preview again."
                onRetry={generate}
              />
            )}

            {!generation.pdf_available && !generation.files_expired && (
              <ErrorBlock
                message={
                  generation.pdf_error
                    || 'PDF preview is unavailable. DOCX download is still ready.'
                }
              />
            )}

            {generation.pdf_available && (
              <div className="preview-shell card">
                <iframe
                  title="Generated resume preview"
                  src={api.generation.previewUrl(generation.id)}
                  className="preview-frame"
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
