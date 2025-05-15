// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import StatsPanel from './components/StatsPanel';
import DataPage from './components/DataPage';
import Documentation from './components/Documentation';
import ModelEvaluation from './components/ModelEvaluation';
import { fetchTopicModel } from './services/api';

// Message bubble icon component
const MessageIcon = () => (
  <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path 
      d="M60 0C26.9 0 0 24.1 0 53.8C0 83.5 26.9 107.6 60 107.6C93.1 107.6 120 83.5 120 53.8C120 24.1 93.1 0 60 0Z" 
      fill="url(#paint0_linear)" 
    />
    <circle cx="40" cy="54" r="8" fill="#ffffff" fillOpacity="0.9" />
    <circle cx="60" cy="54" r="8" fill="#ffffff" fillOpacity="0.9" />
    <circle cx="80" cy="54" r="8" fill="#ffffff" fillOpacity="0.9" />
    <defs>
      <linearGradient id="paint0_linear" x1="10" y1="10" x2="110" y2="110" gradientUnits="userSpaceOnUse">
        <stop stopColor="#9364eb" />
        <stop offset="0.5" stopColor="#e750ae" />
        <stop offset="1" stopColor="#f8986f" />
      </linearGradient>
    </defs>
  </svg>
);

// Homepage component
const Homepage = () => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState({
    start_date: null,
    end_date: null
  });
  const [dateFilter, setDateFilter] = useState({
    startDate: '',
    endDate: ''
  });
  const [topicCounts, setTopicCounts] = useState({});

  // Fetch topics data
  useEffect(() => {
    const fetchTopicData = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log("Fetching topic data with filters:", dateFilter);
        
        // By default, this will fetch the last 3 days of data
        const response = await fetchTopicModel(
          dateFilter.startDate || null, 
          dateFilter.endDate || null
        );
        
        console.log("Received topic data:", response);
        
        if (response.error) {
          setError(response.error);
          console.error("Error from topic model API:", response.error);
        } else {
          if (Array.isArray(response.topics)) {
            setTopics(response.topics);
            
            // Process topic counts by date if available
            if (response.topic_counts_by_date) {
              setTopicCounts(response.topic_counts_by_date);
            }
          } else {
            console.warn("Invalid topics format:", response.topics);
            setTopics([]);
          }
          
          setTimeRange(response.time_range || {
            start_date: null,
            end_date: null
          });
        }
      } catch (err) {
        console.error("Error fetching topic data:", err);
        setError(err.message || "Fehler beim Laden der Daten");
      } finally {
        setLoading(false);
      }
    };

    fetchTopicData();
  }, [dateFilter.startDate, dateFilter.endDate]);

  // Handle date filter form submission
  const handleDateFilterSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const startDate = formData.get('startDate');
    const endDate = formData.get('endDate');
    
    console.log("Setting date filter:", { startDate, endDate });
    
    setDateFilter({
      startDate,
      endDate
    });
  };

  // Render topic post counts by date
  const renderTopicPostCounts = (topicId) => {
    if (!topicCounts[topicId]) return null;
    
    // Sort dates
    const dates = Object.keys(topicCounts[topicId]).sort();
    
    return (
      <div className="topic-post-counts">
        <h4>Posts per Day</h4>
        <div className="post-counts-grid">
          {dates.map(date => (
            <div key={date} className="post-count-item">
              <div className="post-count-date">{new Date(date).toLocaleDateString()}</div>
              <div className="post-count-value">{topicCounts[topicId][date]}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <main className="app-content">
      {/* Title */}
      <h1 className="main-title">
        <span style={{ fontWeight: 900, letterSpacing: '0.03em' }}>SOCIAL MEDIA</span>
        <br />
        <span style={{ fontWeight: 400, fontSize: '0.8em' }}>Trend Analysis</span>
      </h1>
      
      {/* Date Range Filter */}
      <div className="filter-section">
        <form className="calendar-filter" onSubmit={handleDateFilterSubmit}>
          <label>
            From:
            <input 
              type="date" 
              name="startDate" 
              className="calendar-input" 
              defaultValue={timeRange.start_date}
            />
          </label>
          <label>
            To:
            <input 
              type="date" 
              name="endDate" 
              className="calendar-input" 
              defaultValue={timeRange.end_date}
            />
          </label>
          <button type="submit" className="calendar-filter-btn">
            Analyze
          </button>
        </form>
      </div>
      
      {/* Loading State */}
      {loading && (
        <div className="loading-spinner-container">
          <div className="loading-spinner"></div>
          <p>Analyzing topics...</p>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
      
      {/* Topics Stack */}
      {!loading && !error && topics && topics.length > 0 ? (
        <div className="topics-container">
          <div className="topics-stack-section">
            {topics.slice(0, 5).map((topic, index) => (
              <div key={topic.id || index} className={`topic-stack topic-stack-${index + 1}`}>
                {topic.name || `Topic ${index + 1}`}
              </div>
            ))}
          </div>
          
          {/* Topic Post Counts */}
          <div className="topic-post-counts-section">
            {topics.slice(0, 5).map((topic, index) => topic.id && topicCounts[topic.id] ? (
              <div key={topic.id} className="topic-post-counts-card">
                <h3 className={`topic-name topic-name-${index + 1}`}>{topic.name || `Topic ${index + 1}`}</h3>
                {renderTopicPostCounts(topic.id)}
              </div>
            ) : null)}
          </div>
        </div>
      ) : !loading && !error ? (
        <div className="no-data-message">
          <p>No trending topics found for the selected time period.</p>
          <p>Try selecting a different date range or check back later.</p>
        </div>
      ) : null}
    </main>
  );
};

// Stats page component
const StatsPage = () => {
  return (
    <main className="app-content">
      <h1 className="page-title">Statistics Overview</h1>
      <StatsPanel />
    </main>
  );
};

// Simple placeholder for other pages
const PlaceholderPage = ({ title }) => (
  <main className="app-content">
    <h1 className="page-title">{title}</h1>
    <div className="placeholder-content">
      <p>This page is under construction.</p>
    </div>
  </main>
);

function App() {
  const [activePage, setActivePage] = useState('home');

  return (
    <Router>
      <div className="App">
        {/* Navigation */}
        <nav className="app-nav">
          <Link 
            to="/" 
            className="nav-link" 
            onClick={() => setActivePage('home')}
            style={{ fontWeight: activePage === 'home' ? 700 : 400 }}
          >
            Startseite
          </Link>
          <Link 
            to="/pipeline" 
            className="nav-link" 
            onClick={() => setActivePage('pipeline')}
            style={{ fontWeight: activePage === 'pipeline' ? 700 : 400 }}
          >
            Pipeline
          </Link>
          <Link 
            to="/stats" 
            className="nav-link" 
            onClick={() => setActivePage('stats')}
            style={{ fontWeight: activePage === 'stats' ? 700 : 400 }}
          >
            Statistiken
          </Link>
          <Link 
            to="/data" 
            className="nav-link" 
            onClick={() => setActivePage('data')}
            style={{ fontWeight: activePage === 'data' ? 700 : 400 }}
          >
            Data
          </Link>
          <Link 
            to="/evaluation" 
            className="nav-link" 
            onClick={() => setActivePage('evaluation')}
            style={{ fontWeight: activePage === 'evaluation' ? 700 : 400 }}
          >
            Modell-Evaluation
          </Link>
          <Link 
            to="/docs" 
            className="nav-link" 
            onClick={() => setActivePage('docs')}
            style={{ fontWeight: activePage === 'docs' ? 700 : 400 }}
          >
            Doku
          </Link>
        </nav>
        
        {/* Page Routes */}
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="/pipeline" element={<PlaceholderPage title="Pipeline" />} />
          <Route path="/data" element={<DataPage />} />
          <Route path="/evaluation" element={<ModelEvaluation />} />
          <Route path="/docs" element={<Documentation />} />
        </Routes>
        
        {/* Footer */}
        <footer className="app-footer">
          <p>© 2025 TrendAnalyseSocialMedia</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
