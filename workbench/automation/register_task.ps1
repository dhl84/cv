# Registers (or replaces) the daily Task Scheduler job. Run once from an elevated or normal
# PowerShell: .\register_task.ps1   (add -At "06:30" to change the time)
param([string]$At = "07:00", [string]$Name = "cv-daily-income")
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $pwsh) { $pwsh = (Get-Command powershell).Source }
$action  = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$here\daily.ps1`" -Drafts 3" -WorkingDirectory $here
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
Unregister-ScheduledTask -TaskName $Name -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -Description "FCA register diff, job scan, outreach drafts -> cv\gtm\daily" | Out-Null
Write-Host "Registered '$Name' daily at $At. Test now with: Start-ScheduledTask -TaskName $Name"
