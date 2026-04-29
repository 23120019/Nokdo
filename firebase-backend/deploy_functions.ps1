# Firebase functions deploy helper (PowerShell)
Set-Location -Path "$PSScriptRoot\functions"
Write-Host "Installing dependencies..."
npm ci

Write-Host "Ensure firebase CLI is logged in: firebase login"
Write-Host "If needed, set project: firebase use --add"

Write-Host "Deploying functions..."
npm run deploy

Write-Host "Done. Check Firebase Console or CLI output for function endpoints."
