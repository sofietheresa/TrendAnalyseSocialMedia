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
import { fetchTopicModel, fetchPredictions, fetchRecentData, fetchPostsByTopic } from './services/api';
import { Line } from 'react-chartjs-2';
import AccessGate from './components/AccessGate';

/**
 * SVG Message Bubble Icon Component
 * Visual indicator for messaging functionality
 */
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

/**
 * Homepage Component
 * Main landing page with topic visualization and analytics dashboard
 */
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
  const [selectedTopicId, setSelectedTopicId] = useState(null);
  const [topicPosts, setTopicPosts] = useState([]);
  const [loadingPosts, setLoadingPosts] = useState(false);

  /**
   * Converts sentiment score to appropriate emoji representation
   * @param {number} sentiment - Sentiment score in range [-1, 1]
   * @returns {string} Emoji representing the sentiment level
   */
  const getSentimentEmoji = (sentiment) => {
    if (!sentiment && sentiment !== 0) return '';
    
    if (sentiment >= 0.5) return '😄'; // Very positive
    if (sentiment >= 0.1) return '🙂'; // Positive
    if (sentiment > -0.1) return '😐'; // Neutral
    if (sentiment > -0.5) return '🙁'; // Negative
    return '😠'; // Very negative
  };

  /**
   * Handles topic click event to show related posts
   * @param {string} topicId - ID of the selected topic
   * @param {string} topicName - Name of the selected topic
   * @returns {Promise<void>}
   */
  const handleTopicClick = async (topicId, topicName) => {
    try {
      setLoadingPosts(true);
      setSelectedTopicId(topicId);
      
      // Fetch posts related to this topic
      console.log(`Fetching posts for topic ID ${topicId}: ${topicName}`);
      
      try {
        // Use our dedicated API function to fetch posts by topic from the database
        const posts = await fetchPostsByTopic(topicId);
        
        if (posts && posts.length > 0) {
          console.log(`Found ${posts.length} posts for topic ${topicName}`);
          setTopicPosts(posts);
          return;
        } else {
          console.log(`No posts found for topic ${topicName} using fetchPostsByTopic`);
        }
      } catch (err) {
        console.warn("Failed to fetch posts using fetchPostsByTopic:", err);
      }
      
      // Fallback to recent data filtering by topic ID
      try {
        const recentData = await fetchRecentData('all', 20);
        if (recentData && recentData.data && recentData.data.length > 0) {
          // Filter posts that match the topic
          const filteredPosts = recentData.data.filter(post => 
            post.topic_id === topicId || 
            post.topics?.includes(topicId) || 
            post.keywords?.some(kw => topicName.toLowerCase().includes(kw.toLowerCase())) ||
            (post.title && post.title.toLowerCase().includes(topicName.toLowerCase())) ||
            (post.text && post.text.toLowerCase().includes(topicName.toLowerCase())) ||
            (post.content && post.content.toLowerCase().includes(topicName.toLowerCase()))
          );
           
          if (filteredPosts.length > 0) {
            console.log(`Found ${filteredPosts.length} filtered posts for topic ${topicName}`);
            setTopicPosts(filteredPosts);
            return;
          } else {
            console.log(`No filtered posts found for topic ${topicName}`);
            setTopicPosts([]);
          }
        } else {
          console.log(`No recent data found to filter posts for topic ${topicName}`);
          setTopicPosts([]);
        }
      } catch (err) {
        console.error("Error fetching topic posts:", err);
        setTopicPosts([]);
      }
    } catch (err) {
      console.error("Error handling topic click:", err);
      setTopicPosts([]);
    } finally {
      setLoadingPosts(false);
    }
  };

  // Close the post modal
  const closePostModal = () => {
    setSelectedTopicId(null);
    setTopicPosts([]);
  };

  /**
   * Fetches topic data from the API when component mounts or date filters change
   */
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
          setTopics([]);
          setTopicCounts({});
          setTopicSentiments({});
        } else {
          if (Array.isArray(response.topics)) {
            // Filter topics
            const filteredTopics = response.topics.filter(topic => 
              topic.id !== -1 && 
              topic.name && 
              topic.name.trim() !== ''
            );
            
            if (filteredTopics.length > 0) {
              const sortedTopics = filteredTopics.sort((a, b) => (b.weight || 0) - (a.weight || 0));
              setTopics(sortedTopics);
            } else if (response.topics.length > 0) {
              // If no valid topics after filtering but original list isn't empty
              const sortedOriginalTopics = response.topics.sort((a, b) => (b.weight || 0) - (a.weight || 0));
              setTopics(sortedOriginalTopics);
            } else {
              // No topics at all
              setTopics([]);
              setError("No topics were found in the database for the selected time period. Please try a different date range.");
            }
            
            // Process topic counts by date if available
            if (response.topic_counts_by_date) {
              setTopicCounts(response.topic_counts_by_date);
              
              // Process topic trends data for the chart
              if (filteredTopics.length > 0) {
                processTopicTrends(filteredTopics, response.topic_counts_by_date);
              } else if (response.topics.length > 0) {
                processTopicTrends(response.topics, response.topic_counts_by_date);
              } else {
                setTopicTrends([]);
              }
            } else {
              setTopicCounts({});
              setTopicTrends([]);
              console.warn("No topic counts by date found in the response");
            }
            
            // Get sentiment data from response
            if (response.topic_sentiments) {
              setTopicSentiments(response.topic_sentiments);
            } else {
              setTopicSentiments({});
            }
          } else {
            setTopics([]);
            setTopicCounts({});
            setTopicTrends([]);
            setTopicSentiments({});
            setError("Invalid response format from API: topics is not an array");
          }
          
          // Set time range from the response
          setTimeRange(response.time_range || {
            start_date: null,
            end_date: null
          });
        }
      } catch (err) {
        console.error("Error fetching topic data:", err);
        setError(`Failed to fetch topic data: ${err.message}`);
        setTopics([]);
        setTopicCounts({});
        setTopicTrends([]);
        setTopicSentiments({});
      } finally {
        setLoading(false);
      }
    };

    fetchTopicData();
  }, [dateFilter.startDate, dateFilter.endDate]);

  /**
   * Processes topic data to generate trend visualization charts
   * @param {Array} topTopics - Array of topic objects
   * @param {Object} countsByDate - Map of topic counts over time
   */
  const processTopicTrends = (topTopics, countsByDate) => {
    if (!topTopics || !countsByDate) {
      setTopicTrends([]);
      return;
    }
    
    console.log("Processing trends for topics:", topTopics);
    
    // Get all unique dates across all topics
    const allDates = new Set();
    
    // For each topic, collect all available dates
    topTopics.forEach(topic => {
      const topicId = topic.id?.toString();
      if (topicId && countsByDate[topicId]) {
        Object.keys(countsByDate[topicId]).forEach(date => allDates.add(date));
      } else {
        console.warn("Topic missing ID or no counts available:", topic);
      }
    });
    
    // Sort dates chronologically
    const sortedDates = Array.from(allDates).sort();
    
    if (sortedDates.length === 0) {
      console.warn("No dates found for any topics");
      setTopicTrends([]);
      return;
    }
    
    // Prepare chart data
    const datasets = [];
    
    // Only use the top 5 topics for the chart to avoid cluttering
    const topicsToShow = topTopics.slice(0, 5);
    
    // Generate colors for the topics
    const colors = [
      '#232252', // dark blue
      '#2e6cdb', // medium blue
      '#9364eb', // purple
      '#e750ae', // pink
      '#f8986f'  // orange
    ];
    
    // Create datasets for each topic
    topicsToShow.forEach((topic, index) => {
      const topicId = topic.id?.toString();
      if (!topicId || !countsByDate[topicId]) return;
      
      datasets.push({
        label: topic.name || `Topic ${index + 1}`,
        data: sortedDates.map(date => countsByDate[topicId][date] || 0),
        borderColor: colors[index % colors.length],
        backgroundColor: `${colors[index % colors.length]}22`, // Add transparency
        tension: 0.3,
        fill: index === 0 // Only fill the first dataset for visual appeal
      });
    });
    
    // Set final chart data
    setTopicTrends({
      labels: sortedDates,
      datasets
    });
    
    console.log("Generated trend chart data with dates:", sortedDates.length);
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
            {topics.slice(0, 5).map((topic, index) => (
              <div 
                key={topic.id || index} 
                className={`topic-stack topic-stack-${index + 1}`}
                onClick={() => handleTopicClick(topic.id, topic.name)}
                style={{ justifyContent: 'center', textAlign: 'center', margin: '15px auto', cursor: 'pointer' }}
              >
                <span className="topic-name-display">{topic.name || `Topic ${index + 1}`}</span>
                {topic.keywords && topic.keywords.length > 0 && (
                  <span className="topic-keywords">
                    {topic.keywords.slice(0, 3).map((kw, i) => (
                      <span key={i} className="topic-keyword-tag">{kw}</span>
                    ))}
                  </span>
                )}
                {topicSentiments[topic.id] !== undefined && (
                  <span className="sentiment-emoji" title={`Sentiment: ${topicSentiments[topic.id]}`}>
                    {getSentimentEmoji(parseFloat(topicSentiments[topic.id]))}
                  </span>
                )}
              </div>
            ))}
          </div>
          
          {/* Topic Trends Chart - New section */}
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
            {topicTrends.datasets && topicTrends.datasets.length > 0 ? (
              <Line
                data={topicTrends}
                options={chartOptions}
                height={350}
              />
            ) : (
              <div className="no-data-message" style={{height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <p>No trend data available for the selected time period.</p>
              </div>
            )}
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
          
          {/* Topic Post Counts */}
          <div className="topic-post-counts-section">
            {topics.slice(0, 5).map((topic, index) => (
              <div 
                key={topic.id || index} 
                className="topic-post-counts-card"
                onClick={() => handleTopicClick(topic.id, topic.name)}
                style={{ cursor: 'pointer' }}
              >
                <h3 className={`topic-name topic-name-${index + 1}`}>
                  {topic.name || `Topic ${index + 1}`}
                  {topicSentiments[topic.id] !== undefined && (
                    <span className="sentiment-emoji" style={{ marginLeft: '10px' }} title={`Sentiment: ${topicSentiments[topic.id]}`}>
                      {getSentimentEmoji(parseFloat(topicSentiments[topic.id]))}
                    </span>
                  )}
                </h3>
                {topic.keywords && topic.keywords.length > 0 && (
                  <div className="topic-keywords-small">
                    {topic.keywords.slice(0, 3).map((kw, i) => (
                      <span key={i} className="topic-keyword-tag-small">{kw}</span>
                    ))}
                  </div>
                )}
                {topicCounts[topic.id] ? renderTopicPostCounts(topic.id) : (
                  <div className="no-count-data">
                    <p>No post count data available</p>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* Topic Posts Modal */}
          {selectedTopicId && (
            <div className="topic-posts-modal">
              <div className="topic-posts-modal-content">
                <div className="topic-posts-header">
                  <h2>
                    {topics.find(t => t.id === selectedTopicId)?.name || 'Topic Posts'}
                  </h2>
                  <button className="close-modal-btn" onClick={closePostModal}>×</button>
                </div>
                
                {loadingPosts ? (
                  <div className="loading-spinner-container">
                    <div className="loading-spinner"></div>
                    <p>Loading posts...</p>
                  </div>
                ) : (
                  <div className="topic-posts-list">
                    {topicPosts.length > 0 ? (
                      topicPosts.map((post, index) => (
                        <div key={index} className="topic-post-item">
                          <div className="topic-post-header">
                            <div className="topic-post-source">
                              <span className={`source-icon ${(post.platform || post.source || '').toLowerCase()}`}>
                                {(post.platform || post.source || '').slice(0, 1).toUpperCase()}
                              </span>
                              <span className="source-name">{post.platform || post.source || 'Unknown'}</span>
                            </div>
                            <div className="topic-post-date">
                              {new Date(post.date || post.timestamp || Date.now()).toLocaleDateString('de-DE')}
                            </div>
                          </div>
                          <div className="topic-post-content">
                            {post.title && (
                              <h4 className="topic-post-title">{post.title}</h4>
                            )}
                            <p className="topic-post-text">{post.content || post.text || post.body || 'No content available'}</p>
                          </div>
                          {post.sentiment_score !== undefined && (
                            <div className="topic-post-sentiment">
                              <span className="sentiment-emoji">
                                {getSentimentEmoji(parseFloat(post.sentiment_score))}
                              </span>
                              <span className="sentiment-value">
                                Sentiment: {parseFloat(post.sentiment_score).toFixed(2)}
                              </span>
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="no-posts-message">
                        <p>No posts found for this topic.</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ) : !loading && !error ? (
        <div className="no-data-message">
          <p>No trending topics found for the selected time period.</p>
          <p>Please try selecting a different time period or try again later.</p>
          <p className="small-hint">If you haven't chosen a time period, data from the last 3 days will be analyzed.</p>
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
        </div>
      </AccessGate>
    </Router>
  );
}

export default App;
