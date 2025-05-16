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

// Import mock data for social media platforms
const { getMockData } = require('./data');

// Configure mock endpoints on the provided Express app
function configureMockServer(app) {
  // Define API routes for pipeline data
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

  // Add social media data endpoints
  app.get('/api/recent-data', (req, res) => {
    const platform = req.query.platform || 'reddit';
    const limit = parseInt(req.query.limit || 10);
    
    const mockData = getMockData(platform, limit);
    
    res.json({
      data: mockData,
      count: mockData.length,
      message: `Mock ${platform} data loaded successfully`
    });
  });

  // Add scraper status endpoint
  app.get('/api/scraper-status', (req, res) => {
    const status = {
      'reddit': {
        'running': true,
        'total_posts': 15426,
        'last_update': new Date().toISOString()
      },
      'tiktok': {
        'running': true,
        'total_posts': 8732,
        'last_update': new Date().toISOString()
      },
      'youtube': {
        'running': true, 
        'total_posts': 5128,
        'last_update': new Date().toISOString()
      }
    };
    
    res.json(status);
  });

  // Add daily stats endpoint
  app.get('/api/daily-stats', (req, res) => {
    // Generate 7 days of stats
    const stats = {
      reddit: [],
      tiktok: [],
      youtube: []
    };
    
    // Generate data for the past 7 days
    for (let i = 0; i < 7; i++) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      stats.reddit.push({
        date: dateStr,
        count: 150 + Math.floor(Math.random() * 100)  // Random between 150-250
      });
      
      stats.tiktok.push({
        date: dateStr,
        count: 100 + Math.floor(Math.random() * 80)   // Random between 100-180
      });
      
      stats.youtube.push({
        date: dateStr,
        count: 50 + Math.floor(Math.random() * 40)    // Random between 50-90
      });
    }
    
    // Sort by date
    stats.reddit.sort((a, b) => a.date.localeCompare(b.date));
    stats.tiktok.sort((a, b) => a.date.localeCompare(b.date));
    stats.youtube.sort((a, b) => a.date.localeCompare(b.date));
    
    res.json(stats);
  });

  // Add topic-model endpoint
  app.post('/api/topic-model', (req, res) => {
    const { start_date, end_date, platforms, num_topics } = req.body;
    
    // Topic model response
    const topicResponse = {
      topics: [
        {
          id: 0,
          name: "AI & Technology",
          keywords: ["artificial", "intelligence", "machine", "learning", "technology", "data", "models", "algorithms", "robots", "future"],
          count: 432
        },
        {
          id: 1,
          name: "Climate Change",
          keywords: ["climate", "change", "environment", "sustainability", "green", "carbon", "emissions", "renewable", "energy", "planet"],
          count: 387
        },
        {
          id: 2,
          name: "Remote Work",
          keywords: ["remote", "work", "office", "home", "productivity", "collaboration", "digital", "tools", "meetings", "flex"],
          count: 356
        },
        {
          id: 3,
          name: "Health & Wellness",
          keywords: ["health", "wellness", "mental", "physical", "exercise", "nutrition", "sleep", "stress", "balance", "mindfulness"],
          count: 289
        },
        {
          id: 4,
          name: "Digital Economy",
          keywords: ["digital", "economy", "crypto", "blockchain", "finance", "markets", "investment", "trends", "business", "transformation"],
          count: 245
        }
      ],
      metrics: {
        coherence_score: 0.79,
        diversity_score: 0.68,
        total_documents: 1709,
        document_coverage: 0.93
      },
      time_range: {
        start_date: start_date || new Date(Date.now() - 7*24*60*60*1000).toISOString().split('T')[0],
        end_date: end_date || new Date().toISOString().split('T')[0]
      },
      special_stopwords: [
        "youtube", "tiktok", "reddit", "video", "watch", "follow", "post", "comment", 
        "user", "channel", "subscribers", "instagram", "twitter", "facebook"
      ],
      topic_counts_by_date: {
        "0": { 
          "2023-12-09": 58, "2023-12-10": 62, "2023-12-11": 59, 
          "2023-12-12": 65, "2023-12-13": 71, "2023-12-14": 68, "2023-12-15": 49 
        },
        "1": { 
          "2023-12-09": 51, "2023-12-10": 54, "2023-12-11": 57, 
          "2023-12-12": 53, "2023-12-13": 59, "2023-12-14": 63, "2023-12-15": 50 
        },
        "2": { 
          "2023-12-09": 46, "2023-12-10": 48, "2023-12-11": 52, 
          "2023-12-12": 54, "2023-12-13": 55, "2023-12-14": 57, "2023-12-15": 44 
        },
        "3": { 
          "2023-12-09": 38, "2023-12-10": 41, "2023-12-11": 39, 
          "2023-12-12": 43, "2023-12-13": 45, "2023-12-14": 48, "2023-12-15": 35 
        },
        "4": { 
          "2023-12-09": 32, "2023-12-10": 34, "2023-12-11": 36, 
          "2023-12-12": 35, "2023-12-13": 38, "2023-12-14": 39, "2023-12-15": 31 
        }
      }
    };
    
    res.json(topicResponse);
  });

  console.log('Mock endpoints configured successfully');
  return app;
}

// Export the configureMockServer function
module.exports = configureMockServer;

// Start the server
app.listen(port, () => {
  console.log(`Mock API server running at http://localhost:${port}`);
}); 