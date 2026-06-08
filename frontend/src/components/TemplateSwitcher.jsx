import { useEffect, useState } from 'react';
import { api } from '../api/client';

export function TemplateSwitcher({ selectedId, onChange }) {
  const [templates, setTemplates] = useState([]);

  useEffect(() => {
    api.resume.templates()
      .then(setTemplates)
      .catch(console.error);
  }, []);

  if (!templates.length) return null;

  return (
    <div className="template-switcher">
      {templates.map((template) => (
        <button
          key={template.id}
          type="button"
          onClick={() => onChange(template.id)}
          className={`template-switcher__btn${selectedId === template.id ? ' template-switcher__btn--active' : ''}`}
          title={template.description}
        >
          {template.name}
        </button>
      ))}
    </div>
  );
}
