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
  const [lastChecked, setLastChecked] = useState(null);

  const fetchStatus = useCallback(async () => {
    setStatuses(
      SERVICES_CONFIG.reduce((acc, s) => ({ ...acc, [s.key]: { state: 'loading', message: '' } }), {})
    );

    const isConnected = (value) => {
      const normalized = String(value ?? '').toLowerCase();
      return normalized === 'connected' || normalized === 'ready' || normalized === 'ok';
    };

    const promises = SERVICES_CONFIG.map(async (svc) => {
      try {
        const data = await api.health[svc.key]();
        let state = 'ok';
        let message = 'Connected';

        if (svc.key === 'app') {
          if (!isConnected(data.status)) state = 'error';
        } else if (svc.key === 'db') {
          if (!isConnected(data.db)) state = 'error';
        } else if (svc.key === 'llm') {
          if (!isConnected(data.llm)) state = 'error';
        } else if (svc.key === 'mcp') {
          if (!isConnected(data.mcp)) state = 'error';
        }

        if (state === 'error') {
          message = data.detail || data.error || 'Service degraded';
        } else if (svc.key === 'app' && data.version) {
          message = `Version ${data.version}`;
        } else if (svc.key === 'llm' && data.model) {
          message = `Model: ${data.model}`;
        }

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

    setLastChecked(new Date());
  }, []);

  useEffect(() => {
    fetchStatus();                                    // immediate on mount

    const timer = setInterval(fetchStatus, 30_000);  // every 30 s

    return () => clearInterval(timer);                // clean up on unmount
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
          {lastChecked && (
            <p className="text-muted text-sm" style={{ marginTop: 4 }}>
              Last checked {lastChecked.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </p>
          )}
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
