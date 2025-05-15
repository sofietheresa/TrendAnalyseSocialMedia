const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests to the FastAPI backend or our mock API server
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',  // FastAPI backend URL
      changeOrigin: true,
      // Enable this to log API requests
      logLevel: 'debug',
      // Fallback to mock server if backend is unavailable
      onError: (err, req, res) => {
        console.log('Proxy error, falling back to mock API:', err);
        // Redirect to mock API
        const mockProxy = createProxyMiddleware({
          target: 'http://localhost:3001',
          changeOrigin: true,
        });
        mockProxy(req, res);
      }
    })
  );
}; 