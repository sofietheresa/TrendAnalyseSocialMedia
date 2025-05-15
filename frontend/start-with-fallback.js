/**
 * Script to start the frontend with API fallback support
 * This sets up environment variables and starts the server
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

// Check if the API server is available
const testApiConnection = (url) => {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      if (res.statusCode === 200) {
        console.log('✅ API server is available');
        resolve(true);
      } else {
        console.log(`❌ API server returned status: ${res.statusCode}`);
        resolve(false);
      }
    });
    
    req.on('error', (err) => {
      console.log(`❌ API server is not available: ${err.message}`);
      resolve(false);
    });
    
    req.setTimeout(3000, () => {
      req.destroy();
      console.log('❌ API connection timed out');
      resolve(false);
    });
  });
};

// Set up environment variables
const setupEnvironment = async () => {
  // Get API URL from environment or use default
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const mockApiUrl = 'http://localhost:3001';
  
  console.log(`⚙️ Checking API server at: ${apiUrl}`);
  
  // Check if the API server is available
  const apiAvailable = await testApiConnection(`${apiUrl}/health`);
  
  // Set environment variables for child processes
  const env = {
    ...process.env,
    REACT_APP_API_URL: apiUrl,
    REACT_APP_MOCK_API_URL: mockApiUrl,
    REACT_APP_USE_MOCK_API: String(!apiAvailable)
  };
  
  return { env, apiAvailable };
};

// Start the application
const startApp = async () => {
  try {
    const { env, apiAvailable } = await setupEnvironment();
    
    console.log('\n----- Starting Social Media Trend Analysis Application -----');
    console.log(`API Server: ${env.REACT_APP_API_URL}`);
    console.log(`Mock API: ${env.REACT_APP_MOCK_API_URL}`);
    console.log(`Using Mock API: ${env.REACT_APP_USE_MOCK_API}`);
    console.log('------------------------------------------------------\n');
    
    // Start the mock API server if the real API is not available
    let mockServer = null;
    if (!apiAvailable) {
      console.log('⚠️ API server is not available, starting mock API server...');
      
      mockServer = spawn('node', [path.join(__dirname, 'src', 'mock-api', 'start-mock-api.js')], {
        env,
        stdio: 'inherit'
      });
      
      // Wait a moment for the mock server to start
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Start the React development server
    const reactApp = spawn('npm', ['run', 'start'], { 
      env,
      stdio: 'inherit',
      shell: process.platform === 'win32'
    });
    
    // Handle process termination
    const cleanup = () => {
      console.log('\n🛑 Shutting down...');
      
      if (reactApp) {
        reactApp.kill();
      }
      
      if (mockServer) {
        mockServer.kill();
      }
      
      process.exit();
    };
    
    // Listen for termination signals
    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);
    
    // Handle child process exit
    if (mockServer) {
      mockServer.on('exit', (code) => {
        console.log(`📊 Mock API server exited with code ${code}`);
      });
    }
    
    reactApp.on('exit', (code) => {
      console.log(`🌐 React app exited with code ${code}`);
      cleanup();
    });
    
  } catch (error) {
    console.error('❌ Error starting application:', error);
    process.exit(1);
  }
};

// Start the application
startApp(); 