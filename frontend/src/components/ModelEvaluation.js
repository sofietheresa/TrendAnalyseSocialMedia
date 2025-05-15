import React, { useState, useEffect } from 'react';
import { fetchTopicModel } from '../services/api';
import './ModelEvaluation.css';

const ModelEvaluation = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateFilter, setDateFilter] = useState({
    startDate: '',
    endDate: ''
  });
  const [timeRange, setTimeRange] = useState({
    start_date: null,
    end_date: null
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch topic model data which includes metrics
        const response = await fetchTopicModel(
          dateFilter.startDate || null, 
          dateFilter.endDate || null
        );
        
        if (response.error) {
          setError(response.error);
        } else {
          setMetrics(response.metrics);
          setTimeRange(response.time_range || {
            start_date: null,
            end_date: null
          });
        }
      } catch (err) {
        console.error("Error fetching model evaluation data:", err);
        setError(err.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [dateFilter.startDate, dateFilter.endDate]);

  // Handle date filter form submission
  const handleDateFilterSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const startDate = formData.get('startDate');
    const endDate = formData.get('endDate');
    
    setDateFilter({
      startDate,
      endDate
    });
  };

  return (
    <div className="model-evaluation-page">
      <h1 className="page-title">Model Evaluation</h1>
      
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
          <p>Loading evaluation metrics...</p>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
      
      {/* Metrics Display */}
      {!loading && !error && metrics && (
        <div className="metrics-container">
          <div className="metrics-card">
            <h2>Topic Model Quality Metrics</h2>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="metric-value">{(metrics.coherence_score || 0).toFixed(2)}</div>
                <div className="metric-label">Coherence Score</div>
                <div className="metric-description">
                  Measures how semantically coherent the topics are. Higher is better.
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-value">{(metrics.diversity_score || 0).toFixed(2)}</div>
                <div className="metric-label">Diversity Score</div>
                <div className="metric-description">
                  Measures how distinct the topics are from each other. Higher is better.
                </div>
              </div>
              <div className="metric-item">
                <div className="metric-value">{((metrics.document_coverage || 0) * 100).toFixed(0)}%</div>
                <div className="metric-label">Document Coverage</div>
                <div className="metric-description">
                  Percentage of documents assigned to at least one topic.
                </div>
              </div>
              {metrics.total_documents && (
                <div className="metric-item">
                  <div className="metric-value">{metrics.total_documents.toLocaleString()}</div>
                  <div className="metric-label">Total Documents</div>
                  <div className="metric-description">
                    Number of documents processed in the analysis.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelEvaluation; 