# Alaya · 识海 — Setup Script (Windows PowerShell)
# Usage: .\install.ps1

Write-Host "=== Alaya · 识海 Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $python = "python3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
} else {
    Write-Host "ERROR: Python 3 not found. Please install Python 3.8+." -ForegroundColor Red
    exit 1
}

$version = & $python --version 2>&1
Write-Host "Python found: $version"

$verify = Join-Path $PSScriptRoot "scripts\verify_installation.py"
& $python $verify --root $PSScriptRoot
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Say 'alaya init' or '初始化识海' to choose a separate knowledge-base location."
Write-Host "  2. The skill installation has not created or modified a knowledge base."
