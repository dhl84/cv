# Daily income automation runner. Registered with Task Scheduler by register_task.ps1.
# Order matters: register diff feeds the target list that draft_outreach reads.
param(
    [int]$Drafts = 0,          # prospect emails to draft per day (0 = none; inbound-led plan, §06 Channel E)
    [switch]$NoScore,          # skip local-model scoring of jobs (fast, no GPU)
    [switch]$Open              # open today's report when done
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
$log = Join-Path $here "state\last-run.log"
"=== $(Get-Date -Format s) ===" | Out-File $log -Encoding utf8

# Make sure Ollama is up (it serves from the 5090; first call loads the model).
if (-not (Get-Process ollama -ErrorAction SilentlyContinue)) {
    Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 6
}

python fca_register_diff.py 2>&1 | Tee-Object -FilePath $log -Append
if ($NoScore) { python job_scan.py --no-score 2>&1 | Tee-Object -FilePath $log -Append }
else          { python job_scan.py            2>&1 | Tee-Object -FilePath $log -Append }
python draft_outreach.py $Drafts 2>&1 | Tee-Object -FilePath $log -Append

$report = Join-Path (Split-Path $here -Parent) ("daily\" + (Get-Date -Format yyyy-MM-dd) + ".md")
"report: $report" | Tee-Object -FilePath $log -Append
if ($Open -and (Test-Path $report)) { Start-Process $report }
