# Deployment script for Railway
# This script deploys the backend to Railway

Write-Host "Deploying Trend Analysis Social Media API to Railway..."

# Deploy the API
Write-Host "Deploying the unified API..."
railway up

Write-Host "`nDeployment completed successfully!"
Write-Host "Remember to set the following environment variable in your frontend:"
Write-Host "- REACT_APP_API_URL: Your API URL from Railway" 