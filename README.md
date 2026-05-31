# ResumeIQ

**ResumeIQ** is an open-source, zero-paywall AI resume analysis agent built for the DevPost hackathon "Building Agents for Real-World Challenges."

It provides deep resume analysis across 7 dimensions, specific target company intelligence (using live web search), an automated fresher/intern detection mode, an AI-powered resume rewrite capability with an authenticity layer, and a personalized improvement roadmap.

## Hackathon Partner Integration
This project specifically fulfills the **MongoDB** partner track requirements by persisting all agent-generated session outputs (analysis, rewrite, roadmap) via the Google Cloud Agent Builder MCP runtime.

## Tech Stack
- **Frontend**: React (Vite)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (SQLAlchemy Async, Alembic)
- **AI/LLM**: Google Gemini (via `google-generativeai` SDK)
- **Integration**: MongoDB Atlas (via Agent Builder MCP)

## Documentation
- Read the main prompt instructions to understand the 7-phase build structure.
- See `DEMO.md` for local setup instructions and a quickstart guide for the evaluators.
