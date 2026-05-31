/**
 * ResumeIQ — Health API Client
 * All calls to /health/* endpoints go through here.
 * Uses the Vite dev proxy so no absolute URL is needed in development.
 */

const BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * Generic fetch wrapper that always returns { data, error, status }.
 * Never throws — callers check the error field instead.
 */
async function apiFetch(path) {
  try {
    const res = await fetch(`${BASE}${path}`)
    const data = await res.json()
    return { data, error: null, status: res.status }
  } catch (err) {
    return { data: null, error: err.message || 'Network error', status: 0 }
  }
}

/** GET /health — app liveness */
export const getHealth = () => apiFetch('/health')

/** GET /health/db — PostgreSQL check */
export const getHealthDb = () => apiFetch('/health/db')

/** GET /health/llm — Gemini check */
export const getHealthLlm = () => apiFetch('/health/llm')

/** GET /health/mcp — MongoDB MCP check */
export const getHealthMcp = () => apiFetch('/health/mcp')

/**
 * GET /health/all — all checks in one round-trip.
 * Returns combined payload: { app, db, llm, mcp }
 */
export const getHealthAll = () => apiFetch('/health/all')
