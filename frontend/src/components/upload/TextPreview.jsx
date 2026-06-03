import Button from '../common/Button';

export default function TextPreview({ text, onConfirm, onGenerate, onReset, isAnalyzing, isGenerating }) {
  const preview = text || '';

  return (
    <div className="text-preview">
      <div className="text-preview__header">
        <span className="label">Parsed text preview</span>
        <span className="text-sm text-secondary">Verify this looks correct before continuing</span>
      </div>

      <div className="text-preview__content mono">
        {preview.length > 500 ? preview.substring(0, 500) + '...' : preview}
      </div>

      <div className="text-preview__actions">
        <Button onClick={onConfirm} loading={isAnalyzing}>Analyze &rarr;</Button>
        <Button variant="secondary" onClick={onGenerate} loading={isGenerating}>Generate Resume</Button>
        <Button variant="text" onClick={onReset} disabled={isAnalyzing || isGenerating}>Wrong file</Button>
      </div>
    </div>
  );
}
