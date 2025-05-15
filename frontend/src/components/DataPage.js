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
        setError(null);
        console.log(`Fetching ${activeTab} data with limit ${limit}...`);
        const result = await fetchRecentData(activeTab, limit);
        console.log('Result received:', result);
        
        // Process and sort the data
        let processedData = [];
        
        // Handle different possible response structures
        if (result && result.data && Array.isArray(result.data)) {
          processedData = result.data;
        } else if (result && Array.isArray(result)) {
          processedData = result;
        } else if (result && typeof result === 'object') {
          // Try to find any array in the response
          for (const key in result) {
            if (Array.isArray(result[key]) && result[key].length > 0) {
              processedData = result[key];
              break;
            }
          }
        }
        
        // Sort data in descending order by date
        const sortedData = sortDataByDate(processedData);
        console.log('Sorted data:', sortedData);
        
        // Update the state with the sorted data
        setData(prevData => ({
          ...prevData,
          [activeTab]: sortedData
        }));
      } catch (err) {
        console.error("Error fetching data:", err);
        setError(err.message || 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeTab, limit]);

  // Function to sort data by date in descending order
  const sortDataByDate = (dataArray) => {
    if (!Array.isArray(dataArray) || dataArray.length === 0) return [];
    
    return [...dataArray].sort((a, b) => {
      // Try to access date field with different potential names
      const dateA = getDateFromItem(a);
      const dateB = getDateFromItem(b);
      
      // If dates can't be compared, keep original order
      if (!dateA || !dateB) return 0;
      
      // Sort in descending order (newest first)
      return new Date(dateB) - new Date(dateA);
    });
  };
  
  // Helper to extract date from an item with different potential field names
  const getDateFromItem = (item) => {
    return item.scraped_at || item.created_at || item.timestamp || item.date;
  };

  const renderContent = (item) => {
    // Try to access content using different potential field names
    const content = item.text || item.content || item.body || item.description || '';
    return content.length > 200 ? content.substring(0, 200) + '...' : content;
  };

  const renderDate = (item) => {
    // Try to access date using different potential field names
    const date = getDateFromItem(item);
    return date ? new Date(date).toLocaleString() : 'Unknown date';
  };
  
  // Debug function to show data structure
  const debugData = () => {
    if (!data[activeTab] || data[activeTab].length === 0) return null;
    const sample = data[activeTab][0];
    console.log('Sample data item:', sample);
    return (
      <div className="debug-info">
        <h4>Data fields available:</h4>
        <ul>
          {Object.keys(sample).map(key => (
            <li key={key}>{key}: {typeof sample[key] === 'object' ? JSON.stringify(sample[key]) : sample[key]}</li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="data-page">
      <h1 className="page-title">Recent Social Media Content</h1>
      
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
          {(!data[activeTab] || data[activeTab].length === 0) ? (
            <div className="no-data-message">
              <p>No data available for this platform.</p>
              <p>Try selecting a different platform or increasing the limit.</p>
              
              {/* Show what we received from the API for debugging */}
              <div className="debug-section">
                <button 
                  onClick={() => console.log('Current data state:', data)} 
                  className="debug-button"
                >
                  Debug: Log data to console
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="data-count">
                Showing {data[activeTab].length} items
              </div>
              {data[activeTab].map((item, index) => (
                <div key={index} className="data-card">
                  <div className="data-header">
                    <span className="data-timestamp">{renderDate(item)}</span>
                    {item.author && <span className="data-author">by {item.author}</span>}
                  </div>
                  {item.title && <div className="data-title">{item.title}</div>}
                  <div className="data-content">{renderContent(item)}</div>
                  {item.url && (
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="data-link">
                      View original
                    </a>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default DataPage; 