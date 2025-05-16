/**
 * Application Entry Point
 * 
 * This is the main entry file for the TrendAnalyseSocialMedia React application.
 * It sets up the rendering of the application and loads required resources.
 */

// Font imports for consistent typography
import '@fontsource/sora/300.css'; // Light
import '@fontsource/sora/400.css'; // Regular
import '@fontsource/sora/700.css'; // Bold

// React core imports
import React from 'react';
import ReactDOM from 'react-dom/client';

// Bootstrap framework imports
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

// Application specific imports
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Log environment information for debugging
console.log('React version:', React.version);
console.log('Environment:', process.env.NODE_ENV);
console.log('API URL:', process.env.REACT_APP_API_URL);

// Create root and render application
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Report performance metrics
reportWebVitals(); 