param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$TaskName = "JessicaAI_Desktop",
    [string]$ScriptPath = (Resolve-Path "$PSScriptRoot\start_dev.ps1").Path
)

Write-Host "Registering scheduled task '$TaskName' to start Jessica (backend + Electron) at login..."

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`"" -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Description "Start Jessica AI at login (backend + desktop shell)" -Force

Write-Host "Scheduled task '$TaskName' registered."

# Helper to remove the task:
# Unregister-ScheduledTask -TaskName "JessicaAI_Desktop" -Confirm:$false