$ErrorActionPreference = "Stop"

# Load Secrets (Parsing python file is hard, we will hardcode the logic to read it via string matching for this test script)
# Actually, let's just use the known env vars if set, or read the file.
# Since we are an agent, we can't easily parse.
# Let's try to assume the user set them or we can grab them from earlier.
# Wait, I can't "grab them".
# I will make Python print the curl command, and then execute that.

Write-Output "Generating CURL command..."
python -c "from src.app_secrets import SUPABASE_URL, SUPABASE_ANON_KEY; print(f'{SUPABASE_URL} {SUPABASE_ANON_KEY}')" > secrets.tmp

$content = Get-Content secrets.tmp
$parts = $content -split " "
$url = $parts[0] + "/rest/v1/documents"
$key = $parts[1]

Write-Output "Target URL: $url"

$headers = @{
    "apikey" = $key
    "Authorization" = "Bearer $key"
    "Content-Type" = "application/json"
    "Prefer" = "return=representation"
}

$body = @{
    content = "Diagnostics Test: PowerShell Probe"
    metadata = @{
        source = "powershell"
        topic = "db_diagnostics_ps"
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
} | ConvertTo-Json

Write-Output "Sending Request..."
try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
    Write-Output "✅ SUCCESS: Record Inserted"
    Write-Output $response
} catch {
    Write-Output "❌ FAILED: $_"
    Write-Output $_.StartInfo
}

Remove-Item secrets.tmp
