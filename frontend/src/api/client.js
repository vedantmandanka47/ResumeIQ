/**
 * ResumeIQ — Unified API Client
 * Every fetch() call in the app lives here. Components import from this file only.
 * Uses the Vite dev proxy so no absolute URL is needed in development.
 */

const BASE = import.meta.env.VITE_API_BASE_URL || '';

async function request(method, path, body, isFile = false) {
  const opts = { method, headers: {} };

  if (isFile) {
    const fd = new FormData();
    fd.append('file', body);
    opts.body = fd;
  } else if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(`${BASE}${path}`, opts);

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const error = new Error(err.detail || err.error || `Request failed (${res.status})`);
    error.code = err.code || String(res.status);
    throw error;
  }

  return res.json();
}

function GET(path)              { return request('GET', path); }
function POST(path, body)       { return request('POST', path, body); }
function POST_FILE(path, file)  { return request('POST', path, file, true); }

async function DOWNLOAD(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const error = new Error('Download failed');
    error.code = String(res.status);
    throw error;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '';
  const cd = res.headers.get('content-disposition');
  if (cd) {
    const match = cd.match(/filename="?([^"]+)"?/);
    if (match) a.download = match[1];
  }
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const api = {
  health: {
    app:    () => GET('/health'),
    status: () => GET('/health'),
    db:     () => GET('/health/db'),
    llm:    () => GET('/health/llm'),
    mcp:    () => GET('/health/mcp'),
  },
  resume: {
    upload:          (file)       => POST_FILE('/resume/upload', file),
    get:             (id)        => GET(`/resume/${id}`),
    analyze:         (id, body)  => POST(`/resume/${id}/analyze`, body),
    analyzeCompany:  (id, body)  => POST(`/resume/${id}/analyze/company`, body),
    rewrite:         (id, body)  => POST(`/resume/${id}/rewrite`, body),
    rewriteDownload: (id)        => DOWNLOAD(`/resume/${id}/rewrite/download`),
    roadmap:         (id)        => POST(`/resume/${id}/roadmap`, {}),
    save:            (id)        => POST(`/resume/${id}/save`, {}),
    history:         (id)        => GET(`/resume/${id}/history`),
    benchmark:       ()          => GET('/resume/benchmark'),
    exportDrive:     (id)        => POST(`/resume/${id}/export/drive`, {}),
  },
};
