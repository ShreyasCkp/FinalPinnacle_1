# PowerShell script to update database password in .env file
# Usage: .\update_password.ps1 "your_actual_password"

param(
    [Parameter(Mandatory=$true)]
    [string]$Password
)

$envFile = ".env"
$content = Get-Content $envFile -Raw
$content = $content -replace "DB_PASSWORD=your_local_password", "DB_PASSWORD=$Password"
$content = $content -replace "DB_PASSWORD=.*", "DB_PASSWORD=$Password"
Set-Content -Path $envFile -Value $content -NoNewline
Write-Host "Password updated in .env file" -ForegroundColor Green

