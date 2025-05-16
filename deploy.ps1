# Deployment script for Railway
# This script deploys both the drift API and the main backend to Railway

Write-Host "Deploying Trend Analysis Social Media apps to Railway..."

# Step 1: Deploy the drift API
Write-Host "`nStep 1: Deploying the drift API..."
railway up --service drift-api

# Step 2: Deploy the main backend
Write-Host "`nStep 2: Deploying the main backend..."
railway up --service main-api

Write-Host "`nDeployment completed successfully!"
Write-Host "Remember to set the following environment variables in your frontend:"
Write-Host "- REACT_APP_API_URL: Your main API URL"
Write-Host "- REACT_APP_DRIFT_API_URL: Your drift API URL" 