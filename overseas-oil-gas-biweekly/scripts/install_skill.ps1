# overseas-oil-gas-biweekly skill installer
# Usage from repo root:
#   powershell -ExecutionPolicy Bypass -File overseas-oil-gas-biweekly\scripts\install_skill.ps1

param(
    [ValidateSet("cursor", "claude", "both")]
    [string]$Target = "both",
    [string]$SourceDir = ""
)

$ErrorActionPreference = "Stop"

if ($SourceDir) {
    $skillSrc = (Resolve-Path $SourceDir).Path
} else {
    $skillSrc = Split-Path $PSScriptRoot -Parent
}

if (-not (Test-Path (Join-Path $skillSrc "SKILL.md"))) {
    Write-Error "SKILL.md not found. Use -SourceDir to point to overseas-oil-gas-biweekly."
}

function Install-To($dest) {
    $parent = Split-Path $dest -Parent
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    if (Test-Path $dest) {
        Remove-Item -Recurse -Force $dest
    }
    Copy-Item -Recurse -Force $skillSrc $dest
    Write-Host "Installed -> $dest" -ForegroundColor Green
}

Write-Host "Source: $skillSrc"

switch ($Target) {
    "cursor" {
        Install-To (Join-Path $env:USERPROFILE ".cursor\skills\overseas-oil-gas-biweekly")
    }
    "claude" {
        Install-To (Join-Path $env:USERPROFILE ".claude\skills\overseas-oil-gas-biweekly")
    }
    "both" {
        Install-To (Join-Path $env:USERPROFILE ".cursor\skills\overseas-oil-gas-biweekly")
        Install-To (Join-Path $env:USERPROFILE ".claude\skills\overseas-oil-gas-biweekly")
    }
}

Write-Host ""
Write-Host "Installing Python dependencies..."
py -3 -m pip install -r (Join-Path $skillSrc "requirements.txt")

$template = Join-Path $env:USERPROFILE ".cursor\skills\overseas-oil-gas-biweekly\references\sample_issue60.docx"
if (-not (Test-Path $template)) {
    Write-Warning "Missing references\sample_issue60.docx"
} else {
    Write-Host "Word template: OK" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. See INSTALL.md for usage in Cursor / Claude Code."
