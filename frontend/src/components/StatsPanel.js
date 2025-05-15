import React, { useEffect, useState } from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  Title, 
  Tooltip, 
  Legend 
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { fetchScraperStatus, fetchDailyStats } from '../services/api';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

/**
 * StatsPanel Component
 * 
 * Displays statistics about scraped social media data with charts and metrics
 */
const StatsPanel = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scraperStatus, setScraperStatus] = useState(null);
  const [dailyStats, setDailyStats] = useState(null);

  // Fetch data on component mount and periodically
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch data from API
        const status = await fetchScraperStatus();
        const stats = await fetchDailyStats();
        
        setScraperStatus(status);
        setDailyStats(stats);
      } catch (err) {
        console.error("Error fetching data:", err);
        setError(`Failed to load data: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh data every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  /**
   * Prepare chart data from daily stats
   * Creates datasets for each platform with consistent formatting
   */
  const prepareChartData = () => {
    if (!dailyStats) return null;
    
    // Get all unique dates across all platforms
    const allDates = new Set();
    Object.values(dailyStats).forEach(platformData => {
      platformData.forEach(item => allDates.add(item.date));
    });
    
    // Sort dates chronologically
    const sortedDates = Array.from(allDates).sort();
    
    return {
      labels: sortedDates,
      datasets: [
        {
          label: 'Reddit',
          data: sortedDates.map(date => {
            const entry = dailyStats.reddit.find(item => item.date === date);
            return entry ? entry.count : 0;
          }),
          borderColor: '#d1343a',
          backgroundColor: 'rgba(209, 52, 58, 0.1)',
          tension: 0.3,
        },
        {
          label: 'TikTok',
          data: sortedDates.map(date => {
            const entry = dailyStats.tiktok.find(item => item.date === date);
            return entry ? entry.count : 0;
          }),
          borderColor: '#2e6cdb',
          backgroundColor: 'rgba(46, 108, 219, 0.1)',
          tension: 0.3,
        },
        {
          label: 'YouTube',
          data: sortedDates.map(date => {
            const entry = dailyStats.youtube.find(item => item.date === date);
            return entry ? entry.count : 0;
          }),
          borderColor: '#edaf4f',
          backgroundColor: 'rgba(237, 175, 79, 0.1)',
          tension: 0.3,
        },
      ],
    };
  };

  /**
   * Calculate the total posts from all dailyStats data
   */
  const calculateTotalPosts = () => {
    if (!dailyStats) return { reddit: 0, tiktok: 0, youtube: 0 };
    
    return {
      reddit: dailyStats.reddit.reduce((total, item) => total + item.count, 0),
      tiktok: dailyStats.tiktok.reduce((total, item) => total + item.count, 0),
      youtube: dailyStats.youtube.reduce((total, item) => total + item.count, 0)
    };
  };

  /**
   * Calculate today's posts for each platform
   */
  const calculateTodaysPosts = () => {
    if (!dailyStats) return { reddit: 0, tiktok: 0, youtube: 0 };
    
    // Get today's date in the format used in the API (YYYY-MM-DD)
    const today = new Date().toISOString().split('T')[0];
    
    return {
      reddit: dailyStats.reddit.find(item => item.date === today)?.count || 0,
      tiktok: dailyStats.tiktok.find(item => item.date === today)?.count || 0,
      youtube: dailyStats.youtube.find(item => item.date === today)?.count || 0
    };
  };

  /**
   * Get the most recent update date for each platform
   * Uses the most recent post's timestamp for each platform
   */
  const getLastUpdateDates = () => {
    if (!dailyStats) return { reddit: null, tiktok: null, youtube: null };
    
    const getLatestDate = (platformData) => {
      if (!platformData || platformData.length === 0) return null;
      
      // Sort posts by date in descending order to get the most recent
      const sortedPosts = [...platformData].sort((a, b) => 
        new Date(b.date) - new Date(a.date)
      );
      
      // Return the date of the most recent post
      return sortedPosts[0].date ? new Date(sortedPosts[0].date) : null;
    };
    
    return {
      reddit: getLatestDate(dailyStats.reddit),
      tiktok: getLatestDate(dailyStats.tiktok),
      youtube: getLatestDate(dailyStats.youtube)
    };
  };
  
  // Chart configuration options
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
        text: 'Daily Content Volume by Platform',
        font: {
          family: 'Sora, Arial, sans-serif',
          size: 18,
          weight: 'bold'
        },
        color: '#232252'
      },
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

  // Calculate statistics for display
  const totalPosts = calculateTotalPosts();
  const todaysPosts = calculateTodaysPosts();
  const lastUpdateDates = getLastUpdateDates();
  const chartData = prepareChartData();

  return (
    <div className="stats-panel">
      <h2 className="stats-heading">Social Media Monitoring</h2>
      
      {loading ? (
        <div className="loading-spinner-container">
          <div className="loading-spinner"></div>
          <p>Loading statistics...</p>
        </div>
      ) : error ? (
        <div className="error-message">
          <p>{error}</p>
        </div>
      ) : (
        <>
          {/* Platform Cards - Now at top with horizontal layout */}
          <div className="platform-cards-container" style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            gap: '20px', 
            marginBottom: '30px',
            flexWrap: 'wrap'
          }}>
            {['reddit', 'tiktok', 'youtube'].map(platform => (
              <div key={platform} className={`platform-card ${platform}`} style={{ 
                flex: '1',
                minWidth: '250px',
                maxWidth: '350px',
                margin: '0 auto'
              }}>
                <div className="platform-header">
                  <h3>{platform.charAt(0).toUpperCase() + platform.slice(1)}</h3>
                  <span className={`status-indicator ${scraperStatus && scraperStatus[platform]?.running ? 'active' : 'inactive'}`}>
                    {scraperStatus && scraperStatus[platform]?.running ? 'Active' : 'Inactive'}
                  </span>
                </div>
                
                <div className="stats-content">
                  <div className="stats-item">
                    <span className="stats-label">Total Posts:</span>
                    <span className="stats-value">{totalPosts[platform].toLocaleString()}</span>
                  </div>
                  
                  <div className="stats-item">
                    <span className="stats-label">Today's Posts:</span>
                    <span className="stats-value">{todaysPosts[platform]}</span>
                  </div>
                  
                  <div className="stats-item">
                    <span className="stats-label">Last Update:</span>
                    <span className="stats-value">
                      {lastUpdateDates[platform] ? lastUpdateDates[platform].toLocaleString('de-DE', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: false
                      }) : 'Never'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Chart Section */}
          <div className="chart-container">
            {chartData && (
              <Line 
                data={chartData} 
                options={chartOptions}
                height={300}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default StatsPanel; 