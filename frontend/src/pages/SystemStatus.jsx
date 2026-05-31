import { useState, useEffect, useCallback } from 'react'
import { getHealthAll } from '../api/health'
import './SystemStatus.css'

/* ------------------------------------------------------------------ */
/* Sub-components                                                        */
/* ------------------------------------------------------------------ */

function StatusDot({ state }) {
  const map = {
    ok:      { cls: 'dot-ok',    label: 'Online'     },
    error:   { cls: 'dot-error', label: 'Offline'    },
    loading: { cls: 'dot-idle pulse', label: 'Checking…' },
  }
  const { cls, label } = map[state] ?? map.loading
  return (
    <span className={`status-dot ${cls}`} aria-label={label} />
  )
}

function ServiceCard({ name, icon, description, state, detail }) {
  const badgeClass = state === 'ok' ? 'badge-ok' : state === 'error' ? 'badge-error' : 'badge-idle'
  const badgeLabel = state === 'ok' ? 'Connected' : state === 'error' ? 'Error' : 'Checking'

  return (
    <div className={`service-card card ${state === 'error' ? 'service-card--error' : ''}`}>
      <div className="service-card__header">
        <span className="service-card__icon" aria-hidden="true">{icon}</span>
        <div>
          <h3 className="service-card__name">{name}</h3>
          <p className="service-card__desc">{description}</p>
        </div>
        <div className="service-card__status">
          <StatusDot state={state} />
          <span className={`badge ${badgeClass}`}>{badgeLabel}</span>
        </div>
      </div>
      {detail && (
        <p className="service-card__detail">{detail}</p>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Main Page                                                             */
/* ------------------------------------------------------------------ */

const SERVICES_CONFIG = [
  {
    key: 'app',
    name: 'Application Server',
    icon: '⚡',
    description: 'FastAPI backend process',
    getState: (d) => (d?.status === 'ok' ? 'ok' : 'error'),
    getDetail: (d) => d?.version ? `Version ${d.version} · ${d.env}` : null,
  },
  {
    key: 'db',
    name: 'PostgreSQL',
    icon: '🗄️',
    description: 'Primary relational database',
    getState: (d) => (d?.db === 'connected' ? 'ok' : 'error'),
    getDetail: (d) => d?.detail ?? null,
  },
  {
    key: 'llm',
    name: 'Gemini LLM',
    icon: '🤖',
    description: 'Google Gemini AI model',
    getState: (d) => (d?.llm === 'connected' ? 'ok' : 'error'),
    getDetail: (d) => d?.model ? `Model: ${d.model}` : d?.detail ?? null,
  },
  {
    key: 'mcp',
    name: 'MongoDB MCP Server',
    icon: '🍃',
    description: 'MongoDB Atlas via MCP (partner integration)',
    getState: (d) => (d?.mcp === 'connected' ? 'ok' : 'error'),
    getDetail: (d) => {
      if (!d) return null
      if (d.collections?.length) return `Collections: ${d.collections.join(', ')}`
      if (d.note) return d.note
      return d.detail ?? null
    },
  },
]

export default function SystemStatus() {
  const [services, setServices] = useState(null)   // null = not fetched yet
  const [loading, setLoading]   = useState(true)
  const [lastChecked, setLastChecked] = useState(null)
  const [fetchError, setFetchError]   = useState(null)

  const fetchStatus = useCallback(async () => {
    setLoading(true)
    setFetchError(null)

    const { data, error } = await getHealthAll()

    if (error || !data) {
      setFetchError(error || 'Could not reach the backend. Is the server running?')
      setServices(null)
    } else {
      setServices(data)
    }

    setLastChecked(new Date())
    setLoading(false)
  }, [])

  // Fetch on mount
  useEffect(() => { fetchStatus() }, [fetchStatus])

  // Derive overall status
  const allOk =
    services &&
    SERVICES_CONFIG.every((s) => s.getState(services[s.key]) === 'ok')

  return (
    <div className="status-page page">
      {/* ---------- Header ---------- */}
      <div className="container">
        <div className="status-header">
          <div className="status-header__left">
            <div className="status-badge-large">
              <span className={`status-dot-large ${loading ? 'dot-idle pulse' : allOk ? 'dot-ok' : 'dot-error'}`} />
              <span className="status-badge-large__label">
                {loading ? 'Checking systems…' : allOk ? 'All Systems Operational' : 'Degraded — Some Services Offline'}
              </span>
            </div>
            <h1 className="status-title">System Status</h1>
            <p className="status-subtitle">
              Phase 0 — Foundation &amp; Environment Verification
            </p>
          </div>
          <button
            className="btn btn-ghost"
            onClick={fetchStatus}
            disabled={loading}
            id="refresh-status-btn"
            aria-label="Refresh status"
          >
            <span className={loading ? 'spin' : ''} aria-hidden="true">↻</span>
            {loading ? 'Checking…' : 'Refresh'}
          </button>
        </div>

        {/* ---------- Fatal Fetch Error ---------- */}
        {fetchError && (
          <div className="fetch-error card">
            <span aria-hidden="true">⚠️</span>
            <div>
              <strong>Cannot reach backend</strong>
              <p>{fetchError}</p>
              <p className="fetch-error__hint">
                Start the server: <code>cd backend &amp;&amp; uvicorn app.main:app --reload</code>
              </p>
            </div>
          </div>
        )}

        {/* ---------- Service Cards Grid ---------- */}
        <div className="services-grid">
          {SERVICES_CONFIG.map((svc) => {
            const raw = services?.[svc.key]
            const state = loading ? 'loading' : (raw ? svc.getState(raw) : 'error')
            const detail = raw ? svc.getDetail(raw) : null

            return (
              <ServiceCard
                key={svc.key}
                name={svc.name}
                icon={svc.icon}
                description={svc.description}
                state={state}
                detail={detail}
              />
            )
          })}
        </div>

        {/* ---------- Last Checked ---------- */}
        {lastChecked && (
          <p className="last-checked">
            Last checked: {lastChecked.toLocaleTimeString()}
          </p>
        )}
      </div>
    </div>
  )
}
