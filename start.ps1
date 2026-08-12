# start.ps1 - activates the venv, then runs start.py
#
# Run it from the afb_backend folder:
#     .\start.ps1
#     .\start.ps1 -check      (or --check)
#
# The venv can only be activated by the shell, not by Python, which is why
# this wrapper exists. Everything after that happens in start.py.
#
# ASCII ONLY. Windows PowerShell 5.1 misreads non-ASCII characters in files
# saved without a BOM, which breaks string parsing further down the file.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating venv..." -ForegroundColor DarkGray
    & ".\venv\Scripts\Activate.ps1"
} else {
    Write-Host "No venv found at .\venv - create one with:" -ForegroundColor Yellow
    Write-Host "  py -3.14 -m venv venv"
    Write-Host "  .\venv\Scripts\Activate.ps1"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

# start.py uses argparse, which wants --check. PowerShell habit is -check.
# Accept either by promoting single-dash long flags to double-dash.
$fwd = @()
foreach ($a in $args) {
    if ($a -is [string] -and $a -match '^-[A-Za-z][A-Za-z-]+$') {
        $fwd += "-$a"
    } else {
        $fwd += $a
    }
}

python start.py @fwd
