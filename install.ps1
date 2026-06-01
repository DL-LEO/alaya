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

# Check if setup wizard exists
$wizard = Join-Path $PSScriptRoot "scripts\setup_wizard.py"
if (Test-Path $wizard) {
    Write-Host ""
    $runWizard = Read-Host "Run setup wizard? (y/n)"
    if ($runWizard -eq "y" -or $runWizard -eq "Y") {
        & $python $wizard
    }
} else {
    Write-Host "Setup wizard not found. You can create it later."
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Place your knowledge cards in wiki/"
Write-Host "  2. Say 'alaya init' or 'scan cards' to your Agent"
Write-Host "  3. Start chatting: 'Enable Alaya'"
