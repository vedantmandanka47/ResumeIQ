# ResumeIQ — Demo & Local Setup Guide

Follow these steps to run ResumeIQ locally from scratch.

## 1. Environment Setup

1. Copy the example config:
   ```bash
   cp .env.example .env
   ```
2. Fill in the required variables in `.env` (PostgreSQL credentials, Google Gemini API key, MongoDB MCP URL, etc.).

## 2. Database Initialisation

1. Start your local PostgreSQL server.
2. In the `backend/` directory, set up your Python virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
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
curl http://localhost:8000/health/all
```
*Expected: 200 OK with status of app, db, llm, and mcp connections.*

*(Further phase commands will be added here as the application progresses.)*
