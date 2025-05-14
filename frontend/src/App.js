// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Alert, Spinner } from 'react-bootstrap';
import Documentation from './components/Documentation';
import { fetchTopics, fetchAnalysisData } from './services/api';

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
      <div className="gradient-bg">
        <nav className="app-nav">
          <Link to="/" className="nav-link">Startseite</Link>
          <Link to="/daten" className="nav-link">Daten</Link>
          <Link to="/logs" className="nav-link">Logs</Link>
          <Link to="/pipeline" className="nav-link">Pipeline</Link>
          <Link to="/doku" className="nav-link">Doku</Link>
        </nav>

        {error && (
          <Alert variant="danger" className="m-3">
            {error}
          </Alert>
        )}

        <Routes>
          <Route path="/" element={
            <>
              <header className="App-header">
                <h1 className="main-title">SOCIAL MEDIA Trend Analysis</h1>
              </header>
              <main className="App-main">
                <section className="filter-section">
                  <form className="calendar-filter" onSubmit={handleFilterSubmit}>
                    <label>
                      Von:
                      <input
                        type="datetime-local"
                        value={startDateTime}
                        onChange={e => setStartDateTime(e.target.value)}
                        className="calendar-input"
                      />
                    </label>
                    <span className="calendar-separator">bis</span>
                    <label>
                      Bis:
                      <input
                        type="datetime-local"
                        value={endDateTime}
                        onChange={e => setEndDateTime(e.target.value)}
                        className="calendar-input"
                      />
                    </label>
                    <button type="submit" className="calendar-filter-btn">
                      Filtern
                    </button>
                  </form>
                </section>

                {loading ? (
                  <div className="loading-container">
                    <Spinner animation="border" role="status">
                      <span className="visually-hidden">Laden...</span>
                    </Spinner>
                  </div>
                ) : (
                  <>
                    <section className="topics-stack-section">
                      {topics.slice(0, 3).map((topic, i) => (
                        <div
                          key={topic.topic}
                          className={`topic-stack topic-stack-${i+1}`}
                          style={{
                            fontFamily: 'Arial, sans-serif',
                            fontWeight: i === 0 ? 900 : 700,
                            fontSize: i === 0 ? '3.2rem' : i === 1 ? '2.4rem' : '2rem',
                            opacity: i === 0 ? 1 : i === 1 ? 0.7 : 0.5,
                            textAlign: 'center',
                            color: '#2a2253',
                            margin: 0,
                            marginBottom: '0.2em',
                            letterSpacing: '0.01em',
                            lineHeight: 1.1
                          }}
                        >
                          {topic.topic}
                        </div>
                      ))}
                    </section>

                    <section className="postcount-row">
                      <div className="postcount-grid">
                        {Object.entries(sourceCounts).slice(0, 3).map(([quelle, anzahl], i) => (
                          <div key={quelle} className="postcount-col">
                            <div className="postcount-number">{String(i+1).padStart(2, '0')}</div>
                            <div className="postcount-source">{quelle}</div>
                            <div className="postcount-value">{anzahl}</div>
                          </div>
                        ))}
                      </div>
                    </section>
                  </>
                )}
              </main>
            </>
          } />
          <Route path="/daten" element={<DataView />} />
          <Route path="/logs" element={<LogView />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/doku" element={<Documentation />} />
        </Routes>
      </div>
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
