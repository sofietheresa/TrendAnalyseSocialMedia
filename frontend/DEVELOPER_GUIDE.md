# Developer Guide: Mock Data and API Integration

This guide explains how the application currently handles data and provides instructions on how to switch from mock data to real API endpoints when they become available.

## Current State: Mock Data Implementation

The application is currently configured to use mock data since the FastAPI backend endpoints are still under development. This ensures that frontend development can proceed smoothly without waiting for backend implementations.

### Key Components

1. **Configuration in `api.js`**:
   - `useMockApi` flag is set to `true` to force using mock data
   - Mock data implementations are available for all required data types

2. **Start Script (`start-with-fallback.js`)**:
   - Includes `ALWAYS_USE_MOCK_DATA` flag set to `true`
   - Mock API server is always started for development

3. **Mock Data Notification**:
   - Visual indicator shows users when mock data is being displayed
   - Different messages based on whether it's by configuration or due to connection issues

## How Mock Data Works

1. The application first checks the `useMockApi` configuration flag
2. If true, mock data is used directly without attempting API calls
3. If false, real API calls are attempted with fallback to mock data if they fail
4. The `usingMockData` state is tracked and a notification appears when mock data is being used

## Switching to Real API

When the backend FastAPI endpoints are ready, follow these steps to switch to real API data:

### Step 1: Update Configuration Flags

1. In `frontend/src/services/api.js`:
   ```javascript
   // Change this from true to false
   export const useMockApi = false;
   ```

2. In `frontend/start-with-fallback.js`:
   ```javascript
   // Change this from true to false
   const ALWAYS_USE_MOCK_DATA = false;
   ```

### Step 2: Verify API Endpoints

Ensure that the following endpoints are properly implemented in the backend:

1. `/api/recent-data` - For fetching recent social media posts
2. `/api/topic-model` - For fetching topic modeling results
3. `/api/scraper-status` - For checking scraper status
4. `/api/daily-stats` - For daily statistics

### Step 3: Verify Data Format

Ensure that the API endpoints return data in the expected format:

1. Topic model data should include:
   - `topics`: Array of topic objects with `id`, `name`, and `keywords`
   - `topic_counts_by_date`: Object mapping topic IDs to date counts
   - `metrics`: Object with metrics like coherence_score, diversity_score, etc.
   - `time_range`: Object with start_date and end_date

2. Recent data should include:
   - Array of post objects with standard fields like id, title, text, etc.

### Step 4: Testing

1. Run the application with the updated configuration
2. Check browser console for any API errors
3. Verify that the mock data notification doesn't appear
4. Test all features with real data

## Temporary API Issues

Even after switching to real API, the application will automatically fall back to mock data if:

1. The API server is unavailable
2. API requests fail after multiple retries
3. API endpoints return invalid data

The mock data notification will indicate when this happens.

## Implementation Details

### Key Files

- `frontend/src/services/api.js` - Main API service with mock data configuration
- `frontend/src/mock-api/` - Directory containing mock data and server implementation
- `frontend/start-with-fallback.js` - Startup script with API availability checking
- `frontend/src/components/MockDataNotification.js` - UI notification for mock data usage

### Adding New API Endpoints

When adding new API endpoints:

1. Implement the real API call in `api.js`
2. Add appropriate mock data implementation
3. Use the same pattern of checking `useMockApi` before making real calls
4. Include proper error handling and fallback to mock data 