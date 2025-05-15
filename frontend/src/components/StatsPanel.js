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

const StatsPanel = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scraperStatus, setScraperStatus] = useState(null);
  const [dailyStats, setDailyStats] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log("Fetching data for stats panel...");
        
        const status = await fetchScraperStatus();
        const stats = await fetchDailyStats();
        
        setScraperStatus(status);
        setDailyStats(stats);
        console.log("Data fetched successfully:", { status, stats });
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

  // Prepare chart data
  const prepareChartData = () => {
    if (!dailyStats) return null;
    
    // Get all unique dates across all platforms
    const allDates = new Set();
    Object.values(dailyStats).forEach(platformData => {
      platformData.forEach(item => allDates.add(item.date));
    });
    
    // Sort dates
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

  // Calculate the actual total posts from daily stats
  const calculateTotalPosts = () => {
    if (!dailyStats) return { reddit: 0, tiktok: 0, youtube: 0 };
    
    return {
      reddit: dailyStats.reddit.reduce((total, item) => total + item.count, 0),
      tiktok: dailyStats.tiktok.reduce((total, item) => total + item.count, 0),
      youtube: dailyStats.youtube.reduce((total, item) => total + item.count, 0)
    };
  };

  // Calculate today's posts
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

  // Get the most recent update date for each platform
  const getLastUpdateDates = () => {
    if (!dailyStats) return { reddit: null, tiktok: null, youtube: null };
    
    return {
      reddit: dailyStats.reddit.length > 0 
        ? new Date(Math.max(...dailyStats.reddit.map(item => new Date(item.date)))) 
        : null,
      tiktok: dailyStats.tiktok.length > 0 
        ? new Date(Math.max(...dailyStats.tiktok.map(item => new Date(item.date)))) 
        : null,
      youtube: dailyStats.youtube.length > 0 
        ? new Date(Math.max(...dailyStats.youtube.map(item => new Date(item.date)))) 
        : null
    };
  };
  
  // Chart options
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

  if (loading) {
    return (
      <div className="stats-loading">
        <div className="loading-spinner"></div>
        <p>Loading statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stats-error">
        <h3>Error Loading Data</h3>
        <p>{error}</p>
      </div>
    );
  }

  const chartData = prepareChartData();
  const totalPosts = calculateTotalPosts();
  const todaysPosts = calculateTodaysPosts();
  const lastUpdateDates = getLastUpdateDates();

  return (
    <div className="stats-panel">
      <div className="scraper-status-section">
        <h2>Scraper Status</h2>
        <div className="status-cards">
          {scraperStatus && Object.entries(scraperStatus).map(([platform, data]) => (
            <div key={platform} className={`status-card ${platform}`}>
              <h3>{platform.charAt(0).toUpperCase() + platform.slice(1)}</h3>
              <div className={`status-indicator ${data.running ? 'active' : 'inactive'}`}>
                {data.running ? 'Active' : 'Inactive'}
              </div>
              <div className="stats-details">
                <h4>Today's Stats</h4>
                <div className="stats-item">
                  <span className="stats-value" style={{ fontSize: '2rem', fontWeight: '700', display: 'block', textAlign: 'center' }}>{todaysPosts[platform] || 0}</span>
                </div>
                
                <h4>Overall Statistics</h4>
                <div className="stats-item">
                  <span className="stats-label">Total Posts:</span>
                  <span className="stats-value">{totalPosts[platform] || 0}</span>
                </div>
                <div className="stats-item">
                  <span className="stats-label">Last Update:</span>
                  <span className="stats-value">
                    {lastUpdateDates[platform] ? lastUpdateDates[platform].toLocaleString(undefined, {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    }) : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="daily-stats-section">
        <h2>Daily Statistics</h2>
        <div className="stats-summary">
          <div className="summary-item reddit">
            <div className="summary-value">{totalPosts.reddit}</div>
            <div className="summary-label">Reddit Posts</div>
          </div>
          <div className="summary-item tiktok">
            <div className="summary-value">{totalPosts.tiktok}</div>
            <div className="summary-label">TikTok Videos</div>
          </div>
          <div className="summary-item youtube">
            <div className="summary-value">{totalPosts.youtube}</div>
            <div className="summary-label">YouTube Videos</div>
          </div>
        </div>
        <div className="chart-container">
          {chartData ? (
            <Line data={chartData} options={chartOptions} height={300} />
          ) : (
            <p>No data available for chart</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatsPanel; 