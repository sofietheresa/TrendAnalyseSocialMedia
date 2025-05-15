import React, { useState, useEffect } from 'react';
import { fetchRecentData } from '../services/api';
import './DataPage.css';

/**
 * DataPage Component
 * 
 * Displays recent social media content from different platforms
 * with filtering and pagination options
 */
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

  // Fetch data when tab or limit changes
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const result = await fetchRecentData(activeTab, limit);
        
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

  // Fetch data when tab or limit changes
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch data with retry (3 attempts)
        const result = await fetchRecentData(activeTab, limit, 3);
        
        // Check if there's an error in the result
        if (result.error) {
          console.error("API returned error:", result.error);
          setError(result.error);
          return;
        }
        
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
        
        console.log(`Processed ${activeTab} data:`, processedData);
        
        if (processedData.length === 0) {
          console.warn(`No data found for ${activeTab}`);
        }
        
        // Sort data in descending order by date
        const sortedData = sortDataByDate(processedData);
        
        // Update the state with the sorted data
        setData(prevData => ({
          ...prevData,
          [activeTab]: sortedData
        }));
      } catch (err) {
        console.error("Error in data handling:", err);
        setError(`Failed to process data: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeTab, limit]);

  /**
   * Sort data by date in descending order (newest first)
   * 
   * @param {Array} dataArray - Array of data items
   * @returns {Array} - Sorted array
   */
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
  
  /**
   * Extract date value from an item regardless of field name
   * 
   * @param {Object} item - Data item
   * @returns {string|null} - Date value or null
   */
  const getDateFromItem = (item) => {
    return item.scraped_at || item.created_at || item.timestamp || item.date;
  };

  /**
   * Render content with truncation for long text
   * 
   * @param {Object} item - Data item
   * @returns {string} - Formatted content
   */
  const renderContent = (item) => {
    // Try to access content using different potential field names
    const content = item.text || item.content || item.body || item.description || '';
    return content.length > 200 ? content.substring(0, 200) + '...' : content;
  };

  /**
   * Format date for display
   * 
   * @param {Object} item - Data item
   * @returns {string} - Formatted date string
   */
  const renderDate = (item) => {
    // Try to access date using different potential field names
    const date = getDateFromItem(item);
    return date ? new Date(date).toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }) : 'Kein Datum';
  };

  return (
    <div className="data-page">
      <h1 className="page-title">Recent Social Media Content</h1>
      
      <div className="data-controls">
        {/* Platform selection tabs */}
        <div className="platform-tabs">
          {['reddit', 'tiktok', 'youtube'].map(platform => (
            <button 
              key={platform}
              className={`tab-button ${activeTab === platform ? 'active' : ''}`}
              onClick={() => setActiveTab(platform)}
            >
              {platform.charAt(0).toUpperCase() + platform.slice(1)}
            </button>
          ))}
        </div>
        
        {/* Results limit dropdown */}
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

      {/* Content display section */}
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