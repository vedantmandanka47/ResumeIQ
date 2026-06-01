import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import './StatusPage.css';

function StatusDot({ state }) {
  const map = {
    ok:      { cls: 'dot-ok',    label: 'Online' },
    error:   { cls: 'dot-error', label: 'Offline' },
    loading: { cls: 'dot-idle pulse', label: 'Checking…' },
  };
  const { cls, label } = map[state] ?? map.loading;
  return <span className={`status-dot ${cls}`} aria-label={label} />;
}

function ServiceCard({ name, state, message }) {
  return (
    <div className="service-card">
      <div className="service-card__header">
        <h3 className="label">{name}</h3>
        <StatusDot state={state} />
      </div>
      <p className="service-card__message text-sm text-secondary">
        {message || ' '}
      </p>
    </div>
  );
}

const SERVICES_CONFIG = [
  { key: 'app', name: 'Application Server' },
  { key: 'db',  name: 'PostgreSQL' },
  { key: 'llm', name: 'Gemini LLM' },
  { key: 'mcp', name: 'MongoDB MCP' },
];

export default function StatusPage() {
  const [statuses, setStatuses] = useState(
    SERVICES_CONFIG.reduce((acc, s) => ({ ...acc, [s.key]: { state: 'loading', message: '' } }), {})
  );

  const fetchStatus = useCallback(async () => {
    setStatuses(
      SERVICES_CONFIG.reduce((acc, s) => ({ ...acc, [s.key]: { state: 'loading', message: '' } }), {})
    );

    const promises = SERVICES_CONFIG.map(async (svc) => {
      try {
        const data = await api.health[svc.key]();
        let state = 'ok';
        let message = 'Connected';
        
        // Detailed checks per service
        if (svc.key === 'app' && data.status !== 'ok') state = 'error';
        if (svc.key === 'db' && data.db !== 'connected') state = 'error';
        if (svc.key === 'llm' && data.llm !== 'connected') state = 'error';
        if (svc.key === 'mcp' && data.mcp !== 'connected') state = 'error';

        if (state === 'error') message = data.detail || 'Service degraded';
        else if (svc.key === 'app' && data.version) message = `Version ${data.version}`;
        else if (svc.key === 'llm' && data.model) message = `Model: ${data.model}`;

        return { key: svc.key, state, message };
      } catch (err) {
        return { key: svc.key, state: 'error', message: err.message || 'Offline' };
      }
    });

    const results = await Promise.allSettled(promises);
    
    setStatuses((prev) => {
      const next = { ...prev };
      results.forEach(res => {
        if (res.status === 'fulfilled') {
          next[res.value.key] = { state: res.value.state, message: res.value.message };
        }
      });
      return next;
    });
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const serviceStates = Object.values(statuses).map(({ state }) => state);
  const summary = serviceStates.includes('loading')
    ? 'Checking service health...'
    : serviceStates.includes('error')
      ? 'Some services are unavailable'
      : 'All systems operational';

  return (
    <div className="page status-page">
      <div className="container">
        <div className="status-header">
          <h1 className="text-3xl">ResumeIQ Status</h1>
          <p className="text-secondary text-base">{summary}</p>
        </div>

        <div className="status-grid">
          {SERVICES_CONFIG.map(svc => (
            <ServiceCard 
              key={svc.key} 
              name={svc.name} 
              state={statuses[svc.key].state} 
              message={statuses[svc.key].message} 
            />
          ))}
        </div>
      </div>
    </div>
  );
}
