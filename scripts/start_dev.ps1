Write-Host "Starting backend and UI dev servers"

$projRoot = "$PSScriptRoot\.."

# Start backend in a new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$projRoot'; python -m uvicorn backend.app:app --host 127.0.0.1 --port 6060 --reload"

# Start UI dev server in current window
Set-Location "$projRoot\ui"
npm run dev