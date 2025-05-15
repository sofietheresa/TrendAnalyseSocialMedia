import React, { useState, useEffect } from 'react';
import { fetchRecentData } from '../services/api';
import './DataPage.css';

const DataPage = () => {
  const [data, setData] = useState({
    reddit: [],
    tiktok: [],
    youtube: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('reddit');
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await fetchRecentData(activeTab, limit);
        
        setData(prevData => ({
          ...prevData,
          [activeTab]: result.data || []
        }));
      } catch (err) {
        console.error("Error fetching data:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeTab, limit]);

  const renderContent = (item) => {
    // Try to access content using different potential field names
    const content = item.text || item.content || item.body || item.description || '';
    return content.length > 200 ? content.substring(0, 200) + '...' : content;
  };

  const renderDate = (item) => {
    // Try to access date using different potential field names
    const date = item.scraped_at || item.created_at || item.timestamp || item.date;
    return date ? new Date(date).toLocaleString() : 'Unknown date';
  };

  return (
    <div className="data-page">
      <div className="data-controls">
        <div className="platform-tabs">
          <button 
            className={`tab-button ${activeTab === 'reddit' ? 'active' : ''}`}
            onClick={() => setActiveTab('reddit')}
          >
            Reddit
          </button>
          <button 
            className={`tab-button ${activeTab === 'tiktok' ? 'active' : ''}`}
            onClick={() => setActiveTab('tiktok')}
          >
            TikTok
          </button>
          <button 
            className={`tab-button ${activeTab === 'youtube' ? 'active' : ''}`}
            onClick={() => setActiveTab('youtube')}
          >
            YouTube
          </button>
        </div>
        <div className="limit-control">
          <label htmlFor="limit-select">Show:</label>
          <select 
            id="limit-select" 
            value={limit} 
            onChange={(e) => setLimit(Number(e.target.value))}
          >
            <option value={10}>10 entries</option>
            <option value={25}>25 entries</option>
            <option value={50}>50 entries</option>
            <option value={100}>100 entries</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner-container">
          <div className="loading-spinner"></div>
          <p>Loading data...</p>
        </div>
      ) : error ? (
        <div className="error-message">
          <p>{error}</p>
        </div>
      ) : (
        <div className="data-list">
          {data[activeTab].length === 0 ? (
            <p className="no-data-message">No data available for this platform.</p>
          ) : (
            data[activeTab].map((item, index) => (
              <div key={index} className="data-card">
                <div className="data-header">
                  <span className="data-timestamp">{renderDate(item)}</span>
                  {item.author && <span className="data-author">by {item.author}</span>}
                </div>
                <div className="data-content">{renderContent(item)}</div>
                {item.title && <div className="data-title">{item.title}</div>}
                {item.url && (
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="data-link">
                    View original
                  </a>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default DataPage; 