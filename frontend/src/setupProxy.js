const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Configuration for API URLs
  const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const mockApiUrl = process.env.REACT_APP_MOCK_API_URL || 'http://localhost:3001';
  
  console.log('Proxy configured with API URL:', apiUrl);
  console.log('Mock API URL:', mockApiUrl);
  
  // Proxy API requests to the backend API or our mock API server
  app.use(
    '/api',
    createProxyMiddleware({
      target: apiUrl,
      changeOrigin: true,
      // Enable this to log API requests
      logLevel: 'debug',
      // Fallback to mock server if backend is unavailable
      onError: (err, req, res) => {
        console.log('Proxy error, falling back to mock API:', err);
        // Redirect to mock API
        const mockProxy = createProxyMiddleware({
          target: mockApiUrl,
          changeOrigin: true,
        });
        mockProxy(req, res);
      }
    })
  );
}; 