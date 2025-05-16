/**
 * React Development Proxy Configuration
 * 
 * This file configures proxy settings for local development to handle API requests.
 * It forwards API requests to the backend server to avoid CORS issues.
 */
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Configuration for API URL
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  
  console.log('Proxy configured with API URL:', apiUrl);
  
  // Proxy API requests to the backend server
  app.use(
    '/api',
    createProxyMiddleware({
      target: apiUrl,
      changeOrigin: true,
      logLevel: 'debug', // Set to 'debug' to log requests, 'silent' for production
      onError: (err, req, res) => {
        console.error('API proxy error:', err);
        res.statusCode = 500;
        res.end(`Backend API unavailable: ${err.message}`);
      }
    })
  );
}; 