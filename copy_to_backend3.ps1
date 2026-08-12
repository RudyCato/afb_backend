# copy_to_backend3.ps1
# Copies afb_backend to AFB_Backend3 and applies the clean/modern redesign.
#
# Run from anywhere:
#   powershell -ExecutionPolicy Bypass -File "E:\Data\Claude\afb_website\afb_backend\copy_to_backend3.ps1"

$src  = "E:\Data\Claude\afb_website\afb_backend"
$dst  = "E:\Data\Claude\AFB_Backend3"
$mods = "$src\afb2-mods"

Write-Host ""
Write-Host "Step 1 - Copying project to AFB_Backend3..." -ForegroundColor Cyan

robocopy $src $dst /E /NFL /NDL /NJH /NJS `
  /XD ".git" "__pycache__" "venv" ".venv" "node_modules" "afb2-mods" `
  /XF "*.pyc" "copy_to_backend2.ps1" "copy_to_backend3.ps1"

if ($LASTEXITCODE -gt 7) {
  Write-Host "robocopy error ($LASTEXITCODE). Aborting." -ForegroundColor Red
  exit 1
}
Write-Host "  Project copied." -ForegroundColor Green

Write-Host ""
Write-Host "Step 2 - Applying clean/modern design..." -ForegroundColor Cyan

robocopy $mods $dst /E /IS /IT /NFL /NDL /NJH /NJS

if ($LASTEXITCODE -gt 7) {
  Write-Host "robocopy error applying design ($LASTEXITCODE)." -ForegroundColor Red
  exit 1
}
Write-Host "  Design applied." -ForegroundColor Green

Write-Host ""
Write-Host "Done! AFB_Backend3 is at: $dst" -ForegroundColor Green
Write-Host ""
Write-Host "To start it on port 8002:" -ForegroundColor Cyan
Write-Host "  cd $dst"
Write-Host "  py -3.14 -m venv venv"
Write-Host "  venv\Scripts\Activate.ps1"
Write-Host "  pip install -r requirements.txt"
Write-Host "  .\start8002.ps1"
