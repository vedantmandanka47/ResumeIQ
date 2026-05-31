# ResumeIQ — Demo & Local Setup Guide

Follow these steps to run ResumeIQ locally from scratch.

## 1. Environment Setup

Use Python 3.12 with the pinned backend dependencies.

1. Copy the example config:
   ```bash
   cp .env.example .env
   ```
2. Fill in the required variables in `.env` (PostgreSQL credentials, Google Gemini API key, MongoDB MCP URL, etc.).

### MongoDB Setup

Use a MongoDB Atlas cluster and set `MONGODB_ATLAS_URI`. A local MongoDB
Community Server download is not required when Atlas is used. MongoDB Compass
is optional and is useful only as a desktop GUI for inspecting stored data.

Set `MONGODB_MCP_SERVER_URL` to the MCP server used by the separately owned
agent service. MongoDB save, history, benchmark, and health calls remain part
of the backend API contract.

## 2. Database Initialisation

1. Start your local PostgreSQL server.
2. In the `backend/` directory, set up your Python virtual environment and install dependencies:
   ```bash
   py -3.12 -m venv .venv  # Windows
   source .venv/bin/activate  # macOS/Linux
   .\.venv\Scripts\Activate.ps1  # Windows PowerShell
   pip install -r requirements.txt
   ```
3. Run Alembic migrations to create the tables (once configured):
   ```bash
   alembic upgrade head
   ```

## 3. Start the Application

### Backend
From the `backend/` directory (with your virtual environment active):
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.
You can check the API docs at `http://localhost:8000/docs`.

### Frontend
From the `frontend/` directory in a new terminal window:
```bash
npm install
npm run dev
```
The React app will be available at `http://localhost:5173`.

## 4. Phase Testing (Curl Commands)

### Phase 0: Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/llm
curl http://localhost:8000/health/mcp
```
*Expected: each configured service responds with its own structured status.*

*(Further phase commands will be added here as the application progresses.)*
