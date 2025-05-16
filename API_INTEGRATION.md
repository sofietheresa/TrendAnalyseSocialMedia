# Unified API Integration

This document describes the integration of the previously separate drift_api.py and main.py APIs into a single unified API.

## Overview

The system has been simplified by merging the functionality of the dedicated "drift API" (drift_api.py) into the main API (src/main.py). This eliminates the need to run two separate services and simplifies the architecture.

## Changes Made

1. All MLOPS endpoints from drift_api.py have been integrated into main.py:
   - `/api/mlops/pipelines`
   - `/api/mlops/pipelines/{pipeline_id}`
   - `/api/mlops/pipelines/{pipeline_id}/executions`
   - `/api/mlops/pipelines/{pipeline_id}/execute`
   - `/api/mlops/models/{model_name}/drift`

2. Import handling has been improved to handle both direct and relative imports.

3. The API description has been updated to reflect the expanded functionality.

## How to Use

### Starting the API

Run the integrated API:

```bash
python src/main.py
```

The API will run on port 8002 by default.

### Frontend Configuration

Update your frontend's API configuration to point to a single endpoint:

```javascript
// Update this in your frontend config file
const API_URL = "http://localhost:8002";
```

There's no need to configure a fallback to the drift API anymore.

### Available Endpoints

The following endpoints are now available on the integrated API:

#### Core Endpoints
- `/` - API root
- `/health` - Health check
- `/ping` - Simple ping for availability check
- `/data` - Get data from all platform tables
- `/sync` - Synchronize data from external clients

#### Debug Endpoints
- `/debug/routes` - List all available API routes

#### MLOPS Endpoints
- `/api/mlops/pipelines` - Get all ML pipelines status
- `/api/mlops/pipelines/{pipeline_id}` - Get details for a specific pipeline
- `/api/mlops/pipelines/{pipeline_id}/executions` - Get executions for a specific pipeline
- `/api/mlops/pipelines/{pipeline_id}/execute` - Execute a specific pipeline
- `/api/mlops/models/{model_name}/drift` - Get data drift metrics for a model version
- `/api/db/predictions` - Get topic predictions from ML models

## Decommissioning the Drift API

Since all functionality is now in the main API, the drift_api.py service should be stopped and can be removed from startup scripts or service managers.

You can keep the file for reference, but it's no longer needed for production use. 