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
          borderColor: '#FF4500',
          backgroundColor: 'rgba(255, 69, 0, 0.1)',
          tension: 0.3,
        },
        {
          label: 'TikTok',
          data: sortedDates.map(date => {
            const entry = dailyStats.tiktok.find(item => item.date === date);
            return entry ? entry.count : 0;
          }),
          borderColor: '#00F2EA',
          backgroundColor: 'rgba(0, 242, 234, 0.1)',
          tension: 0.3,
        },
        {
          label: 'YouTube',
          data: sortedDates.map(date => {
            const entry = dailyStats.youtube.find(item => item.date === date);
            return entry ? entry.count : 0;
          }),
          borderColor: '#FF0000',
          backgroundColor: 'rgba(255, 0, 0, 0.1)',
          tension: 0.3,
        },
      ],
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
          }
        }
      },
      title: {
        display: true,
        text: 'Daily Content Volume by Platform',
        font: {
          family: 'Sora, Arial, sans-serif',
          size: 18,
          weight: 'bold'
        }
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
          }
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(200, 200, 200, 0.2)'
        },
        ticks: {
          font: {
            family: 'Sora, Arial, sans-serif'
          }
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
                <div className="stats-item">
                  <span className="stats-label">Total Posts:</span>
                  <span className="stats-value">{data.total_posts}</span>
                </div>
                <div className="stats-item">
                  <span className="stats-label">Last Update:</span>
                  <span className="stats-value">
                    {data.last_update ? new Date(data.last_update).toLocaleString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="daily-stats-section">
        <h2>Daily Statistics</h2>
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