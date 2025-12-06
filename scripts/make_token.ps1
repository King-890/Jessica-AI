param(
    [ValidateSet('user','admin','skill')]
    [string]$Role = 'user'
)

Set-Location "$PSScriptRoot\.."

# Generate token with selected role
$pythonCode = @"
from backend.routes.auth import make_token
print(make_token("""$Role"""))
"@

$token = python -c $pythonCode

Write-Host "Generated $Role token: $token"

# Save to dev file
Set-Content -Path "data/dev_token.txt" -Value $token -Encoding ASCII
Write-Host "Saved to data/dev_token.txt"

# Update .env with API_TOKEN and REQUIRE_API_TOKEN=true
$envPath = ".env"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath
    $hasApiToken = $false
    $newContent = @()
    foreach ($line in $envContent) {
        if ($line -match '^API_TOKEN=') {
            $hasApiToken = $true
            $newContent += "API_TOKEN=$token"
        } else {
            $newContent += $line
        }
    }
    if (-not $hasApiToken) {
        $newContent += "API_TOKEN=$token"
    }
    # Ensure REQUIRE_API_TOKEN=true present
    if (-not ($newContent -match '^REQUIRE_API_TOKEN=')) {
        $newContent += "REQUIRE_API_TOKEN=true"
    }
    $newContent | Set-Content $envPath -Encoding UTF8
} else {
    Set-Content $envPath @(
        "API_TOKEN=$token",
        "REQUIRE_API_TOKEN=true"
    ) -Encoding UTF8
}

Write-Host "Updated .env with API_TOKEN and REQUIRE_API_TOKEN=true"