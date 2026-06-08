# ResumeIQ

**ResumeIQ** is an AI-powered resume analysis and generation app: upload a resume, get multidimensional analysis, company-fit research, AI rewrite, improvement roadmap, and DOCX/PDF output from templates.

## Tech stack

| Layer | Technology |
|--------|------------|
| Frontend | React 18, Vite, React Router |
| Backend | FastAPI, Uvicorn, SQLAlchemy (async), Alembic |
| Database | PostgreSQL (`asyncpg`) |
| AI | Google Gemini (`google-genai`) |
| Integrations | MongoDB Atlas (MCP), Google Drive (optional) |
| Templates | `docxtpl` (Jinja2 DOCX) |

---

## Prerequisites

- **Python 3.12+** (3.11+ may work; project is tested on 3.12)
- **Node.js 18+** and npm
- **PostgreSQL** running locally or remote
- **Google Gemini API key** ([Google AI Studio](https://aistudio.google.com/apikey))
- Optional: **LibreOffice** or **Microsoft Word** (for PDF conversion on Windows)
- Optional: MongoDB Atlas + MCP URL, Google Drive OAuth (for save/export features)

---

## Quick start

### 1. Clone and configure environment

```powershell
# From the repo root
copy backend\.env.example backend\.env
# Edit backend\.env — at minimum set DATABASE_URL and GOOGLE_API_KEY
```

**Required for startup**

| Variable | Example |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@localhost:5432/resumeiq` |
| `GOOGLE_API_KEY` | Your Gemini API key |

**Optional** (app starts without these; related routes may fail until configured)

- `MONGODB_MCP_SERVER_URL`, `MONGODB_ATLAS_URI` — history, benchmark, MCP health
- `GOOGLE_DRIVE_*` — Drive export
- `GEMINI_RESUME_MODEL` / `GEMINI_MODEL` — default `gemini-2.5-flash`

### 2. Database

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
```

> **Important:** Migration `0002` creates `structured_resumes` and `generated_resumes`. Without it, DOCX preview/generation returns errors.

### 3. DOCX templates (first-time setup)

```powershell
# Still in backend/ — use the venv Python (not plain `python`, which may be Python 2)
.\.venv\Scripts\python.exe create_canonical_docx_templates.py
```

This creates `backend/template/canonical_minimalist.docx` and `canonical_modern_blue.docx`.

### 4. Start backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or use the helper script:

```powershell
cd backend
.\scripts\start-api.ps1
```

Keep this terminal open. The frontend Vite proxy expects the API at **http://127.0.0.1:8000**.

- API: http://localhost:8000  
- Swagger: http://localhost:8000/docs  

### 5. Start frontend

```powershell
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173  

**Development API routing:** Leave `VITE_API_BASE_URL` empty (see `frontend/.env.example`). Vite proxies `/health`, `/resume`, `/generate`, etc. to port 8000. If you set `VITE_API_BASE_URL=http://localhost:8000`, ensure `ALLOWED_ORIGINS` in backend `.env` includes `http://localhost:5173`.

---

## Application flow

1. **Upload** (`/`) — PDF/DOCX → `POST /resume/upload`
2. **Analysis** (`/analysis/:sessionId`) — `POST /resume/{id}/analyze`
3. **Rewrite** (`/rewrite/:sessionId`) — `POST /resume/{id}/rewrite` + DOCX preview via `POST /resume/render`
4. **Generate** (`/generate/:sessionId`) — `POST /generate` + template switch + PDF preview
5. **Roadmap** (`/roadmap/:sessionId`) — `POST /resume/{id}/roadmap`
6. **Status** (`/status`) — health checks

See [DEMO.md](DEMO.md) for curl examples.

---

## Pre-run review — bugs found and fixes applied

Issues identified before running, and what was changed:

### Critical / showstoppers

| # | Issue | Impact | Fix |
|---|--------|--------|-----|
| 1 | `backend/app/routers/__init__.py` used absolute imports while the package was loading | Possible `ImportError` on startup | Switched to relative imports: `from . import generation, health, resume` |
| 2 | `validate_env()` required MongoDB + Google Drive at startup | Server refused to start without full hackathon integrations | Only `DATABASE_URL` + `GOOGLE_API_KEY` required; optional vars log warnings |
| 3 | Missing Alembic migration `0002` | `structured_resumes` table missing → 500 on DOCX preview | Documented; run `alembic upgrade head` |
| 4 | Missing DOCX template files | Generation/render 404 | Documented; run `create_canonical_docx_templates.py`; startup warns if none found |
| 5 | `RewritePage` sent `{ model: 'gemini-1.5-pro' }` — not in `RewriteRequest` schema | Ignored by API; confusing | Removed invalid field; sends `{}` |

### Logic / UX

| # | Issue | Impact | Fix |
|---|--------|--------|-----|
| 6 | `cache_hit` on template switch implied full cache hit | Misleading status on Generate page | `template_switch` + `structured_cache_hit` fields (see prior bugfix pass) |
| 7 | Health returned `llm: "ready"` but UI expected `"connected"` | Status page showed LLM offline | Normalized health payloads; StatusPage accepts `ready`/`ok`/`connected` |
| 8 | `pdf_available` set when DB had path but file expired | Broken preview/download links | Disk check before setting availability flags |
| 9 | `GEMINI_MODEL` vs `GEMINI_RESUME_MODEL` mismatch | Wrong model if only one env var set | `gemini.py` reads both; `.env.example` documents both |

### Environment / ops (documented, not code defects)

| # | Issue | Mitigation |
|---|--------|------------|
| 10 | PDF conversion needs LibreOffice or MS Word on Windows | DOCX still works; PDF preview may be unavailable (`pdf_error` in API) |
| 11 | Root `.env` `VITE_*` vars not read by Vite | Use `frontend/.env.local` or rely on Vite proxy |
| 12 | Virtualenv should live in `backend/.venv` | README paths use `backend/.venv` |

---

## Recommended testing order

Run in this sequence so failures are easy to localize.

### Phase 0 — Infrastructure

1. PostgreSQL reachable; database `resumeiq` exists.
2. `cd backend && alembic upgrade head` — succeeds.
3. `python create_canonical_docx_templates.py` — two `.docx` files under `backend/template/`.
4. `uvicorn app.main:app --reload` — no import or env errors.
5. `curl http://localhost:8000/health` → `{"status":"ok",...}`.
6. `curl http://localhost:8000/health/db` → `{"db":"connected"}`.
7. `curl http://localhost:8000/health/llm` → `{"llm":"connected"}` (needs valid `GOOGLE_API_KEY`).
8. `npm run dev` in `frontend/` — http://localhost:5173 loads.
9. **Status page** (`/status`) — all core services green.

### Phase 1 — Core resume pipeline

10. **Upload UI** — upload PDF/DOCX → preview text appears.
11. `POST /resume/upload` (via Swagger) — returns `session_id`.
12. **Analysis page** — open `/analysis/{sessionId}` → score and dimensions render.
13. `POST /resume/{id}/analyze` — 200 with JSON analysis.

### Phase 2 — Rewrite + DOCX

14. **Rewrite page** — `/rewrite/{sessionId}` → side-by-side text + change log.
15. `GET /resume/{id}/structured-resume` — 404 first time is OK.
16. `POST /generate` — creates structured JSON + files (may take 20–30s first run).
17. **DOCX preview** on Rewrite page — template switcher + rendered preview.
18. `POST /resume/render` — returns binary DOCX.

### Phase 3 — Generation UI

19. **Generate page** — `/generate/{sessionId}` → template dropdown, DOCX download.
20. `POST /change-template` — new files; status shows “Re-rendered DOCX/PDF…”.
21. `GET /download/{id}?format=docx` — file downloads.
22. `GET /preview/{id}` — PDF iframe (if conversion succeeded).

### Phase 4 — Optional integrations

23. Company research on Analysis page (needs MCP + Gemini search).
24. `POST /resume/{id}/roadmap`.
25. `POST /resume/{id}/save` + benchmark (needs MongoDB).
26. `POST /resume/{id}/export/drive` (needs Google Drive env vars).

### Automated backend test

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest tests/test_template_engine.py -q
```

---

## Project layout

```
ResumeIQ/
├── backend/
│   ├── app/              # FastAPI app (routers, services, models)
│   ├── alembic/          # DB migrations
│   ├── template/         # DOCX templates + template_metadata.json
│   ├── generated/        # Generated docx/pdf output
│   ├── tests/
│   ├── create_canonical_docx_templates.py
│   └── requirements.txt
├── frontend/
│   └── src/              # React pages and components
├── DEMO.md
└── Bugfixes.md           # Historical bugfix notes
```

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|----------------|--------|
| Vite `proxy error` / `ECONNREFUSED` on `/resume/upload` | Backend not running on port 8000 | Start uvicorn in `backend/` (see step 4) |
| `FastAPIError: Invalid args for response field` on startup | Fixed in code — pull latest | Restart backend after update |
| `SyntaxError` running template script | Used `python` instead of Python 3 | Run `.\.venv\Scripts\python.exe create_canonical_docx_templates.py` |
| Server won’t start — missing env | No `.env` in `backend/` | Copy `backend/.env.example` → `backend/.env` |
| `relation "structured_resumes" does not exist` | Migration not applied | `alembic upgrade head` |
| DOCX preview “Something went wrong” | Old backend code or missing migration | Restart API; run migrations |
| Generate returns 404 template | No `.docx` in `template/` | Run `create_canonical_docx_templates.py` |
| LLM health offline | Bad/missing API key | Check `GOOGLE_API_KEY` |
| MCP/Drive features fail | Optional env not set | Configure or ignore optional routes |
| PDF preview missing | No LibreOffice/Word | Use DOCX download; check `pdf_error` in response |
| Frontend API errors | Proxy bypass + CORS | Clear `VITE_API_BASE_URL` or fix `ALLOWED_ORIGINS` |

---

## Documentation

- [DEMO.md](DEMO.md) — evaluator quickstart and curl commands  
- [Bugfixes.md](Bugfixes.md) — detailed stability improvements log  
- API docs: http://localhost:8000/docs (when backend is running)

## License / hackathon

Built for DevPost “Building Agents for Real-World Challenges” — MongoDB partner track (session persistence via MCP).
