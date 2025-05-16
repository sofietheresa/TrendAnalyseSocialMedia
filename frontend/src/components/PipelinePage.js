import React, { useState, useEffect } from 'react';
import { fetchPipelines, fetchPipelineExecutions, executePipeline } from '../services/api';
import { formatDateTime } from '../utils/dateUtils';
import './PipelinePage.css';

/**
 * PipelinePage Component
 * 
 * Visualizes and monitors ML Ops pipelines for the Social Media Trend Analysis project
 */
const PipelinePage = () => {
  const [pipelineData, setPipelineData] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState('trend_analysis');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pipelineStats, setPipelineStats] = useState({
    success: 0,
    failed: 0,
    running: 0,
    total: 0,
    avgRuntime: 0
  });
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionMessage, setExecutionMessage] = useState(null);

  // Fetch pipeline data on component mount and when selected pipeline changes
  useEffect(() => {
    const fetchPipelineData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch all available pipelines
        const allPipelines = await fetchPipelines();
        console.log('All available pipelines:', allPipelines);
        
        if (!allPipelines || Object.keys(allPipelines).length === 0) {
          throw new Error('No pipelines available');
        }
        
        // Fetch pipeline data from API
        const pipelineData = await fetchPipelines(selectedPipeline);
        console.log('Received pipeline data:', pipelineData);
        
        if (!pipelineData || pipelineData.error || typeof pipelineData !== 'object') {
          throw new Error(`Failed to fetch pipeline data for ${selectedPipeline}`);
        }
        
        setPipelineData(pipelineData);
        
        // Fetch executions for the selected pipeline
        const executionsData = await fetchPipelineExecutions(selectedPipeline);
        console.log('Received executions data:', executionsData);
        
        if (!Array.isArray(executionsData)) {
          throw new Error(`Failed to fetch pipeline executions for ${selectedPipeline}`);
        }
        
        setExecutions(executionsData);
        
        // Calculate stats based on the pipeline data
        const stats = {
          success: executionsData.filter(exec => exec.status === "completed").length,
          failed: executionsData.filter(exec => exec.status === "failed").length,
          running: executionsData.filter(exec => exec.status === "running").length,
          total: executionsData.length,
          avgRuntime: pipelineData.averageRuntime || "00:00:00"
        };
        
        setPipelineStats(stats);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching pipeline data:", err);
        setError(`Failed to load pipeline data: ${err.message}`);
        setLoading(false);
      }
    };

    fetchPipelineData();
  }, [selectedPipeline]);
  
  // Execute pipeline function
  const handleExecutePipeline = async () => {
    try {
      setIsExecuting(true);
      setExecutionMessage(null);
      
      const result = await executePipeline(selectedPipeline);
      
      if (result.error) {
        setExecutionMessage({
          type: 'error',
          text: result.error
        });
      } else {
        setExecutionMessage({
          type: 'success',
          text: result.message || `Pipeline "${selectedPipeline}" execution started`
        });
        
        // Refresh pipeline data after a short delay
        setTimeout(() => {
          const fetchPipelineData = async () => {
            try {
              const pipelineData = await fetchPipelines(selectedPipeline);
              const executionsData = await fetchPipelineExecutions(selectedPipeline);
              
              if (pipelineData && typeof pipelineData === 'object') {
                setPipelineData(pipelineData);
              }
              
              if (Array.isArray(executionsData)) {
                setExecutions(executionsData);
                
                // Update stats
                const stats = {
                  success: executionsData.filter(exec => exec.status === "completed").length,
                  failed: executionsData.filter(exec => exec.status === "failed").length,
                  running: executionsData.filter(exec => exec.status === "running").length,
                  total: executionsData.length,
                  avgRuntime: pipelineData?.averageRuntime || "00:00:00"
                };
                
                setPipelineStats(stats);
              }
            } catch (error) {
              console.error("Error refreshing pipeline data:", error);
              setExecutionMessage({
                type: 'warning',
                text: 'Pipeline execution started, but could not refresh pipeline data'
              });
            }
          };
          
          fetchPipelineData();
        }, 2000);
      }
    } catch (err) {
      setExecutionMessage({
        type: 'error',
        text: `Failed to execute pipeline: ${err.message}`
      });
    } finally {
      setIsExecuting(false);
    }
  };

  // Helper function to get step status class
  const getStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'status-completed';
      case 'running':
        return 'status-running';
      case 'failed':
        return 'status-failed';
      case 'pending':
        return 'status-pending';
      default:
        return '';
    }
  };

  // Helper function to format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return formatDateTime(dateString);
  };

  return (
    <div className="pipeline-page">
      <h1 className="page-title">ML Ops Pipelines</h1>
      
      {/* Pipeline Selection */}
      <div className="pipeline-selector">
        <div className="pipeline-selector-title">Select Pipeline:</div>
        <div className="pipeline-selector-buttons">
          <button 
            className={`pipeline-selector-button ${selectedPipeline === 'trend_analysis' ? 'active' : ''}`}
            onClick={() => setSelectedPipeline('trend_analysis')}
          >
            Trend Analysis
          </button>
          <button 
            className={`pipeline-selector-button ${selectedPipeline === 'realtime_monitoring' ? 'active' : ''}`}
            onClick={() => setSelectedPipeline('realtime_monitoring')}
          >
            Realtime Monitoring
          </button>
          <button 
            className={`pipeline-selector-button ${selectedPipeline === 'model_training' ? 'active' : ''}`}
            onClick={() => setSelectedPipeline('model_training')}
          >
            Model Training
          </button>
        </div>
      </div>
      
      {/* Loading State */}
      {loading && (
        <div className="loading-spinner-container">
          <div className="loading-spinner"></div>
          <p>Loading pipeline data...</p>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}
      
      {/* Execution Message */}
      {executionMessage && (
        <div className={`execution-message ${executionMessage.type}`}>
          <p>{executionMessage.text}</p>
        </div>
      )}
      
      {/* Pipeline Visualization */}
      {!loading && !error && pipelineData && (
        <div className="pipeline-container">
          <div className="pipeline-header">
            <div className="pipeline-title">
              <h2>{pipelineData.name || 'Pipeline'}</h2>
              <p className="pipeline-description">{pipelineData.description || 'No description available'}</p>
            </div>
            <div className="pipeline-actions">
              <button 
                className="execute-pipeline-button"
                onClick={handleExecutePipeline}
                disabled={isExecuting || (pipelineData.status === 'running')}
              >
                {isExecuting ? 'Starting Pipeline...' : 'Execute Pipeline'}
              </button>
              <div className={`pipeline-status status-${pipelineData.status || 'unknown'}`}>
                {(pipelineData.status || 'UNKNOWN').toUpperCase()}
              </div>
            </div>
          </div>
          
          {/* Pipeline Statistics */}
          <div className="pipeline-stats">
            <div className="stat-card">
              <div className="stat-value">{pipelineStats.total}</div>
              <div className="stat-label">Total Runs</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{pipelineStats.success}</div>
              <div className="stat-label">Successful</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{pipelineStats.failed}</div>
              <div className="stat-label">Failed</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{pipelineStats.running}</div>
              <div className="stat-label">Running</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{pipelineStats.avgRuntime || '00:00:00'}</div>
              <div className="stat-label">Avg. Runtime</div>
            </div>
          </div>
          
          {/* Execution Timeline */}
          <div className="pipeline-executions">
            <h3>Recent Executions</h3>
            <div className="executions-list">
              {executions && executions.length > 0 ? (
                executions.map(execution => (
                  <div key={execution.id} className={`execution-item status-${execution.status || 'unknown'}`}>
                    <div className="execution-info">
                      <div className="execution-id">{execution.id || 'N/A'}</div>
                      <div className="execution-trigger">{execution.trigger || 'N/A'}</div>
                    </div>
                    <div className="execution-times">
                      <div>Start: {formatDate(execution.startTime)}</div>
                      <div>End: {execution.endTime ? formatDate(execution.endTime) : 'Running...'}</div>
                    </div>
                    <div className="execution-status">{execution.status || 'Unknown'}</div>
                  </div>
                ))
              ) : (
                <div className="no-executions">No executions found for this pipeline</div>
              )}
            </div>
          </div>
          
          {/* Pipeline Steps Visualization */}
          <div className="pipeline-steps-container">
            <h3>Pipeline Steps</h3>
            <div className="pipeline-steps">
              {pipelineData.steps && Array.isArray(pipelineData.steps) && pipelineData.steps.length > 0 ? (
                pipelineData.steps.map((step, index) => (
                  <div key={step.id || index} className="pipeline-step">
                    <div className={`step-number ${getStatusClass(step.status)}`}>{index + 1}</div>
                    <div className="step-connector">
                      {index < pipelineData.steps.length - 1 && (
                        <div className={`connector-line ${
                          (pipelineData.steps[index + 1].status === 'pending' || 
                          step.status === 'failed') ? 
                          'connector-inactive' : ''
                        }`}></div>
                      )}
                    </div>
                    <div className={`step-content ${getStatusClass(step.status)}`}>
                      <div className="step-header">
                        <h4>{step.name || `Step ${index + 1}`}</h4>
                        <div className="step-status">{step.status || 'Unknown'}</div>
                      </div>
                      <div className="step-description">{step.description || 'No description available'}</div>
                      <div className="step-runtime">Runtime: {step.runtime || 'N/A'}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-steps">No steps data available for this pipeline</div>
              )}
            </div>
          </div>
          
          {/* Schedule Information */}
          <div className="pipeline-schedule">
            <div className="schedule-info">
              <div className="schedule-label">Last Run:</div>
              <div className="schedule-value">{formatDate(pipelineData.lastRun)}</div>
            </div>
            <div className="schedule-info">
              <div className="schedule-label">Next Run:</div>
              <div className="schedule-value">
                {pipelineData.nextScheduledRun === 'continuous' ? 
                  'Continuous Execution' : 
                  formatDate(pipelineData.nextScheduledRun)
                }
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PipelinePage; 