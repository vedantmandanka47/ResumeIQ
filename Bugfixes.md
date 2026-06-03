# Bugfixes & Smoothness Improvements (Applied)

See [README.md](README.md) for full run instructions, pre-run review, and testing order.

## Additional fixes (pre-run review pass)

| Issue | Fix |
|--------|-----|
| `routers/__init__.py` absolute imports during package init | Relative imports `from . import ...` |
| All integrations required at startup | Only `DATABASE_URL` + `GOOGLE_API_KEY` required |
| Missing DOCX templates silent failure | Startup warning + README step to run `create_canonical_docx_templates.py` |
| Invalid `model` field on rewrite request (frontend) | Removed from `RewritePage.jsx` |
| `GEMINI_MODEL` vs `GEMINI_RESUME_MODEL` drift | `gemini.py` reads both |
| Dead `HTTPException` re-raise in global handler | Removed |
| Company request alias robustness | `populate_by_name=True` on `CompanyAnalysisRequest` |

---
This document lists high-impact bugfixes and stability improvements based on a static code review of the current backend (FastAPI) and frontend (React).

## 1) Backend startup reliability
### 1.1 Fragile router importing
**Issue:** `backend/app/main.py` uses:
```py
from app.routers import generation, health, resume
```
But `backend/app/routers/__init__.py` contains only a docstring and does not explicitly expose those submodules.

**Fix to consider:** Update `backend/app/routers/__init__.py` to explicitly import/export the router modules (or change `main.py` to import submodules directly, e.g. `from app.routers import generation as generation_router` / `from app.routers.health import router as health_router`, etc.).

**Impact if not fixed:** Possible `ImportError` and immediate server crash on startup.

---

## 2) Generation UI correctness & caching signals
### 2.1 `cache_hit` incorrectly set during template switching
**Issue:** In `backend/app/services/resume_generation.py`, `switch_template()` returns:
```py
return GenerationResult(..., cache_hit=True)
```
Even though it renders new DOCX/PDF for the new template, it only reuses structured resume JSON. This can mislead UI text and downstream logic.

**Fix to consider:** Return `cache_hit` based on structured-resume cache reuse only, or rename the field in the API response (e.g. `structured_cache_hit`) and keep `cache_hit` meaning “structured resume cache reused”.

**Impact:** UI “cached structured resume” messaging may be wrong; users may think generation is instant when files are actually regenerated.

---

## 3) Health endpoint / frontend robustness
### 3.1 Health response shape assumptions
**Issue:** `frontend/src/pages/StatusPage.jsx` assumes:
- `data.db === 'connected'`
- `data.llm === 'connected'`
- `data.mcp === 'connected'`

Backend health endpoints depend on the agent responses:
- `/health/llm` uses `invoke("check_llm_health")`
- `/health/mcp` uses `invoke("check_mcp_health")`

**Fix to consider:**
- Normalize backend health response schema to always return consistent keys/values (e.g. always `{ llm: "connected" | "error" }`).
- Consider adding a fallback on the frontend when keys are missing (already partly handled, but strict equality checks can still produce “error” states).

**Impact:** “Offline” indicators may show incorrectly, and error messaging may be misleading.

---

### 3.2 Health JSON parsing failure handling
**Issue:** `frontend/src/api/client.js` assumes `await res.json()` in error cases:
```js
const err = await res.json().catch(() => ({}));
```
If backend returns non-JSON bodies (rare, but possible), frontend may throw less descriptive errors.

**Fix to consider:**
- Ensure backend always returns JSON for error responses.
- Optionally improve frontend error message to include `res.status` and raw text if JSON parsing fails.

**Impact:** Better diagnostics; less UI ambiguity during outages.

---

## 4) Generation preview/download availability consistency
### 4.1 Preview and download URLs may return 410 quickly
**Issue:** Backend marks `pdf_available` based on `record.pdf_path` truthiness, but the file on disk may be expired/removed. Endpoints handle this by returning 410.

**Fix to consider:**
- When generating responses, optionally verify the file exists before setting `pdf_available=true`.
- Or keep current behavior but improve frontend copy to clearly explain “may have expired—refresh generation”.

**Impact:** Prevents “Available but broken iframe/download” confusion.

---

## 5) Request/response compatibility hardening
### 5.1 Frontend payload structure vs backend schema
**Observation:** `GeneratePage.jsx` sends only `session_id` and `template_id`.
Backend allows optional `job_description` and `rewrite_instructions`, so this is OK, but:

**Fix to consider:** Ensure all frontend endpoints send exactly the fields the backend schema expects where required, and default optional fields consistently.

**Impact:** Avoids future regressions if schema changes tighten constraints.

---

## 6) Template rendering endpoint robustness
**Issue risk area:** `routers/resume.py` uses a broad set of endpoints that interact with:
- DOCX rendering
- PDF conversion
- file storage/streaming

**Fix to consider:**
- Add consistent error envelopes for all endpoints that return bytes/streams (ensure `res.json()` is always valid when returning errors).
- Ensure streaming endpoints set correct content types and handle encoding consistently.

**Impact:** Fewer “blank download” or “500 on render” surprises.

---

# Recommended Next Validation Steps (No Code Changes)
1. Start backend and confirm it boots without `ImportError`.
2. Call all health endpoints and confirm JSON shapes match frontend expectations.
3. Run end-to-end:
   - `/resume/upload`
   - `/generation/generate`
   - `/generation/preview/{id}` (iframe)
   - `/generation/download/{id}?format=docx`
   - `/generation/download/{id}?format=pdf`
4. Smoke test frontend pages:
   - StatusPage → UploadPage → GeneratePage → AnalysisPage
