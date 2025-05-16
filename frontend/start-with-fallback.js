/**
 * Start Script for Frontend Application
 * 
 * This script starts the frontend application and manages API availability checks.
 * It ensures proper environment configuration and provides fallback options for development.
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const https = require('https');
const fs = require('fs');

// Flag is always set to false to ensure we only use real data
const ALWAYS_USE_MOCK_DATA = false;

/**
 * Tests if an API endpoint is available
 * @param {string} url - The URL to test
 * @param {number} timeoutMs - Timeout in milliseconds
 * @returns {Promise<boolean>} - True if API is available, false otherwise
 */
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

/**
 * Sets up environment variables for the application
 * @returns {Promise<Object>} - Environment configuration object
 */
const setupEnvironment = async () => {
  // Get API URL from environment or use default
  const apiUrl = process.env.REACT_APP_API_URL || 'https://trendanalysesocialmedia-production.up.railway.app';
  
  console.log(`⚙️ Testing API server availability at: ${apiUrl}`);
  
  // We still check API availability for logging purposes
  let apiAvailable = false;
  
  // Try multiple health endpoints with multiple attempts
  const healthEndpoints = ['/health', '/api/health', '/railway-health', '/api/scraper-status'];
  const maxRetries = 5;
  const timeout = 8000;
  
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
  
  // Always set useMockApi to false regardless of API availability
  const useMockApi = false;
  
  // Set environment variables for child processes
  const env = {
    ...process.env,
    REACT_APP_API_URL: apiUrl,
    REACT_APP_USE_MOCK_API: String(useMockApi) // always 'false'
  };
  
  return { env, apiAvailable, useMockApi };
};

/**
 * Starts the application with proper configuration
 */
const startApp = async () => {
  try {
    const { env, apiAvailable } = await setupEnvironment();
    
    console.log('\n----- Starting Social Media Trend Analysis Application -----');
    console.log(`API Server: ${env.REACT_APP_API_URL}`);
    console.log(`API Available: ${apiAvailable}`);
    console.log(`Using Real Data: true`);
    console.log('------------------------------------------------------\n');
    
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
      
      process.exit();
    };
    
    // Listen for termination signals
    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);
    
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