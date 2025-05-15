/**
 * Start script for the mock API server with improved error handling and logging
 */

const express = require('express');
const cors = require('cors');
const { createServer } = require('http');
const mockServer = require('./server');

// Set the port for the mock API server
const PORT = process.env.MOCK_API_PORT || 3001;

// Create express app and http server
const app = express();
const server = createServer(app);

// Enable CORS and JSON support
app.use(cors());
app.use(express.json());

// Configure mock endpoints
mockServer(app);

// Add status endpoint
app.get('/', (req, res) => {
  res.json({
    status: 'running',
    message: 'Mock API server is running',
    timestamp: new Date().toISOString()
  });
});

// Start the server with error handling
server.listen(PORT, () => {
  console.log(`Mock API server running at http://localhost:${PORT}`);
  console.log('Available endpoints:');
  console.log('- GET /api/mlops/pipelines');
  console.log('- GET /api/mlops/pipelines/:pipelineId');
  console.log('- GET /api/mlops/pipelines/:pipelineId/executions');
  console.log('- POST /api/mlops/pipelines/:pipelineId/execute');
  console.log('- GET /api/mlops/models/:modelName/versions');
  console.log('- GET /api/mlops/models/:modelName/metrics');
  console.log('- GET /api/mlops/models/:modelName/drift');
}).on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`Port ${PORT} is already in use. The mock API server may already be running.`);
  } else {
    console.error('Error starting mock API server:', err);
  }
  process.exit(1);
});

// Handle process termination
process.on('SIGINT', () => {
  console.log('Shutting down mock API server...');
  server.close(() => {
    console.log('Mock API server stopped');
    process.exit(0);
  });
}); 