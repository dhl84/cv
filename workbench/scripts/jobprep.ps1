<#
.SYNOPSIS
    Launch a local-LLM (Ollama) job application session.

.DESCRIPTION
    Creates an application folder, loads MASTER_PROFILE.md and the task prompt for the
    chosen mode into an Ollama chat session, and drops you into an interactive terminal
    chat that can generate CVs, cover letters, form answers, research a company from the
    web and role-play interviews.

.PARAMETER Company
    Company name. Used for the folder name and injected into context.

.PARAMETER Role
    Job title you are applying for.

.PARAMETER Mode
    cv | cover | fit | research | interview | roleplay | forms | chat

.PARAMETER Jd
    Path to a file containing the job advert (txt/md). Copied into the application folder.

.PARAMETER Model
    Ollama model tag. Defaults to $env:JOBPREP_MODEL, else gemma4:26b-a4b-it-qat.

.PARAMETER Research
    Run a single web search into research.md and exit.

.PARAMETER Ask
    Send one prompt non-interactively and exit.

.EXAMPLE
    .\scripts\jobprep.ps1 -Company Monzo -Role "Financial Controller" -Mode fit -Jd .\ad.txt

.EXAMPLE
    .\scripts\jobprep.ps1 -Company Monzo -Role "Financial Controller" -Mode roleplay

.EXAMPLE
    .\scripts\jobprep.ps1 -Company Monzo -Research "Monzo annual report 2026 auditor"
#>
[CmdletBinding()]
param(
    [Alias('c')][string]$Company = '',
    [Alias('r')][string]$Role = '',
    [Alias('m')][ValidateSet('cv','cover','fit','research','interview','roleplay','forms','chat')]
    [string]$Mode = 'chat',
    [string]$Jd = '',
    [string]$Dir = '',
    [string]$Model = '',
    [int]$Ctx = 32768,
    [double]$Temp = 0.4,
    [string]$Research = '',
    [string]$Ask = '',
    [switch]$NoServe
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

# --- python ---------------------------------------------------------------
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) { $pyCmd = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $pyCmd) { Write-Error 'Python not found on PATH. Install Python 3.9+ and retry.'; exit 1 }
$py = $pyCmd.Source

# --- ollama ---------------------------------------------------------------
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Error 'Ollama not found on PATH. Install from https://ollama.com and retry.'; exit 1
}

$ollamaHost = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { 'http://localhost:11434' }
if ($ollamaHost -notmatch '^https?://') { $ollamaHost = "http://$ollamaHost" }

function Test-Ollama {
    try { Invoke-RestMethod -Uri "$ollamaHost/api/tags" -TimeoutSec 3 | Out-Null; $true }
    catch { $false }
}

if (-not (Test-Ollama)) {
    if ($NoServe) { Write-Error "Ollama is not responding at $ollamaHost."; exit 1 }
    Write-Host 'Starting ollama serve...' -ForegroundColor Cyan
    Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden
    $deadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Ollama) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 500 }
    if (-not (Test-Ollama)) { Write-Error "Ollama did not start at $ollamaHost."; exit 1 }
}

# --- model ----------------------------------------------------------------
if (-not $Model) {
    $Model = if ($env:JOBPREP_MODEL) { $env:JOBPREP_MODEL } else { 'gemma4:26b-a4b-it-qat' }
}
$installed = (Invoke-RestMethod -Uri "$ollamaHost/api/tags").models.name
if ($installed -notcontains $Model -and -not ($installed | Where-Object { $_ -like "$Model*" })) {
    Write-Host "Model '$Model' is not installed." -ForegroundColor Yellow
    Write-Host ("Installed: `n  " + ($installed -join "`n  "))
    $pull = Read-Host "Pull '$Model' now? (y/N)"
    if ($pull -eq 'y') { ollama pull $Model } else { exit 1 }
}

# --- warm the model so the first reply is not a cold start ----------------
if (-not $Research) {
    Write-Host "Loading $Model ..." -ForegroundColor DarkGray
    try {
        Invoke-RestMethod -Uri "$ollamaHost/api/generate" -Method Post -TimeoutSec 300 `
            -ContentType 'application/json' `
            -Body (@{ model = $Model; prompt = ''; keep_alive = '30m' } | ConvertTo-Json) | Out-Null
    } catch { Write-Host 'warm-up skipped' -ForegroundColor DarkGray }
}

# --- hand over to the python REPL -----------------------------------------
$argv = @(
    (Join-Path $PSScriptRoot 'jobprep.py')
    '--mode',  $Mode
    '--model', $Model
    '--ctx',   $Ctx
    '--temp',  $Temp
)
if ($Company)  { $argv += @('--company',  $Company) }
if ($Role)     { $argv += @('--role',     $Role) }
if ($Jd)       { $argv += @('--jd',       (Resolve-Path $Jd).Path) }
if ($Dir)      { $argv += @('--dir',      $Dir) }
if ($Research) { $argv += @('--research', $Research) }
if ($Ask)      { $argv += @('--ask',      $Ask) }

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
& $py @argv
exit $LASTEXITCODE
