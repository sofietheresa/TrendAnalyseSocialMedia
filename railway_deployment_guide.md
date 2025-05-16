# Railway Deployment Guide for TrendAnalyseSocialMedia

This guide will help you deploy the current application state (commit cf4200b) to Railway properly.

## Step 1: Verify Required Files

Make sure these critical files are present:

- `railway.toml` - Deployment configuration
- `app/run_railway.sh` - Startup script (must be executable)
- `app/railway.py` - Railway-specific launcher
- `app/health_app.py` - Health check app
- `app/main.py` - Main application

## Step 2: Deploy to Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **New Project** > **Deploy from GitHub**
3. Select your GitHub repository
4. For the **Branch**, select the branch containing commit `cf4200b` or create a new branch from this commit
5. Click **Deploy**

## Step 3: Add PostgreSQL Database

1. In your project dashboard, click **+ New**
2. Select **Database** > **PostgreSQL**
3. Wait for the database to provision

## Step 4: Set Required Environment Variables

Add these **exact** environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `PORT` | `8000` | **Required** - Railway expects the app to run on port 8000 |
| `FLASK_ENV` | `production` | **Required** - Sets Flask to production mode |
| `ENVIRONMENT` | `production` | **Required** - Additional environment indicator |
| `PYTHONUNBUFFERED` | `1` | **Required** - Ensures Python output is unbuffered |

**Important**: The `DATABASE_URL` variable will be automatically set by Railway when you add the PostgreSQL plugin.

To set these variables:
1. Go to your project in Railway
2. Click the **Variables** tab
3. Add each variable and its value
4. Click **Save Changes**

## Step 5: Verify Deployment Configuration

Make sure your `railway.toml` file contains:

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "cd app && chmod +x run_railway.sh && ./run_railway.sh"
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"

[environments]
[environments.production]
numReplicas = 1
```

## Step 6: Make run_railway.sh Executable

If you're deploying from Windows, make sure to add this line to your deployment:

```bash
# Make sure the script is executable when deployed
git update-index --chmod=+x app/run_railway.sh
git commit -m "Make run_railway.sh executable"
git push
```

## Step 7: Check Deployment

1. Wait for the deployment to complete
2. Click on your service in Railway dashboard
3. Go to the **Deployments** tab to see the build progress
4. Once deployed, click the URL to verify the app is running

## Step 8: Troubleshooting

If you encounter 502 errors:

1. Check logs in the Railway dashboard for errors
2. Verify that your `run_railway.sh` script is being executed
3. Ensure the health check endpoint at `/` is responding
4. Check that your database connection is working with the automatically provided `DATABASE_URL`

## Connecting the Frontend

If your frontend is hosted separately (e.g., on Vercel), set this environment variable in your frontend deployment:

```
REACT_APP_API_URL=https://your-railway-app-url.up.railway.app
```

Note that with this working commit (cf4200b), API endpoints are accessed directly (not behind `/api`), so don't add any path prefix. 