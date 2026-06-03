# Start ResumeIQ API (run from backend/ directory)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    py -3.12 -m venv .venv
}

$python = ".\.venv\Scripts\python.exe"
& $python -m pip install -q -r requirements.txt

if (-not (Test-Path ".\templete\canonical_minimalist.docx")) {
    Write-Host "Generating DOCX templates..."
    & $python create_canonical_docx_templates.py
}

Write-Host "Starting API on http://127.0.0.1:8000"
& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
