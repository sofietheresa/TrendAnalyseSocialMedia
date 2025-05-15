/**
 * Script to start the frontend with API fallback support
 * This sets up environment variables and starts the server
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const https = require('https');
const fs = require('fs');

// Check if the API server is available with improved reliability
const testApiConnection = (url, timeoutMs = 5000) => {
  return new Promise((resolve) => {
    // Determine http module based on protocol
    const protocol = url.startsWith('https') ? https : http;
    
    console.log(`Testing connection to ${url}...`);
    
    const req = protocol.get(url, { timeout: timeoutMs }, (res) => {
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
    
    req.setTimeout(timeoutMs, () => {
      req.destroy();
      console.log('❌ API connection timed out');
      resolve(false);
    });
  });
};

// Set up environment variables
const setupEnvironment = async () => {
  // Get API URL from environment or use default
  const apiUrl = process.env.REACT_APP_API_URL || 'https://trendanalysesocialmedia-production.up.railway.app';
  const mockApiUrl = 'http://localhost:3001';
  
  console.log(`⚙️ Testing API server availability at: ${apiUrl}`);
  
  // Forcefully prefer real API
  let apiAvailable = false;
  
  // Try multiple health endpoints with multiple attempts
  const healthEndpoints = ['/health', '/api/health', '/railway-health', '/api/scraper-status'];
  const maxRetries = 5; // Increase retries
  const timeout = 8000;  // Increase timeout
  
  for (const endpoint of healthEndpoints) {
    if (apiAvailable) break;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      console.log(`Attempting to connect to ${apiUrl}${endpoint} (attempt ${attempt + 1}/${maxRetries})...`);
      
      try {
        // Try with a longer timeout
        const isAvailable = await testApiConnection(`${apiUrl}${endpoint}`, timeout);
        if (isAvailable) {
          apiAvailable = true;
          console.log(`✅ API server is available at ${apiUrl}${endpoint}`);
          break;
        }
        
        // Wait before retry with increasing delay
        if (attempt < maxRetries - 1) {
          const delay = 1000 * (attempt + 1); // Increasing delay
          console.log(`Waiting ${delay}ms before retry...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      } catch (error) {
        console.error(`Error checking API availability: ${error.message}`);
      }
    }
  }
  
  // Set environment variables for child processes
  const env = {
    ...process.env,
    REACT_APP_API_URL: apiUrl,
    REACT_APP_MOCK_API_URL: mockApiUrl,
    REACT_APP_USE_MOCK_API: 'false' // Force to use real API and handle fallback in code
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