// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import StatsPanel from './components/StatsPanel';
import DataPage from './components/DataPage';
import Documentation from './components/Documentation';
import ModelEvaluation from './components/ModelEvaluation';
import PipelinePage from './components/PipelinePage';
import PredictionsPage from './components/PredictionsPage';
import { fetchTopicModel } from './services/api';
import { Line } from 'react-chartjs-2';
import MockDataNotification from './components/MockDataNotification';
import AccessGate from './components/AccessGate';

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
  const [topicTrends, setTopicTrends] = useState([]);
  const [topicSentiments, setTopicSentiments] = useState({});

  // Get sentiment emoji based on sentiment score
  const getSentimentEmoji = (sentiment) => {
    if (!sentiment && sentiment !== 0) return '';
    
    if (sentiment >= 0.5) return '😄'; // Very positive
    if (sentiment >= 0.1) return '🙂'; // Positive
    if (sentiment > -0.1) return '😐'; // Neutral
    if (sentiment > -0.5) return '🙁'; // Negative
    return '😠'; // Very negative
  };

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
            // Filter out topics with id -1 or name "Other"
            const filteredTopics = response.topics.filter(topic => 
              topic.id !== -1 && topic.name !== "Other" && topic.name !== "-1"
            );
            
            setTopics(filteredTopics);
            
            // Process topic counts by date if available
            if (response.topic_counts_by_date) {
              setTopicCounts(response.topic_counts_by_date);
              
              // Process topic trends data for the chart
              processTopicTrends(filteredTopics, response.topic_counts_by_date);
            }
            
            // Generate mock sentiment data for topics (this would be replaced with real data)
            const sentiments = generateMockSentiments(filteredTopics);
            setTopicSentiments(sentiments);
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

  // Generate random sentiment scores for each topic (mock data for demo)
  const generateMockSentiments = (topics) => {
    return topics.reduce((acc, topic) => {
      if (topic.id) {
        // Generate a random sentiment between -0.8 and 0.8
        acc[topic.id] = (Math.random() * 1.6 - 0.8).toFixed(2);
      }
      return acc;
    }, {});
  };

  // Process topic trends data for the chart
  const processTopicTrends = (topTopics, countsByDate) => {
    if (!topTopics || !countsByDate) return;
    
    console.log("Processing trends for topics:", topTopics);
    console.log("With counts by date:", countsByDate);
    
    // Filter out topics with id -1 or name "Other" and skip the first topic
    const filteredTopics = topTopics.filter((topic, index) => 
      topic.id !== -1 && topic.name !== "Other" && topic.name !== "-1" && index > 0
    );
    
    // Get all unique dates across all topics
    const allDates = new Set();
    
    // For each topic, collect all available dates
    filteredTopics.forEach(topic => {
      if (topic.id && countsByDate[topic.id]) {
        Object.keys(countsByDate[topic.id]).forEach(date => allDates.add(date));
      } else {
        console.warn("Topic missing id or no counts available:", topic);
      }
    });
    
    // Sort dates chronologically
    const sortedDates = Array.from(allDates).sort();
    
    if (sortedDates.length === 0) {
      console.warn("No dates found for any topics");
      return;
    }
    
    // Prepare chart data
    const trendsData = {
      labels: sortedDates.map(date => new Date(date).toLocaleDateString('de-DE')),
      datasets: filteredTopics.filter(topic => topic.id && countsByDate[topic.id]).map((topic, index) => {
        // Generate colors based on index
        const colors = [
          '#232252', // dark blue
          '#2e6cdb', // medium blue
          '#9364eb', // purple
          '#e750ae', // pink
          '#f8986f'  // orange
        ];
        
        // Check if this topic has any non-zero counts
        const hasData = sortedDates.some(date => 
          topic.id && 
          countsByDate[topic.id] && 
          countsByDate[topic.id][date] && 
          countsByDate[topic.id][date] > 0
        );
        
        console.log(`Topic ${topic.name || index} has data: ${hasData}`);
        
        return {
          label: topic.name || `Topic ${index + 1}`,
          data: sortedDates.map(date => {
            const count = topic.id && countsByDate[topic.id] && countsByDate[topic.id][date] 
              ? countsByDate[topic.id][date] 
              : 0;
            return count;
          }),
          borderColor: colors[index % colors.length],
          backgroundColor: `${colors[index % colors.length]}22`, // Add transparency
          tension: 0.3,
          fill: index === 0 // Only fill the first dataset
        };
      })
    };
    
    console.log("Generated trends data:", trendsData);
    setTopicTrends(trendsData);
  };

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
              <div className="post-count-date">{new Date(date).toLocaleDateString('de-DE')}</div>
              <div className="post-count-value">{topicCounts[topicId][date]}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Chart options for trend visualization
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: {
            family: 'Sora, Arial, sans-serif',
            size: 14
          },
          color: '#232252'
        }
      },
      title: {
        display: true,
        text: 'Topic Trends Over Time',
        font: {
          family: 'Sora, Arial, sans-serif',
          size: 18,
          weight: 'bold'
        },
        color: '#232252'
      },
      tooltip: {
        callbacks: {
          title: (context) => {
            return `Date: ${context[0].label}`;
          },
          label: (context) => {
            return `${context.dataset.label}: ${context.raw} posts`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        },
        ticks: {
          font: {
            family: 'Sora, Arial, sans-serif'
          },
          color: '#232252'
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(46, 108, 219, 0.1)'
        },
        ticks: {
          font: {
            family: 'Sora, Arial, sans-serif'
          },
          color: '#232252'
        }
      }
    }
  };

    return (    <main className="app-content">      {/* Title with proper margin for fixed navbar */}      <h1 className="main-title" style={{ marginTop: '20px', marginBottom: '40px' }}>        <span style={{ fontWeight: 900, letterSpacing: '0.03em' }}>SOCIAL MEDIA</span>        <br />        <span style={{ fontWeight: 400, fontSize: '0.8em' }}>Trend Analysis</span>      </h1>
      
      {/* Date Range Filter - Position unchanged */}
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
      
      {/* Topics Stack - Now centered */}
      {!loading && !error && topics && topics.length > 0 ? (
        <div className="topics-container">
          <div className="topics-stack-section" style={{ alignItems: 'center', textAlign: 'center' }}>
            {topics.slice(1, 6).map((topic, index) => (
              <div 
                key={topic.id || index} 
                className={`topic-stack topic-stack-${index + 1}`}
                style={{ justifyContent: 'center', textAlign: 'center', margin: '15px auto' }}
              >
                {topic.name || `Topic ${index + 1}`} {topicSentiments[topic.id] && 
                  <span className="sentiment-emoji" title={`Sentiment: ${topicSentiments[topic.id]}`}>
                    {getSentimentEmoji(parseFloat(topicSentiments[topic.id]))}
                  </span>
                }
              </div>
            ))}
          </div>
          
          {/* Topic Trends Chart - New section */}
          {topicTrends.datasets && topicTrends.datasets.length > 0 && (
            <div className="topic-trends-chart" style={{ 
              marginTop: '40px',
              marginBottom: '40px',
              width: '100%',
              maxWidth: '1000px',
              margin: '40px auto',
              height: '400px',
              backgroundColor: 'rgba(255, 255, 255, 0.85)',
              padding: '20px',
              borderRadius: '15px',
              boxShadow: '0 4px 30px rgba(0, 0, 0, 0.05)'
            }}>
              <Line
                data={topicTrends}
                options={chartOptions}
                height={350}
              />
              {dateFilter.startDate && dateFilter.endDate && (
                <div className="selected-range-info" style={{
                  textAlign: 'center',
                  marginTop: '10px',
                  fontSize: '0.9rem',
                  color: '#64748B'
                }}>
                  Selected range: {new Date(dateFilter.startDate).toLocaleDateString('de-DE')} - {new Date(dateFilter.endDate).toLocaleDateString('de-DE')}
                </div>
              )}
            </div>
          )}
          
          {/* Topic Post Counts */}
          <div className="topic-post-counts-section">
            {topics.slice(1, 6).map((topic, index) => topic.id && topicCounts[topic.id] ? (
              <div key={topic.id} className="topic-post-counts-card">
                <h3 className={`topic-name topic-name-${index + 1}`}>
                  {topic.name || `Topic ${index + 1}`}
                  {topicSentiments[topic.id] && 
                    <span className="sentiment-emoji" style={{ marginLeft: '10px' }} title={`Sentiment: ${topicSentiments[topic.id]}`}>
                      {getSentimentEmoji(parseFloat(topicSentiments[topic.id]))}
                    </span>
                  }
                </h3>
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
      <AccessGate>
        <div className="App">
          {/* Navigation */}
          <nav className="app-nav">
            {/* App Title on the left */}
            <div className="app-nav-title">
              <Link to="/" onClick={() => setActivePage('home')}>
                <span className="nav-title-text">SOCIAL MEDIA</span>
                <span className="nav-subtitle-text">TRENDANALYSE</span>
              </Link>
            </div>
            
            {/* Navigation Links */}
            <div className="nav-links-container">
              <Link 
                to="/predictions" 
                className={`nav-link ${activePage === 'predictions' ? 'active-nav-link' : ''}`} 
                onClick={() => setActivePage('predictions')}
              >
                Predictions
              </Link>
              <Link 
                to="/pipeline" 
                className={`nav-link ${activePage === 'pipeline' ? 'active-nav-link' : ''}`} 
                onClick={() => setActivePage('pipeline')}
              >
                Pipeline
              </Link>
              <Link 
                to="/stats" 
                className={`nav-link ${activePage === 'stats' ? 'active-nav-link' : ''}`} 
                onClick={() => setActivePage('stats')}
              >
                Statistiken
              </Link>
              <Link 
                to="/data" 
                className={`nav-link ${activePage === 'data' ? 'active-nav-link' : ''}`} 
                onClick={() => setActivePage('data')}
              >
                Data
              </Link>
              <Link 
                to="/evaluation" 
                className={`nav-link ${activePage === 'evaluation' ? 'active-nav-link' : ''}`} 
                onClick={() => setActivePage('evaluation')}
              >
                Modell-Evaluation
              </Link>
              <Link 
                to="/docs" 
                className={`nav-link ${activePage === 'docs' ? 'active-nav-link' : ''}`} 
                onClick={() => setActivePage('docs')}
              >
                Doku
              </Link>
            </div>
          </nav>
          
          {/* Page Routes */}
          <Routes>
            <Route path="/" element={<Homepage />} />
            <Route path="/predictions" element={<PredictionsPage />} />
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/data" element={<DataPage />} />
            <Route path="/evaluation" element={<ModelEvaluation />} />
            <Route path="/docs" element={<Documentation />} />
          </Routes>
          
          {/* Footer */}
          <footer className="app-footer">
            <p>© 2025 TrendAnalyseSocialMedia</p>
          </footer>
          
          {/* Add the mock data notification that will only show when mock data is used */}
          <MockDataNotification />
        </div>
      </AccessGate>
    </Router>
  );
}

export default App;
