# Agent Service Boundary

The API layer loads `app.services.agent` at call time. That separately owned
package must expose these async functions:

- `analyze(raw_text, target_role)`
- `company_analyze(analysis_result, company_name)`
- `rewrite(raw_text, analysis, target_role, company_name)`
- `roadmap(analysis, company_result)`
- `save_to_mongo(session_id, analysis, company_result, rewrite_result, roadmap)`
- `get_history(session_id)`
- `get_benchmark()`
- `export_to_drive(rewritten_text, roadmap, session_id)`
- `check_llm_health()`
- `check_mcp_health()`

The backend intentionally does not implement prompts, Gemini calls, MongoDB
access, or Google Drive access.
