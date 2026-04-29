# Frontend deploy helper (PowerShell)
# Usage: open PowerShell and run this script after configuring wrangler or prefer GitHub+Cloudflare Pages.

param(
  [string]$publishWith = "wrangler"  # "wrangler" or "git"
)

Set-Location -Path "$PSScriptRoot"
Write-Host "Installing dependencies..."
npm ci
Write-Host "Building frontend..."
npm run build

if ($publishWith -eq "wrangler") {
  if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Error "npx (node) not found. Install Node and npm."
    exit 1
  }
  Write-Host "Publishing with wrangler (requires login configured)..."
  npx wrangler pages publish ./dist --project-name your-pages-project
} else {
  Write-Host "Built to ./dist. Push this repo to GitHub and connect to Cloudflare Pages."
}
