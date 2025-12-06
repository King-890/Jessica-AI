Param(
    [string]$ListenHost = "127.0.0.1",
    [int]$ListenPort = 6060
)

# Use format string to avoid PowerShell variable-scope parsing on ':'
Write-Host ("Starting FastAPI backend on http://{0}:{1}" -f $ListenHost, $ListenPort)
Set-Location "$PSScriptRoot\.."
python -m uvicorn backend.app:app --host $ListenHost --port $ListenPort --reload