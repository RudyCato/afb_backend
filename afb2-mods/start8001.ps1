# start8001.ps1 - starts AFB_Backend2 on port 8001
# Run from E:\Data\Claude\AFB_Backend2:
#   .\start8001.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating venv..." -ForegroundColor DarkGray
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "No venv found. Run this first:" -ForegroundColor Yellow
    Write-Host "  py -3.14 -m venv venv"
    Write-Host "  .\venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

python start.py --port 8001
