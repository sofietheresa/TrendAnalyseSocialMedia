import React, { useState, useEffect } from 'react';
import { fetchPredictions } from '../services/api';
import { Line } from 'react-chartjs-2';
import { formatDate, formatWeekday } from '../utils/dateUtils';
import './PredictionsPage.css';
import ModelVersionBadge from './ModelVersionBadge';
import './ModelVersionBadge.css';

const PredictionsPage = () => {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [timeRange, setTimeRange] = useState({
    start_date: null,
    end_date: null
  });
  const [dateFilter, setDateFilter] = useState({
    startDate: '',
    endDate: ''
  });
  const [predictionTrends, setPredictionTrends] = useState([]);

  // Get sentiment emoji based on sentiment score
  const getSentimentEmoji = (sentiment) => {
    if (!sentiment && sentiment !== 0) return '';
    
    if (sentiment >= 0.5) return '😄'; // Very positive
    if (sentiment >= 0.1) return '🙂'; // Positive
    if (sentiment > -0.1) return '😐'; // Neutral
    if (sentiment > -0.5) return '🙁'; // Negative
    return '😠'; // Very negative
  };

  // Fetch predictions data
  useEffect(() => {
    const fetchPredictionData = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log("Fetching prediction data with filters:", dateFilter);
        
        const response = await fetchPredictions(
          dateFilter.startDate || null, 
          dateFilter.endDate || null
        );
        
        console.log("Received prediction data:", response);
        
        if (response.error) {
          setError(response.error);
          console.error("Error from predictions API:", response.error);
        } else {
          if (Array.isArray(response.predictions)) {
            if (response.predictions.length > 0) {
              setPredictions(response.predictions);
              
              // Process prediction trends data for the chart
              if (response.prediction_trends) {
                processPredictionTrends(response.predictions, response.prediction_trends);
              }
            } else {
              // Handle empty predictions array
              setError("No prediction data found for the selected time period. Please try a different date range.");
              setPredictions([]);
            }
          } else {
            console.warn("Invalid predictions format:", response.predictions);
            setError("The data received from the server has an invalid format. Please contact an administrator.");
            setPredictions([]);
          }
          
          setTimeRange(response.time_range || {
            start_date: null,
            end_date: null
          });
        }
      } catch (err) {
        console.error("Error fetching prediction data:", err);
        setError(`Failed to fetch real prediction data: ${err.message}`);
        setPredictions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPredictionData();
  }, [dateFilter.startDate, dateFilter.endDate]);

  // Process prediction trends data for the chart
  const processPredictionTrends = (topicPredictions, trendsByDate) => {
    if (!topicPredictions || !trendsByDate) return;
    
    console.log("Processing trends for predictions:", topicPredictions);
    console.log("With trends by date:", trendsByDate);
    
    // Get all unique dates across all predictions
    const allDates = new Set();
    
    // For each topic, collect all available dates
    topicPredictions.forEach(prediction => {
      if (prediction.topic_id && trendsByDate[prediction.topic_id]) {
        Object.keys(trendsByDate[prediction.topic_id]).forEach(date => allDates.add(date));
      } else {
        console.warn("Prediction missing topic_id or no trends available:", prediction);
      }
    });
    
    // Sort dates chronologically
    const sortedDates = Array.from(allDates).sort();
    
    if (sortedDates.length === 0) {
      console.warn("No dates found for any predictions");
      return;
    }
    
    // Prepare chart data
    const trendsData = {
      labels: sortedDates.map(date => formatDate(date)),
      datasets: topicPredictions.filter(prediction => prediction.topic_id && trendsByDate[prediction.topic_id]).map((prediction, index) => {
        // Generate colors based on index
        const colors = [
          '#232252', // dark blue
          '#2e6cdb', // medium blue
          '#9364eb', // purple
          '#e750ae', // pink
          '#f8986f'  // orange
        ];
        
        return {
          label: prediction.topic_name || `Topic ${index + 1}`,
          data: sortedDates.map(date => {
            const value = prediction.topic_id && trendsByDate[prediction.topic_id] && trendsByDate[prediction.topic_id][date] 
              ? trendsByDate[prediction.topic_id][date] 
              : 0;
            return value;
          }),
          borderColor: colors[index % colors.length],
          backgroundColor: `${colors[index % colors.length]}22`, // Add transparency
          tension: 0.3,
          fill: index === 0 // Only fill the first dataset
        };
      })
    };
    
    console.log("Generated prediction trends data:", trendsData);
    setPredictionTrends(trendsData);
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
        text: 'Predicted Topic Trends',
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
            return `${context.dataset.label}: ${context.raw} predicted posts`;
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

  return (
    <main className="app-content">
      {/* Title with proper margin for fixed navbar */}
      <h1 className="main-title" style={{ marginTop: '20px', marginBottom: '40px' }}>
        <span style={{ fontWeight: 900, letterSpacing: '0.03em' }}>TOPIC PREDICTIONS</span>
        <br />
        <span style={{ fontWeight: 400, fontSize: '0.8em' }}>Machine Learning Forecasts</span>
      </h1>
      
      {/* Model Version Badge */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
        <ModelVersionBadge version="V1.0.2" date="16.5.2025, 20:28:13" />
      </div>
      
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
            Predict
          </button>
        </form>
      </div>
      
      {/* Loading State */}
      {loading && (
        <div className="loading-spinner-container">
          <div className="loading-spinner"></div>
          <p>Analyzing predictions...</p>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
      
      {/* Predictions Display */}
      {!loading && !error && predictions && predictions.length > 0 ? (
        <div className="predictions-container">
          <div className="predictions-header">
            <h2>Predicted Trending Topics</h2>
            <p className="predictions-subheader">
              ML-powered forecast of upcoming trends
            </p>
          </div>

          {/* Prediction Cards */}
          <div className="predictions-grid">
            {predictions.map((prediction, index) => (
              <div key={index} className={`prediction-card prediction-color-${index % 5}`}>
                <h3 className="prediction-topic">{prediction.topic_name || `Topic ${index + 1}`}</h3>
                <div className="prediction-confidence">
                  <div className="prediction-meter">
                    <div 
                      className="prediction-fill"
                      style={{width: `${Math.min(100, Math.max(0, (prediction.confidence || 0.5) * 100))}%`}}
                    ></div>
                  </div>
                  <span className="prediction-percentage">{Math.round((prediction.confidence || 0.5) * 100)}% confidence</span>
                </div>
                
                {prediction.sentiment_score !== undefined && (
                  <div className="prediction-sentiment">
                    <span className="sentiment-emoji" title={`Sentiment: ${prediction.sentiment_score}`}>
                      {getSentimentEmoji(prediction.sentiment_score)}
                    </span>
                    <span className="sentiment-label">
                      Predicted sentiment: {prediction.sentiment_score >= 0.1 ? 'Positive' : 
                      prediction.sentiment_score <= -0.1 ? 'Negative' : 'Neutral'}
                    </span>
                  </div>
                )}

                {prediction.keywords && prediction.keywords.length > 0 && (
                  <div className="prediction-keywords">
                    <span className="keywords-label">Related keywords:</span>
                    <div className="keywords-list">
                      {prediction.keywords.map((keyword, kidx) => (
                        <span key={kidx} className="keyword-tag">{keyword}</span>
                      ))}
                    </div>
                  </div>
                )}
                
                {prediction.forecast_data && (
                  <div className="prediction-forecast">
                    <span className="forecast-label">7-day forecast:</span>
                    <div className="forecast-bars">
                      {Object.entries(prediction.forecast_data).map(([date, value], idx) => (
                        <div key={idx} className="forecast-bar-container">
                          <div className="forecast-date">{formatWeekday(date)}</div>
                          <div className="forecast-bar-wrapper">
                            <div 
                              className="forecast-bar" 
                              style={{height: `${Math.min(100, Math.max(5, value / (prediction.forecast_max || 100) * 100))}%`}}
                            ></div>
                          </div>
                          <div className="forecast-value">{Math.round(value)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* Prediction Trends Chart */}
          {predictionTrends.datasets && predictionTrends.datasets.length > 0 && (
            <div className="prediction-trends-chart" style={{ 
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
                data={predictionTrends}
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
                  Prediction period: {formatDate(dateFilter.startDate)} - {formatDate(dateFilter.endDate)}
                </div>
              )}
            </div>
          )}
        </div>
      ) : !loading && !error ? (
        <div className="no-data-message">
          <p>No predictions available for the selected time period.</p>
          <p>Try selecting a different date range or check back later.</p>
        </div>
      ) : null}
    </main>
  );
};

export default PredictionsPage; 