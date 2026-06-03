/**
 * ResumeIQ — Unified API Client
 * Every fetch() call in the app lives here. Components import from this file only.
 * Uses the Vite dev proxy so no absolute URL is needed in development.
 */

const BASE = import.meta.env.VITE_API_BASE_URL || '';

async function parseApiError(res) {
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const err = await res.json().catch(() => ({}));
    return {
      message: err.detail || err.error || `Request failed (${res.status})`,
      code: err.code || String(res.status),
    };
  }
  const text = await res.text().catch(() => '');
  const trimmed = text.trim();
  return {
    message: trimmed || `Request failed (${res.status})`,
    code: String(res.status),
  };
}

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
    const { message, code } = await parseApiError(res);
    const error = new Error(message);
    error.code = code;
    throw error;
  }

  return res.json();
}

function GET(path)              { return request('GET', path); }
function POST(path, body)       { return request('POST', path, body); }
function POST_FILE(path, file)  { return request('POST', path, file, true); }

async function POST_BINARY(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const { message, code } = await parseApiError(res);
    const error = new Error(message);
    error.code = code;
    throw error;
  }
  return res.arrayBuffer();
}

async function DOWNLOAD(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const { message, code } = await parseApiError(res);
    const error = new Error(message);
    error.code = code;
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
    rewriteDownload: (id)        => DOWNLOAD(`/resume/${id}/rewrite/download/docx`),
    roadmap:         (id)        => POST(`/resume/${id}/roadmap`, {}),
    save:            (id)        => POST(`/resume/${id}/save`, {}),
    history:         (id)        => GET(`/resume/${id}/history`),
    benchmark:       ()          => GET('/resume/benchmark'),
    exportDrive:     (id)        => POST(`/resume/${id}/export/drive`, {}),
    templates:       ()          => GET('/resume/templates'),
    renderDocx:      (resumeData, templateId) =>
      POST_BINARY('/resume/render', { resume_data: resumeData, template_id: templateId }),
    renderDocxDownload: (resumeData, templateId) =>
      POST_BINARY('/resume/render/download', { resume_data: resumeData, template_id: templateId }),
    structuredResume: (id) => GET(`/resume/${id}/structured-resume`),
  },
  generation: {
    templates:       ()          => GET('/templates'),
    generate:        (body)      => POST('/generate', {
      session_id: body.session_id,
      template_id: body.template_id ?? null,
      job_description: body.job_description ?? null,
      rewrite_instructions: body.rewrite_instructions ?? null,
    }),
    changeTemplate:  (body)      => POST('/change-template', body),
    downloadDocx:    (id)        => DOWNLOAD(`/download/${id}?format=docx`),
    downloadPdf:     (id)        => DOWNLOAD(`/download/${id}?format=pdf`),
    previewUrl:      (id)        => `${BASE}/preview/${id}`,
  },
};
