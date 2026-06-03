import { useEffect, useRef, useState } from 'react';
import { renderAsync } from 'docx-preview';
import { api } from '../api/client';

export function ResumeDocxPreview({ resumeData, templateId }) {
  const containerRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!resumeData || !templateId) return undefined;

    const fetchAndRender = async () => {
      setLoading(true);
      setError(null);

      try {
        const arrayBuffer = await api.resume.renderDocx(resumeData, templateId);

        if (containerRef.current) {
          containerRef.current.innerHTML = '';
          await renderAsync(arrayBuffer, containerRef.current, undefined, {
            className: 'docx-preview',
            inWrapper: true,
            ignoreWidth: false,
            ignoreHeight: false,
            ignoreFonts: false,
            breakPages: true,
            useBase64URL: true,
          });
        }
      } catch (err) {
        setError(err.message ?? 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchAndRender();
    return undefined;
  }, [resumeData, templateId]);

  return (
    <div className="resume-docx-preview">
      {loading && (
        <div className="resume-docx-preview__overlay">
          <span className="text-secondary">Rendering resume…</span>
        </div>
      )}
      {error && (
        <div className="resume-docx-preview__error">
          {error}
        </div>
      )}
      <div ref={containerRef} className="resume-docx-preview__container docx-container" />
    </div>
  );
}
