# New-M6RoleVenvs.ps1 -- create the .venv layer for the whole pack in one shot.
#
# Creates .venv with an explicitly resolved Python interpreter in: pack root + 00-analyst, 01-coder,
# 02-tester, 03-runner, 04-boundary, 06-security. NEVER in 05-judge
# (output-only folder by design; the script REPORTS a violation if one exists).
#
# Requirements are TWO-LAYER:
#   - pack root requirements.txt      = baseline (STDLIB-ONLY policy)
#   - <role>\requirements.txt         = role-specific file that includes the
#     baseline via "-r ../requirements.txt" plus a GATED role section
#     (packages land there only via owner decision + operator + changelog).
# Each venv installs from ITS OWN role file when present, else the baseline.
# Nothing is installed while all layers are comment-only (stdlib-only).
# Idempotent: safe to re-run; existing venvs are kept and re-verified.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup\New-M6RoleVenvs.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup\New-M6RoleVenvs.ps1 -PythonExe C:\Path\To\python.exe
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup\New-M6RoleVenvs.ps1 -Recreate   # delete + rebuild all
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup\New-M6RoleVenvs.ps1 -SkipInstall

param(
    [string]$PackRoot = "",
    [string]$PythonExe = "",
    [switch]$Recreate,
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($PackRoot)) {
    $PackRoot = Split-Path $PSScriptRoot -Parent
}
$PackRoot = [System.IO.Path]::GetFullPath($PackRoot)

$targets = @('.', '00-analyst', '01-coder', '02-tester', '03-runner', '04-boundary', '06-security')
$rootReq = Join-Path $PackRoot 'requirements.txt'

function Resolve-BasePython([string]$explicitPath) {
    if (-not [string]::IsNullOrWhiteSpace($explicitPath)) {
        $full = [System.IO.Path]::GetFullPath($explicitPath)
        if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
            throw "Python executable not found: $full"
        }
        return [pscustomobject]@{ Program = $full; PrefixArgs = @(); Label = $full }
    }
    $launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($launcher) {
        return [pscustomobject]@{ Program = $launcher.Source; PrefixArgs = @('-3'); Label = 'py -3' }
    }
    foreach ($name in @('python.exe', 'python3.exe')) {
        $cmd = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue
        if ($cmd) {
            return [pscustomobject]@{ Program = $cmd.Source; PrefixArgs = @(); Label = $cmd.Source }
        }
    }
    throw "Python 3 not found. Install Python 3 or rerun with -PythonExe C:\Path\To\python.exe"
}

$basePython = Resolve-BasePython $PythonExe
Write-Host ("Base Python: " + $basePython.Label)

function Invoke-BasePython([string[]]$Arguments) {
    $prefix = @($basePython.PrefixArgs)
    & $basePython.Program @prefix @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Base Python failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
    }
}

function Test-ReqHasPackages([string]$reqFile) {
    # True when the file (following one level of "-r <file>" includes) contains
    # any real requirement line (non-comment, non-include).
    if (-not (Test-Path -LiteralPath $reqFile)) { return $false }
    foreach ($line in (Get-Content -Encoding UTF8 $reqFile)) {
        $t = $line.Trim()
        if ($t.Length -eq 0 -or $t.StartsWith('#')) { continue }
        if ($t -match '^-r\s+(.+)$') {
            $inc = $Matches[1].Trim()
            $incPath = Join-Path (Split-Path $reqFile -Parent) $inc
            if (Test-ReqHasPackages ([System.IO.Path]::GetFullPath($incPath))) { return $true }
            continue
        }
        return $true
    }
    return $false
}

$rows = @()
foreach ($t in $targets) {
    $base = if ($t -eq '.') { $PackRoot } else { Join-Path $PackRoot $t }
    if (-not (Test-Path -LiteralPath $base)) { throw "Role folder missing: $base" }
    $venv = Join-Path $base '.venv'
    if ($Recreate -and (Test-Path -LiteralPath $venv)) {
        Remove-Item -Recurse -Force -Confirm:$false $venv
    }
    $created = $false
    if (-not (Test-Path -LiteralPath $venv)) {
        Write-Host ("creating venv: " + $venv)
        Invoke-BasePython @('-m', 'venv', $venv)
        $created = $true
    }
    $pyexe = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pyexe)) { throw "venv creation failed: $venv" }
    $ver = (& $pyexe --version) 2>$null
    # role file wins; pack root falls back to the baseline
    $roleReq = Join-Path $base 'requirements.txt'
    $reqFile = if ((Test-Path -LiteralPath $roleReq) -and ($t -ne '.')) { $roleReq } else { $rootReq }
    $reqLabel = if ($reqFile -eq $rootReq) { 'baseline' } else { $t + '\requirements.txt' }
    $installed = 'stdlib-only (nothing to install; ' + $reqLabel + ')'
    if (-not $SkipInstall -and (Test-ReqHasPackages $reqFile)) {
        Write-Host ("installing " + $reqLabel + " into " + $venv)
        & $pyexe -m pip install --disable-pip-version-check -r $reqFile
        if ($LASTEXITCODE -ne 0) { throw "pip install failed in $venv" }
        $installed = 'installed from ' + $reqLabel
    }
    $rows += New-Object PSObject -Property @{
        Folder = $t; Venv = 'OK' + $(if ($created) { ' (new)' } else { ' (existing)' })
        Python = [string]$ver; Install = $installed
    }
}

# 05-judge must NOT have a venv
$judgeVenv = Join-Path $PackRoot '05-judge\.venv'
if (Test-Path -LiteralPath $judgeVenv) {
    Write-Host "VIOLATION: 05-judge has a .venv - it must be output-only. Delete it:" -ForegroundColor Red
    Write-Host ("  Remove-Item -Recurse -Force '" + $judgeVenv + "'")
} else {
    $rows += New-Object PSObject -Property @{ Folder = '05-judge'; Venv = 'NONE (by design)'; Python = '-'; Install = '-' }
}

$rows | Select-Object Folder, Venv, Python, Install | Format-Table -AutoSize
Write-Host "Activation is PER WINDOW (cannot be batched across windows):"
Write-Host "  PowerShell:  & .\.venv\Scripts\Activate.ps1"
Write-Host "  cmd.exe:     .venv\Scripts\activate.bat"
Write-Host "Note: run pack Python tooling with the active role venv (or its explicit .venv\Scripts\python.exe path)."
