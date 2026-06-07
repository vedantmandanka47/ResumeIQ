import { useState, useEffect } from 'react';

const DEFAULT_STEPS = [
  { key: 'parse',    label: 'Parsing document…'     },
  { key: 'extract',  label: 'Extracting content…'   },
  { key: 'score',    label: 'Scoring dimensions…'   },
  { key: 'insights', label: 'Generating insights…'  },
  { key: 'done',     label: 'Finalising report…'    },
];

export default function StepProgress({ steps = DEFAULT_STEPS, intervalMs = 2800, className = '' }) {
  const [activeIdx, setActiveIdx] = useState(0);

  useEffect(() => {
    if (activeIdx >= steps.length - 1) return;
    const t = setTimeout(() => setActiveIdx((i) => Math.min(i + 1, steps.length - 1)), intervalMs);
    return () => clearTimeout(t);
  }, [activeIdx, steps.length, intervalMs]);

  return (
    <div className={`step-progress ${className}`} role="status" aria-label="Loading progress">
      {steps.map((step, idx) => {
        const state =
          idx < activeIdx  ? 'done'
          : idx === activeIdx ? 'active'
          : '';
        return (
          <div key={step.key} className={`step-item step-item--${state || 'pending'}`}>
            <span className="step-dot" aria-hidden="true" />
            <span>{step.label}</span>
          </div>
        );
      })}
    </div>
  );
}
