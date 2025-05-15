const express = require('express');
const cors = require('cors');
const app = express();
const port = 3001;

// Enable CORS
app.use(cors());
app.use(express.json());

// Mock data
const pipelines = {
  "trend_analysis": {
    "name": "Trend Analysis Pipeline",
    "description": "Analyzes social media data to identify trending topics",
    "steps": [
      {"id": "data_collection", "name": "Data Collection", "description": "Collects data from social media APIs", "status": "completed", "runtime": "00:18:22"},
      {"id": "preprocessing", "name": "Preprocessing", "description": "Cleans and prepares data for analysis", "status": "completed", "runtime": "00:12:25"},
      {"id": "topic_modeling", "name": "Topic Modeling", "description": "Identifies emerging topics in the data", "status": "completed", "runtime": "00:32:44"},
      {"id": "sentiment_analysis", "name": "Sentiment Analysis", "description": "Determines sentiment for each post", "status": "completed", "runtime": "00:09:18"},
      {"id": "trend_detection", "name": "Trend Detection", "description": "Identifies emerging trends in topics", "status": "completed", "runtime": "00:06:42"}
    ],
    "lastRun": "2023-12-15T14:30:22",
    "nextScheduledRun": getTomorrowDate(6),
    "averageRuntime": "00:51:48",
    "status": "completed"
  },
  "realtime_monitoring": {
    "name": "Realtime Monitoring Pipeline",
    "description": "Monitors social media in real-time for emerging trends",
    "steps": [
      {"id": "stream_ingestion", "name": "Stream Ingestion", "description": "Collects streaming data from social APIs", "status": "completed", "runtime": "00:01:02"},
      {"id": "realtime_preprocessing", "name": "Realtime Preprocessing", "description": "Preprocesses streaming data", "status": "completed", "runtime": "00:00:48"},
      {"id": "anomaly_detection", "name": "Anomaly Detection", "description": "Detects unusual patterns in real-time", "status": "running", "runtime": "00:02:15"},
      {"id": "alert_generation", "name": "Alert Generation", "description": "Generates alerts for detected anomalies", "status": "pending", "runtime": "00:00:00"}
    ],
    "lastRun": "2023-12-15T16:45:10",
    "nextScheduledRun": getTomorrowDate(6),
    "averageRuntime": "00:10:22",
    "status": "running"
  },
  "model_training": {
    "name": "Model Training Pipeline",
    "description": "Trains and deploys ML models for trend prediction",
    "steps": [
      {"id": "data_collection", "name": "Data Collection", "description": "Collects historical data for training", "status": "completed", "runtime": "00:12:45"},
      {"id": "feature_engineering", "name": "Feature Engineering", "description": "Creates features for model training", "status": "completed", "runtime": "00:18:20"},
      {"id": "model_training", "name": "Model Training", "description": "Trains prediction models", "status": "completed", "runtime": "01:24:56"},
      {"id": "model_validation", "name": "Model Validation", "description": "Validates models against test data", "status": "failed", "runtime": "00:05:23"}
    ],
    "lastRun": "2023-12-14T09:15:33",
    "nextScheduledRun": getTomorrowDate(6),
    "averageRuntime": "02:01:24",
    "status": "failed"
  }
};

const executions = [
  {"id": "exec-001", "pipelineId": "trend_analysis", "startTime": "2023-12-15T14:30:22", "endTime": "2023-12-15T15:22:10", "status": "completed", "trigger": "scheduled"},
  {"id": "exec-002", "pipelineId": "trend_analysis", "startTime": "2023-12-14T14:30:15", "endTime": "2023-12-14T15:24:02", "status": "completed", "trigger": "scheduled"},
  {"id": "exec-003", "pipelineId": "realtime_monitoring", "startTime": "2023-12-15T16:45:10", "endTime": null, "status": "running", "trigger": "manual"},
  {"id": "exec-004", "pipelineId": "model_training", "startTime": "2023-12-14T09:15:33", "endTime": "2023-12-14T11:16:57", "status": "failed", "trigger": "manual"},
  {"id": "exec-005", "pipelineId": "trend_analysis", "startTime": "2023-12-13T14:30:18", "endTime": "2023-12-13T15:25:33", "status": "completed", "trigger": "scheduled"}
];

// Helper function to get tomorrow's date with specific hours
function getTomorrowDate(hoursInterval) {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  // Set to the next 6-hour interval (0, 6, 12, 18)
  const currentHour = new Date().getHours();
  const nextIntervalHour = Math.ceil(currentHour / hoursInterval) * hoursInterval;
  tomorrow.setHours(nextIntervalHour, 0, 0, 0);
  
  return tomorrow.toISOString();
}

// Define API routes
app.get('/api/mlops/pipelines', (req, res) => {
  res.json(pipelines);
});

app.get('/api/mlops/pipelines/:pipelineId', (req, res) => {
  const { pipelineId } = req.params;
  const pipeline = pipelines[pipelineId];
  
  if (!pipeline) {
    return res.status(404).json({ error: `Pipeline ${pipelineId} not found` });
  }
  
  res.json(pipeline);
});

app.get('/api/mlops/pipelines/:pipelineId/executions', (req, res) => {
  const { pipelineId } = req.params;
  const pipelineExecutions = executions.filter(exec => exec.pipelineId === pipelineId);
  
  res.json(pipelineExecutions);
});

app.post('/api/mlops/pipelines/:pipelineId/execute', (req, res) => {
  const { pipelineId } = req.params;
  
  if (!pipelines[pipelineId]) {
    return res.status(404).json({ error: `Pipeline ${pipelineId} not found` });
  }
  
  const executionId = `exec-${Date.now()}`;
  
  res.json({
    execution_id: executionId,
    pipeline_id: pipelineId,
    status: "started",
    startTime: new Date().toISOString(),
    message: `Pipeline ${pipelineId} execution started with ID ${executionId}`
  });
});

// Add model endpoints
app.get('/api/mlops/models/:modelName/versions', (req, res) => {
  const { modelName } = req.params;
  
  const versions = [
    {"id": "v1.0.2", "name": `${modelName} v1.0.2`, "date": new Date().toISOString(), "status": "production"},
    {"id": "v1.0.1", "name": `${modelName} v1.0.1`, "date": new Date(Date.now() - 7*24*60*60*1000).toISOString(), "status": "archived"},
    {"id": "v1.0.0", "name": `${modelName} v1.0.0`, "date": new Date(Date.now() - 14*24*60*60*1000).toISOString(), "status": "archived"}
  ];
  
  res.json(versions);
});

app.get('/api/mlops/models/:modelName/metrics', (req, res) => {
  const { modelName } = req.params;
  const { version } = req.query;
  
  const metrics = {
    coherence_score: 0.78,
    diversity_score: 0.65,
    document_coverage: 0.92,
    total_documents: 15764,
    uniqueness_score: 0.81,
    silhouette_score: 0.72,
    topic_separation: 0.68,
    avg_topic_similarity: 0.43,
    execution_time: 183.4,
    topic_quality: 0.75
  };
  
  res.json(metrics);
});

app.get('/api/mlops/models/:modelName/drift', (req, res) => {
  const { modelName } = req.params;
  const { version } = req.query;
  
  const drift = {
    timestamp: new Date().toISOString(),
    dataset_drift: true,
    share_of_drifted_columns: 0.25,
    drifted_columns: ["text_length", "sentiment_score", "engagement_rate"]
  };
  
  res.json(drift);
});

// Start the server
app.listen(port, () => {
  console.log(`Mock API server running at http://localhost:${port}`);
}); 