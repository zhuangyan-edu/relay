# Relay 安装器（Windows PowerShell 5.1+）
#
# 默认行为是无损安装：同内容文件跳过，已有但不同的文件报告冲突并保留用户版本。
# 使用 -Force 才会覆盖冲突；配合 -Backup 可在覆盖前生成时间戳备份。
#
# 示例：
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Force -Backup
#   powershell -ExecutionPolicy Bypass -File .\install.ps1 -Check

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$Force,
    [switch]$Backup,
    [switch]$Check,
    [switch]$Quiet,
    [string]$AgentsDir = ""
)

$ErrorActionPreference = "Stop"

function Write-Status {
    param(
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::Gray
    )
    if (-not $Quiet) {
        Write-Host $Message -ForegroundColor $Color
    }
}

$scriptPath = $MyInvocation.MyCommand.Definition
$scriptDir = (Resolve-Path (Split-Path -Parent $scriptPath)).Path
if ([string]::IsNullOrWhiteSpace($AgentsDir)) {
    $homeDir = [Environment]::GetFolderPath("UserProfile")
    $AgentsDir = Join-Path $homeDir ".agents"
} else {
    $AgentsDir = [IO.Path]::GetFullPath($AgentsDir)
}

$versionPath = Join-Path $scriptDir "VERSION"
$version = if (Test-Path -LiteralPath $versionPath) {
    (Get-Content -LiteralPath $versionPath -Raw).Trim()
} else {
    "dev"
}

$manifest = New-Object System.Collections.Generic.List[object]
function Add-ManifestFile {
    param([string]$Source, [string]$RelativePath)
    if (Test-Path -LiteralPath $Source -PathType Leaf) {
        $manifest.Add([PSCustomObject]@{ Source = $Source; RelativePath = $RelativePath })
    } else {
        throw "Relay package is incomplete; missing file: $Source"
    }
}

Add-ManifestFile (Join-Path $scriptDir "VERSION") "VERSION"
Add-ManifestFile (Join-Path $scriptDir "relay.py") "relay.py"
Add-ManifestFile (Join-Path $scriptDir "PHILOSOPHY.md") "PHILOSOPHY.md"
Add-ManifestFile (Join-Path $scriptDir "custodian\projects.md") "custodian\projects.md"
Add-ManifestFile (Join-Path $scriptDir "custodian\ai-agents.md") "custodian\ai-agents.md"

foreach ($assetRoot in @("skills", "templates")) {
    $root = Join-Path $scriptDir $assetRoot
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        throw "Relay package is incomplete; missing directory: $root"
    }
    Get-ChildItem -LiteralPath $root -File -Recurse | ForEach-Object {
        $relativePath = $_.FullName.Substring($scriptDir.Length).TrimStart('\', '/')
        $manifest.Add([PSCustomObject]@{ Source = $_.FullName; RelativePath = $relativePath })
    }
}

if ($Check) {
    Write-Status ("Relay package OK: version {0}, {1} files" -f $version, $manifest.Count) Green
    exit 0
}

if (-not $DryRun) {
    foreach ($directory in @($AgentsDir, (Join-Path $AgentsDir "custodian"), (Join-Path $AgentsDir "custodian\reports"), (Join-Path $AgentsDir "skills"), (Join-Path $AgentsDir "templates"))) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
}

$installed = 0
$unchanged = 0
$conflicts = New-Object System.Collections.Generic.List[string]
$backedUp = 0
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

foreach ($item in $manifest) {
    $destination = Join-Path $AgentsDir $item.RelativePath
    $destinationParent = Split-Path -Parent $destination

    if ((Test-Path -LiteralPath $destination) -and -not (Test-Path -LiteralPath $destination -PathType Leaf)) {
        Write-Status ("[CONFLICT] {0} (目标路径不是文件；保留目标路径)" -f $item.RelativePath) Yellow
        $conflicts.Add($item.RelativePath)
        continue
    }

    if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
        Write-Status ("[ADD] {0}" -f $item.RelativePath) Cyan
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
            Copy-Item -LiteralPath $item.Source -Destination $destination
        }
        $installed++
        continue
    }

    $sourceHash = (Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash
    $destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
    if ($sourceHash -eq $destinationHash) {
        Write-Status ("[OK]  {0}" -f $item.RelativePath) DarkGray
        $unchanged++
        continue
    }

    if (-not $Force) {
        Write-Status ("[CONFLICT] {0} (保留目标文件；使用 -Force 覆盖)" -f $item.RelativePath) Yellow
        $conflicts.Add($item.RelativePath)
        continue
    }

    if ($Backup) {
        $backupPath = "$destination.bak.$timestamp"
        Write-Status ("[BACKUP] {0}" -f $backupPath) Magenta
        if (-not $DryRun) {
            Copy-Item -LiteralPath $destination -Destination $backupPath
        }
        $backedUp++
    }

    Write-Status ("[UPDATE] {0}" -f $item.RelativePath) Green
    if (-not $DryRun) {
        Copy-Item -LiteralPath $item.Source -Destination $destination -Force
    }
    $installed++
}

Write-Status ""
Write-Status ("Relay {0}: 新增/更新 {1}，未变更 {2}，备份 {3}，冲突 {4}" -f $version, $installed, $unchanged, $backedUp, $conflicts.Count) Cyan
$dryRunSuffix = if ($DryRun) { " (dry-run，未写入)" } else { "" }
Write-Status ("目标目录: {0}{1}" -f $AgentsDir, $dryRunSuffix) Gray
if (-not $DryRun) {
    Write-Status ("CLI: py -3 `"{0}`" init . --profile auto" -f (Join-Path $AgentsDir "relay.py")) Gray
}

if ($conflicts.Count -gt 0) {
    Write-Status "安装未完全应用：存在冲突。确认目标文件后重新运行 -Force（建议同时使用 -Backup）。" Yellow
    exit 2
}

exit 0
