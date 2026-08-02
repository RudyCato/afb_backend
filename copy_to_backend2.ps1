# copy_to_backend2.ps1
# ─────────────────────────────────────────────────────────────────────────────
# 1. Copies the full afb_backend project to E:\Data\Claude\AFB_Backend2
# 2. Overlays the americanfoodbeverage.com-schema modified afb-site files
#
# Run (from any directory):
#   powershell -ExecutionPolicy Bypass -File "E:\Data\Claude\afb_website\afb_backend\copy_to_backend2.ps1"
# ─────────────────────────────────────────────────────────────────────────────

$src  = "E:\Data\Claude\afb_website\afb_backend"
$dst  = "E:\Data\Claude\AFB_Backend2"
$mods = "$src\afb2-mods"

# ── Step 1: Full project copy ────────────────────────────────────────────────
Write-Host ""
Write-Host "Step 1 - Copying project: $src -> $dst" -ForegroundColor Cyan

robocopy $src $dst /E /NFL /NDL /NJH /NJS `
  /XD ".git" "__pycache__" "venv" ".venv" "node_modules" "afb2-mods" `
  /XF "*.pyc" "copy_to_backend2.ps1"

if ($LASTEXITCODE -gt 7) {
  Write-Host "robocopy error (exit $LASTEXITCODE). Aborting." -ForegroundColor Red
  exit 1
}
Write-Host "  ✓ Project copied." -ForegroundColor Green

# ── Step 2: Overlay americanfoodbeverage.com schema modifications ────────────
Write-Host ""
Write-Host "Step 2 - Applying americanfoodbeverage.com schema to afb-site/" -ForegroundColor Cyan

robocopy $mods $dst /E /NFL /NDL /NJH /NJS

if ($LASTEXITCODE -gt 7) {
  Write-Host "robocopy error applying mods (exit $LASTEXITCODE)." -ForegroundColor Red
  exit 1
}
Write-Host "  ✓ Schema modifications applied." -ForegroundColor Green

# ── Summary ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Done! AFB_Backend2 is ready at: $dst" -ForegroundColor Green
Write-Host ""
Write-Host "Modified files (americanfoodbeverage.com schema):" -ForegroundColor Yellow
Write-Host "  afb-site/assets/app.js  - 5-category nav + Corporate/Links/Support/Pages footer"
Write-Host "  afb-site/about.html     - 1989 founding story, 4 facilities, 10 acres NJ"
Write-Host "  afb-site/index.html     - category-grid homepage matching afb.com layout"
Write-Host ""
Write-Host "To run AFB_Backend2 on port 8001:" -ForegroundColor Cyan
Write-Host "  cd $dst"
Write-Host "  py -3.14 -m venv venv"
Write-Host "  venv\Scripts\Activate.ps1"
Write-Host "  pip install -r requirements.txt"
Write-Host "  start.ps1 --port 8001"
