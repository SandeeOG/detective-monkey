# Detective Monkey — one-command launcher (Windows PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}
& ".venv\Scripts\python.exe" -m pip install -q -r backend\requirements.txt
Write-Host "Starting Detective Monkey at http://localhost:8000 ..." -ForegroundColor Green
Set-Location backend
& "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
