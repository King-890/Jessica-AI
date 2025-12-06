Write-Host "Configuring Jessica to start automatically on login..."

$shortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\JessicaAI.lnk"

# Resolve project root relative to this script
$projRoot = (Resolve-Path "$PSScriptRoot\..").Path
$targetScript = Join-Path $projRoot "scripts\start_dev.ps1"

if (-Not (Test-Path $targetScript)) {
  Write-Host "❌ start_dev.ps1 not found at $targetScript" -ForegroundColor Red
  exit 1
}

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell"
$shortcut.Arguments = "-NoExit -File `"$targetScript`""
$shortcut.WorkingDirectory = $projRoot
$shortcut.IconLocation = "$env:SystemRoot\\System32\\SHELL32.dll,1"
$shortcut.Save()

Write-Host "✅ Jessica will start automatically on login." -ForegroundColor Green