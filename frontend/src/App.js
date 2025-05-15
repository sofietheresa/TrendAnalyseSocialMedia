// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Alert, Spinner } from 'react-bootstrap';
import { fetchScraperStatus, fetchDailyStats } from './services/api';
import Dashboard from './components/Dashboard';

function App() {
  // Basic, reliable UI that doesn't depend on complex data fetching initially
  return (
    <Router>
      <div className="App">
        <header className="app-header">
          <h1>Social Media Trend Analysis</h1>
          <div className="debug-message">Debug Mode: Basic Layout</div>
        </header>
        
        <main className="app-content">
          <DebugDashboard />
        </main>
        
        <footer className="app-footer">
          <p>© 2025 TrendAnalyseSocialMedia</p>
        </footer>
      </div>
    </Router>
  );
}

// Simple debug component to show basic UI
function DebugDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    const testConnection = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log("Testing API connection...");
        
        // Try to fetch data with error handling
        try {
          const scraperStatus = await fetchScraperStatus();
          const dailyStats = await fetchDailyStats();
          setData({ status: scraperStatus, stats: dailyStats });
          console.log("API connection successful:", { scraperStatus, dailyStats });
        } catch (err) {
          console.error("API connection failed:", err);
          setError(`API connection failed: ${err.message}`);
        }
      } catch (err) {
        console.error("General error:", err);
        setError(`General error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    testConnection();
  }, []);

  return (
    <div className="debug-dashboard">
      <h2>Debug Dashboard</h2>
      
      {loading && (
        <div className="debug-section">
          <h3>Loading data...</h3>
          <Spinner animation="border" />
        </div>
      )}
      
      {error && (
        <div className="debug-section">
          <h3>Error</h3>
          <Alert variant="danger">{error}</Alert>
        </div>
      )}
      
      {!loading && !error && data && (
        <div className="debug-section">
          <h3>Connection Successful</h3>
          <p>API is responding correctly.</p>
          
          <div className="debug-data">
            <h4>Scraper Status:</h4>
            <pre>{JSON.stringify(data.status, null, 2)}</pre>
            
            <h4>Daily Stats:</h4>
            <pre>{JSON.stringify(data.stats, null, 2)}</pre>
          </div>
        </div>
      )}
      
      {!loading && !error && !data && (
        <div className="debug-section">
          <h3>No Data</h3>
          <p>API responded without errors but no data was returned.</p>
        </div>
      )}
    </div>
  );
}

export default App;
