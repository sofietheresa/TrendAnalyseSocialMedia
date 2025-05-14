// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Alert, Spinner } from 'react-bootstrap';
import Documentation from './components/Documentation';
import { fetchTopics, fetchAnalysisData } from './services/api';
import { DataProvider } from './context/DataContext';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';

function App() {
  const [startDateTime, setStartDateTime] = useState("");
  const [endDateTime, setEndDateTime] = useState("");
  const [topics, setTopics] = useState([]);
  const [sourceCounts, setSourceCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch topics and analysis data
      const topicsData = await fetchTopics(startDateTime, endDateTime);
      
      if (topicsData.top_topics) {
        setTopics(topicsData.top_topics.slice(0, 5));
      } else if (topicsData.topics) {
        setTopics(topicsData.topics.slice(0, 5));
      }
      
      if (topicsData.sources) {
        setSourceCounts(topicsData.sources);
      }
    } catch (err) {
      setError('Fehler beim Laden der Daten. Bitte versuchen Sie es später erneut.');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [startDateTime, endDateTime]);

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    loadData();
  };

  return (
    <Router>
      <DataProvider>
        <div className="App">
          <Navigation />
          <Dashboard />
        </div>
      </DataProvider>
    </Router>
  );
}

// Separate components for different views
function DataView() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadAnalysisData = async () => {
      try {
        setLoading(true);
        const result = await fetchAnalysisData();
        setData(result);
      } catch (err) {
        setError('Fehler beim Laden der Analysedaten');
      } finally {
        setLoading(false);
      }
    };

    loadAnalysisData();
  }, []);

  if (loading) return <div className="loading-container"><Spinner animation="border" /></div>;
  if (error) return <Alert variant="danger">{error}</Alert>;

  return (
    <div className="page-content">
      <h2>Daten-Ansicht</h2>
      <div className="data-grid">
        {data.map((item, index) => (
          <div key={index} className="data-item">
            <h3>{item.title}</h3>
            <p>{item.description}</p>
            {/* Add more data visualization as needed */}
          </div>
        ))}
      </div>
    </div>
  );
}

function LogView() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadLogs = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/logs');
        const data = await response.json();
        setLogs(data);
      } catch (err) {
        setError('Fehler beim Laden der Logs');
      } finally {
        setLoading(false);
      }
    };

    loadLogs();
    // Set up polling for log updates
    const interval = setInterval(loadLogs, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading-container"><Spinner animation="border" /></div>;
  if (error) return <Alert variant="danger">{error}</Alert>;

  return (
    <div className="page-content">
      <h2>System Logs</h2>
      <div className="logs-container">
        {logs.map((log, index) => (
          <div key={index} className={`log-entry log-level-${log.level.toLowerCase()}`}>
            <span className="log-timestamp">{new Date(log.timestamp).toLocaleString()}</span>
            <span className="log-level">{log.level}</span>
            <span className="log-message">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Pipeline() {
  return (
    <div className="page-content">
      <h2>Pipeline</h2>
      <p>Pipeline-Ansicht wird geladen...</p>
    </div>
  );
}

export default App;
