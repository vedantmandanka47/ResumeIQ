# ResumeIQ

<div align="center">

![ResumeIQ Logo](frontend/src/assets/Logo.png)

**AI-powered resume intelligence — analyze, rewrite, and generate job-ready resumes in minutes.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?style=flat-square&logo=google)](https://aistudio.google.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org)
[![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-MCP-47A248?style=flat-square&logo=mongodb)](https://www.mongodb.com/atlas)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

## Overview

ResumeIQ is a full-stack AI agent application that transforms how job seekers optimize their resumes. Upload a PDF or DOCX resume and receive:

- **Multi-dimensional AI scoring** across 7 professional dimensions
- **Targeted AI rewrite** with tracked change log
- **Company-fit research** powered by Gemini's grounded web search
- **Personalized improvement roadmap** with actionable milestones
- **Professional DOCX/PDF export** from polished templates
- **Google Drive export** of rewritten resume + roadmap

Built for the DevPost *"Building Agents for Real-World Challenges"* hackathon — **MongoDB partner track** (session persistence via MCP).

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite, React Router 6 |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy (async) |
| **Database** | PostgreSQL (`asyncpg`), Alembic migrations |
| **AI** | Google Gemini 2.5 Flash (`google-genai`) |
| **Integrations** | MongoDB Atlas (MCP), Google Drive API (OAuth2) |
| **Document Engine** | `docxtpl` (Jinja2 DOCX templates), `docx2pdf` |
| **Rate Limiting** | SlowAPI (optional Redis backend) |

---

## Features

### 📊 Multi-Dimensional Analysis
Scores your resume across 7 dimensions — ATS Compatibility, Impact & Quantification, Skill Relevance, Language & Authenticity, Structure & Readability, Completeness, and Competitive Standing — with a fresher-mode for entry-level candidates.

### ✍️ AI-Powered Rewrite
Rewrites your resume for a target role with a side-by-side comparison and full change log. Optionally accepts a job description for precision targeting.

### 🏢 Company Fit Research
Grounded company analysis using Gemini's Google Search tool — surfaces hiring signals, culture fit indicators, and skill gaps vs. the target employer.

### 🗺️ Improvement Roadmap
Generates a prioritized, time-boxed action plan to close your skill and experience gaps.

### 📄 Template-Based Generation
Generates a structured resume from your content and renders it into professionally designed DOCX templates (Minimalist / Modern Blue). Download as DOCX or preview as PDF.

### ☁️ Google Drive Export
Exports your rewritten resume and roadmap directly to a new Google Doc in your Drive.

### 🕒 Session History
Stores analysis history via MongoDB Atlas MCP, with benchmarking against past sessions.

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.12+ |
| Node.js | 18+ |
| PostgreSQL | 14+ |
| Google Gemini API key | — |
| MongoDB Atlas URI *(optional)* | — |
| LibreOffice *(optional, for PDF)* | — |

---

## Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/your-username/ResumeIQ.git
cd ResumeIQ

# Copy environment files
cp backend/.env.example backend/.env
# Edit backend/.env — set DATABASE_URL and GOOGLE_API_KEY at minimum
```

**Required environment variables:**

| Variable | Example |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@localhost:5432/resumeiq` |
| `GOOGLE_API_KEY` | Your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) |

**Optional (app starts without these; related features degrade gracefully):**

| Variable | Feature |
|----------|---------|
| `MONGODB_MCP_SERVER_URL` | History, benchmark, MCP health |
| `MONGODB_ATLAS_URI` | Session persistence |
| `GOOGLE_DRIVE_*` | Drive export |
| `GEMINI_RESUME_MODEL` | Override default `gemini-2.5-flash` |

### 2. Database Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.\.venv\Scripts\Activate.ps1     # Windows PowerShell

pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

### 3. Generate DOCX Templates *(first-time only)*

```bash
# Still in backend/ with venv active
python create_canonical_docx_templates.py
# Creates: backend/template/canonical_minimalist.docx
#          backend/template/canonical_modern_blue.docx
```

### 4. Start Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API: http://localhost:8000  
Swagger UI: http://localhost:8000/docs

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

> **Tip:** Leave `VITE_API_BASE_URL` empty in `frontend/.env`. Vite proxies all API calls to port 8000 automatically.

---

## Application Flow

```
Upload (/upload)
  └─► POST /resume/upload → session_id

Analysis (/analysis/:sessionId)
  └─► POST /resume/{id}/analyze → 7-dimension score

Rewrite (/rewrite/:sessionId)
  └─► POST /resume/{id}/rewrite → side-by-side diff + DOCX preview

Generate (/generate/:sessionId)
  └─► POST /generate → structured JSON → DOCX/PDF templates

Roadmap (/roadmap/:sessionId)
  └─► POST /resume/{id}/roadmap → milestone action plan

Company Research (embedded in Analysis)
  └─► POST /resume/{id}/company → Gemini grounded search
```

---

## API Reference

Full interactive docs available at http://localhost:8000/docs when the backend is running.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/resume/upload` | Upload PDF/DOCX, create session |
| `POST` | `/resume/{id}/analyze` | Run multi-dimensional analysis |
| `POST` | `/resume/{id}/rewrite` | AI rewrite for target role |
| `POST` | `/resume/{id}/roadmap` | Generate improvement roadmap |
| `POST` | `/resume/{id}/company` | Company-fit research |
| `POST` | `/resume/{id}/cover-letter` | Generate cover letter |
| `POST` | `/generate` | Structured resume generation |
| `POST` | `/resume/render` | Render DOCX from template |
| `GET`  | `/resume/{id}/download` | Download DOCX/PDF |
| `POST` | `/resume/{id}/save` | Persist to MongoDB |
| `POST` | `/resume/{id}/export/drive` | Export to Google Drive |
| `GET`  | `/health` | Liveness check |
| `GET`  | `/health/db` | Database health |
| `GET`  | `/health/llm` | Gemini LLM health |
| `GET`  | `/health/mcp` | MongoDB MCP health |

---

## Project Structure

```
ResumeIQ/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # Settings & env validation
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── middleware/          # Rate limiter, input sanitizer
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── routers/             # health, resume, generation
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   └── services/
│   │       ├── agent/           # Gemini agents (analyzer, rewriter, etc.)
│   │       │   └── prompts/     # Prompt templates
│   │       ├── docx_builder.py  # DOCX rendering engine
│   │       └── file_manager.py  # File lifecycle management
│   ├── alembic/                 # DB migration versions
│   ├── template/                # DOCX templates + metadata
│   ├── tests/
│   ├── create_canonical_docx_templates.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/client.js        # Axios API client
│       ├── components/          # Reusable UI components
│       ├── pages/               # Route-level page components
│       └── hooks/               # Custom React hooks
├── DEMO.md                      # Evaluator quickstart + curl commands
└── Bugfixes.md                  # Stability improvements log
```

---

## Testing

### Backend Unit Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/test_template_engine.py -q
```

### Manual Integration Test Sequence

**Phase 0 — Infrastructure**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/llm
```

**Phase 1 — Core Pipeline**
```bash
# Upload a resume
curl -X POST http://localhost:8000/resume/upload \
  -F "file=@/path/to/resume.pdf"
# Returns: { "session_id": "...", "id": "..." }

# Analyze
curl -X POST http://localhost:8000/resume/{id}/analyze \
  -H "Content-Type: application/json" \
  -d '{"target_role": "Software Engineer"}'
```

See [DEMO.md](DEMO.md) for the complete curl command sequence.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Vite `ECONNREFUSED` on `/resume/upload` | Backend not running | Start uvicorn on port 8000 |
| `relation "structured_resumes" does not exist` | Migration not applied | `alembic upgrade head` |
| DOCX preview "Something went wrong" | Missing templates | Run `create_canonical_docx_templates.py` |
| LLM health shows offline | Invalid API key | Check `GOOGLE_API_KEY` in `.env` |
| PDF preview missing | No LibreOffice/Word installed | Use DOCX download; check `pdf_error` in response |
| MCP/Drive features fail | Optional env vars not set | Configure or skip optional routes |
| Frontend API CORS errors | `ALLOWED_ORIGINS` mismatch | Add `http://localhost:5173` to `ALLOWED_ORIGINS` |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Commit your changes (`git commit -m 'feat: add your feature'`)
4. Push to the branch (`git push origin feat/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- Built with [Google Gemini 2.5 Flash](https://aistudio.google.com) for AI inference
- Session persistence via [MongoDB Atlas MCP](https://www.mongodb.com/developer/products/atlas/mcp-server-atlas/)
- Document rendering powered by [docxtpl](https://docxtpl.readthedocs.io)
- Built for the DevPost *"Building Agents for Real-World Challenges"* hackathon
