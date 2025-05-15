import '@fontsource/sora/300.css';
import '@fontsource/sora/400.css';
import '@fontsource/sora/700.css';
import React from 'react';
import ReactDOM from 'react-dom/client';

// Bootstrap CSS and JS
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Log the React version
console.log('React version:', React.version);
console.log('Environment:', process.env.NODE_ENV);
console.log('API URL:', process.env.REACT_APP_API_URL);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

reportWebVitals(); 