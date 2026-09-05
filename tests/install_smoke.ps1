# Relay installer smoke test (Windows PowerShell 5.1+).
# This test uses a generated temporary directory and never touches ~/.agents.

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$installer = Join-Path $repoRoot "install.ps1"
$target = Join-Path ([IO.Path]::GetTempPath()) ("relay-smoke-" + [guid]::NewGuid().ToString("N"))
$directoryConflictTarget = Join-Path ([IO.Path]::GetTempPath()) ("relay-smoke-directory-" + [guid]::NewGuid().ToString("N"))

function Invoke-Installer {
    param([string[]]$Arguments)
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer @Arguments
    return $LASTEXITCODE
}

try {
    if ((Invoke-Installer @("-Check", "-Quiet")) -ne 0) {
        throw "package check failed"
    }

    if ((Invoke-Installer @("-AgentsDir", $target, "-Quiet")) -ne 0) {
        throw "initial install failed"
    }
    foreach ($relative in @("VERSION", "relay.py", "PHILOSOPHY.md", "skills\skill-relay\SKILL.md")) {
        if (-not (Test-Path -LiteralPath (Join-Path $target $relative) -PathType Leaf)) {
            throw "missing installed asset: $relative"
        }
    }

    Set-Content -LiteralPath (Join-Path $target "PHILOSOPHY.md") -Value "local customization" -Encoding UTF8
    if ((Invoke-Installer @("-AgentsDir", $target, "-Quiet")) -ne 2) {
        throw "conflicting install did not return exit code 2"
    }
    if ((Get-Content -LiteralPath (Join-Path $target "PHILOSOPHY.md") -Raw).Trim() -ne "local customization") {
        throw "conflicting install overwrote a local file"
    }

    if ((Invoke-Installer @("-AgentsDir", $target, "-Force", "-Backup", "-Quiet")) -ne 0) {
        throw "forced install failed"
    }
    if ((Get-ChildItem -LiteralPath $target -Filter "PHILOSOPHY.md.bak.*" -File).Count -lt 1) {
        throw "forced install did not create a backup"
    }

    New-Item -ItemType Directory -Path $directoryConflictTarget -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $directoryConflictTarget "relay.py") -Force | Out-Null
    if ((Invoke-Installer @("-AgentsDir", $directoryConflictTarget, "-Quiet")) -ne 2) {
        throw "directory destination did not return exit code 2"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $directoryConflictTarget "relay.py") -PathType Container)) {
        throw "directory destination was replaced"
    }

    Write-Host "Relay installer smoke test passed" -ForegroundColor Green
    exit 0
} finally {
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
    if (Test-Path -LiteralPath $directoryConflictTarget) {
        Remove-Item -LiteralPath $directoryConflictTarget -Recurse -Force
    }
}
