import '../../pages/RewritePage.css';

export default function SideBySide({ oldText, newText }) {
  return (
    <div className="side-by-side">
      <div className="sbs-pane">
        <h3 className="label sbs-pane__header">Original</h3>
        <div className="sbs-pane__content mono text-sm text-secondary">
          {oldText}
        </div>
      </div>
      <div className="sbs-pane">
        <h3 className="label sbs-pane__header">Rewritten</h3>
        <div className="sbs-pane__content mono text-sm text-primary">
          {newText}
        </div>
      </div>
    </div>
  );
}
