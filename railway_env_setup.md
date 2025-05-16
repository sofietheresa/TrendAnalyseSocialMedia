# Railway Environment Variables Setup

To fix the 502 errors with your backend URLs in the Railway deployment, you need to properly configure the following environment variables in the Railway dashboard. These settings are based on the working commit `cf4200b` ("improve topics 2").

## Critical Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | `postgresql://...` | Will be auto-set by Railway PostgreSQL plugin, but verify it's correct |
| `PORT` | `8000` | Railway expects the app to run on port 8000 |
| `FLASK_ENV` | `production` | Sets Flask to production mode |
| `ENVIRONMENT` | `production` | Additional environment indicator |
| `PYTHONUNBUFFERED` | `1` | Ensures Python output is unbuffered for proper logging |

## Railway Configuration Files

The working commit uses a special Railway setup:

1. `railway.toml` configuration:
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

2. The `run_railway.sh` script handles:
   - NLTK setup
   - Starting a health check app
   - Launching the main application on port 8000

## How to Set Environment Variables on Railway

1. Go to the [Railway Dashboard](https://railway.app/dashboard)
2. Select your project
3. Go to the "Variables" tab
4. Add each of the variables listed above

## Database Configuration Check

Ensure that:
1. You have the PostgreSQL plugin added to your Railway project
2. `DATABASE_URL` is correctly pointing to your Railway PostgreSQL instance
3. Your application can connect to the database (check logs for connection errors)

## Additional Troubleshooting

If you still experience 502 errors:

1. Check the application logs for specific error messages
2. Ensure the health check endpoint is working (`/railway-health`)
3. Try restarting the service from the Railway dashboard
4. Verify you're using the same structure as in commit `cf4200b`

## Using the Monitor Script

Run the provided `railway_monitor.py` script to check the health of your Railway deployment:

```bash
python railway_monitor.py
```

This will perform checks on various endpoints and provide recommendations for fixing issues. 