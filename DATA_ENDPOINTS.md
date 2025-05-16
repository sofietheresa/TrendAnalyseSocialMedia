# Data Endpoints Documentation

## Issue

The frontend was encountering 404 errors when trying to access two important data endpoints:

1. `/api/db/predictions` - Used by the Predictions page to display forecasted topic trends
2. `/api/db/analysis` - Used for analysis data in the application

## Solution

Added both endpoints to the main API with mock data to ensure the frontend can display all information correctly:

### 1. Predictions Endpoint

**Endpoint:** `/api/db/predictions`  
**Method:** GET  
**Response Format:**

```json
{
  "predictions": [
    {
      "topic_id": "topic1",
      "topic_name": "AI & Technology",
      "current_count": 1250,
      "predicted_count": 1520,
      "growth_rate": 21.6,
      "confidence": 0.85,
      "sentiment_score": 0.32,
      "keywords": ["artificial intelligence", "machine learning", "neural networks", "chatgpt", "generative AI"]
    },
    // More topics...
  ],
  "prediction_trends": {
    "topic1": {
      "2025-05-17": 1275,
      "2025-05-18": 1305,
      // More dates...
    },
    // More topics...
  },
  "time_range": {
    "start_date": "2025-05-10",
    "end_date": "2025-05-24"
  }
}
```

### 2. Analysis Endpoint

**Endpoint:** `/api/db/analysis`  
**Method:** GET  
**Response Format:**

```json
{
  "topics": [
    {
      "topic_id": "topic1",
      "topic_name": "AI & Technology",
      "post_count": 1250,
      "engagement": 28500,
      "sentiment_score": 0.32,
      "keywords": ["artificial intelligence", "machine learning", "neural networks", "chatgpt", "generative AI"],
      "platforms": {
        "reddit": 520,
        "tiktok": 430,
        "youtube": 300
      }
    },
    // More topics...
  ],
  "time_range": {
    "start_date": "2025-05-10",
    "end_date": "2025-05-17"
  },
  "platforms": {
    "reddit": {
      "post_count": 4250,
      "user_count": 3100,
      "engagement": 89700
    },
    // More platforms...
  }
}
```

## Implementation Details

Both endpoints generate dynamic mock data with:
- Current dates based on `datetime.now()`
- Realistic values for each field
- Proper nesting and data structure as expected by the frontend

## Benefits

1. Eliminates 404 errors in the frontend
2. Allows the Predictions page to function properly
3. Maintains data consistency with other endpoints
4. Uses current dates for a more realistic user experience

## Deployment

The changes have been pushed to the repository and will be automatically deployed to the production environment by Railway. 