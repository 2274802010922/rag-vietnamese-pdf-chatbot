$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$healthUrl = "http://127.0.0.1:8000/health"
try {
    $existing = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
    Write-Host "Backend appears to be running already at $healthUrl"
    Write-Host ($existing | ConvertTo-Json -Compress)
    Write-Host "Stop the existing backend first if you want to restart with new code."
    exit 0
} catch {
    # No backend is listening, continue.
}

.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
