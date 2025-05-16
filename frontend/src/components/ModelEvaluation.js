import React, { useState, useEffect } from 'react';
import { fetchTopicModel, fetchModelVersions, fetchModelMetrics, fetchModelDrift } from '../services/api';
import { formatDate, formatDateTime, formatNumber } from '../utils/dateUtils';
import './ModelEvaluation.css';
import ModelVersionBadge from './ModelVersionBadge';
import './ModelVersionBadge.css';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, RadialLinearScale } from 'chart.js';
import { Radar, Line, Bar, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
);

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
  const [selectedModel, setSelectedModel] = useState('topic_model');
  const [modelVersions, setModelVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [confusionMatrix, setConfusionMatrix] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [featureImportance, setFeatureImportance] = useState(null);
  const [sentimentExamples, setSentimentExamples] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch model versions
        let versions;
        try {
          versions = await fetchModelVersions(selectedModel);
          console.log('Fetched model versions:', versions);
          
          if (!versions || versions.error || !Array.isArray(versions) || versions.length === 0) {
            throw new Error('Failed to fetch valid model versions');
          }
          
          setModelVersions(versions);
        } catch (err) {
          console.error('Error fetching model versions:', err);
          throw new Error('Could not fetch model versions');
        }
        
        // Set selected version to the production version or first available
        const productionVersion = versions.find(v => v.status === 'production')?.id;
        const versionToSelect = productionVersion || (versions.length > 0 ? versions[0].id : null);
        setSelectedVersion(versionToSelect);
        
        // Fetch model metrics for the selected version
        try {
          if (versionToSelect) {
            const metricsData = await fetchModelMetrics(selectedModel, versionToSelect);
            console.log('Fetched model metrics:', metricsData);
            
            if (!metricsData || metricsData.error) {
              throw new Error('Failed to fetch valid metrics data');
            }
            
            setMetrics(metricsData);

            // For trend prediction model, fetch forecast data
            if (selectedModel === 'trend_prediction' && metricsData.forecast_data) {
              setForecastData(metricsData.forecast_data);
              
              // Set feature importance if available
              if (metricsData.feature_importance) {
                setFeatureImportance(metricsData.feature_importance);
              }
            }
            
            // For sentiment analysis, set example classifications
            if (selectedModel === 'sentiment_analysis' && metricsData.example_classifications) {
              setSentimentExamples(metricsData.example_classifications);
            }
          } else {
            throw new Error('No valid model version available');
          }
        } catch (err) {
          console.error('Error fetching model metrics:', err);
          throw new Error('Could not fetch model metrics');
        }
        
        // Fetch metrics history
        try {
          const historyData = await fetch(`/api/mlops/models/${selectedModel}/metrics/history`);
          const historyJson = await historyData.json();
          
          if (historyJson && Array.isArray(historyJson) && historyJson.length > 0) {
            setMetricsHistory(historyJson);
          } else {
            console.warn('No metrics history data available');
            setMetricsHistory([]);
          }
        } catch (err) {
          console.error('Error fetching metrics history:', err);
          setMetricsHistory([]);
        }
        
        // Fetch drift metrics for relevant model types
        if (selectedModel === 'topic_model' || selectedModel === 'sentiment_analysis') {
          try {
            const driftData = await fetchModelDrift(selectedModel, versionToSelect);
            console.log('Fetched drift data:', driftData);
            
            if (driftData && !driftData.error && driftData.confusionMatrix) {
              setConfusionMatrix(driftData.confusionMatrix);
            } else {
              console.warn('No confusion matrix data available');
              setConfusionMatrix(null);
            }
          } catch (err) {
            console.error('Error fetching drift data:', err);
            setConfusionMatrix(null);
          }
        }
        
        // Set time range based on available data
        const today = new Date();
        const twoWeeksAgo = new Date(today);
        twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
        
        setTimeRange({
          start_date: twoWeeksAgo.toISOString().split('T')[0],
          end_date: today.toISOString().split('T')[0]
        });
        
        setLoading(false);
      } catch (err) {
        console.error("Error fetching model evaluation data:", err);
        setError(err.message || "Failed to load data");
        setLoading(false);
      }
    };

    fetchData();
  }, [dateFilter.startDate, dateFilter.endDate, selectedModel]);

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
  
  // Handle version selection
  const handleVersionSelect = async (versionId) => {
    if (versionId === selectedVersion) return;
    
    setSelectedVersion(versionId);
    
    try {
      setLoading(true);
      // Fetch metrics for the selected version
      const metricsData = await fetchModelMetrics(selectedModel, versionId);
      console.log('Fetched metrics for selected version:', metricsData);
      
      if (!metricsData || metricsData.error) {
        throw new Error('Failed to fetch valid metrics data');
      }
      
      setMetrics(metricsData);

      // For trend prediction model, update forecast data
      if (selectedModel === 'trend_prediction' && metricsData.forecast_data) {
        setForecastData(metricsData.forecast_data);
        
        // Update feature importance if available
        if (metricsData.feature_importance) {
          setFeatureImportance(metricsData.feature_importance);
        }
      }
      
      // For sentiment analysis, update example classifications
      if (selectedModel === 'sentiment_analysis' && metricsData.example_classifications) {
        setSentimentExamples(metricsData.example_classifications);
      }
      
      // Fetch drift metrics for relevant model types
      if (selectedModel === 'topic_model' || selectedModel === 'sentiment_analysis') {
        try {
          const driftData = await fetchModelDrift(selectedModel, versionId);
          console.log('Fetched drift data for selected version:', driftData);
          
          if (driftData && !driftData.error && driftData.confusionMatrix) {
            setConfusionMatrix(driftData.confusionMatrix);
          }
        } catch (err) {
          console.error('Error fetching drift data:', err);
          setConfusionMatrix(null);
        }
      }
      
    } catch (err) {
      console.error("Error fetching metrics for selected version:", err);
      setError(`Failed to load metrics for version: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Prepare radar chart data
  const radarChartData = {
    labels: [
      'Topic Coherence',
      'Topic Diversity',
      'Document Coverage',
      'Uniqueness',
      'Silhouette Score',
      'Topic Separation'
    ],
    datasets: [
      {
        label: 'Current Model',
        data: metrics ? [
          metrics.coherence_score || 0,
          metrics.diversity_score || 0,
          metrics.document_coverage || 0,
          metrics.uniqueness_score || 0,
          metrics.silhouette_score || 0,
          metrics.topic_separation || 0
        ] : [0, 0, 0, 0, 0, 0],
        backgroundColor: 'rgba(46, 108, 219, 0.2)',
        borderColor: 'rgba(46, 108, 219, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(46, 108, 219, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(46, 108, 219, 1)'
      }
    ]
  };
  
  // Radar chart options
  const radarChartOptions = {
    scales: {
      r: {
        angleLines: {
          display: true
        },
        suggestedMin: 0,
        suggestedMax: 1
      }
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Topic Model Performance',
        font: {
          size: 18
        }
      }
    }
  };
  
  // Prepare metrics history chart data
  const metricsHistoryData = {
    labels: metricsHistory.map(m => m.version),
    datasets: [
      {
        label: 'Coherence',
        data: metricsHistory.map(m => m.coherence),
        borderColor: 'rgba(35, 34, 82, 1)',
        backgroundColor: 'rgba(35, 34, 82, 0.2)',
        tension: 0.4
      },
      {
        label: 'Diversity',
        data: metricsHistory.map(m => m.diversity),
        borderColor: 'rgba(46, 108, 219, 1)',
        backgroundColor: 'rgba(46, 108, 219, 0.2)',
        tension: 0.4
      },
      {
        label: 'Coverage',
        data: metricsHistory.map(m => m.coverage),
        borderColor: 'rgba(147, 100, 235, 1)',
        backgroundColor: 'rgba(147, 100, 235, 0.2)',
        tension: 0.4
      },
      {
        label: 'Uniqueness',
        data: metricsHistory.map(m => m.uniqueness),
        borderColor: 'rgba(231, 80, 174, 1)',
        backgroundColor: 'rgba(231, 80, 174, 0.2)',
        tension: 0.4
      }
    ]
  };
  
  // Metrics history chart options
  const metricsHistoryOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Model Performance Across Versions',
        font: {
          size: 18
        }
      },
      tooltip: {
        callbacks: {
          title: (context) => {
            const dataIndex = context[0].dataIndex;
            return metricsHistory[dataIndex] ? `${metricsHistory[dataIndex].version} (${formatDate(metricsHistory[dataIndex].date)})` : '';
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 1
      }
    }
  };
  
  // Prepare confusion matrix data
  const prepareConfusionMatrixData = () => {
    if (!confusionMatrix) return null;
    
    // Check structure and use alternative display if necessary
    if (!confusionMatrix.values || !confusionMatrix.labels) {
      // Alternative structure for API response
      if (confusionMatrix.matrix) {
        return {
          labels: confusionMatrix.classes || [],
          datasets: (confusionMatrix.matrix || []).map((row, index) => {
            const colors = [
              'rgba(54, 162, 235, 0.8)',
              'rgba(255, 206, 86, 0.8)',
              'rgba(255, 99, 132, 0.8)'
            ];
            
            return {
              label: confusionMatrix.classes ? confusionMatrix.classes[index] : `Class ${index + 1}`,
              data: row,
              backgroundColor: colors[index % colors.length],
              borderWidth: 1
            };
          })
        };
      }
      
      // Log warning for unexpected format
      console.warn('Confusion matrix data is not in expected format:', confusionMatrix);
      return null;
    }
    
    // Standard format
    const datasets = confusionMatrix.values.map((row, index) => {
      const colors = [
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 206, 86, 0.8)',
        'rgba(255, 99, 132, 0.8)'
      ];
      
      return {
        label: confusionMatrix.labels[index],
        data: row,
        backgroundColor: colors[index % colors.length],
        borderWidth: 1
      };
    });
    
    return {
      labels: confusionMatrix.labels,
      datasets
    };
  };
  
  // Confusion matrix options
  const confusionMatrixOptions = {
    responsive: true,
    scales: {
      x: {
        stacked: true,
      },
      y: {
        stacked: true
      }
    },
    plugins: {
      title: {
        display: true,
        text: 'Confusion Matrix (Sentiment Analysis Model)',
        font: {
          size: 18
        }
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            if (!confusionMatrix?.labels) return '';
            const datasetLabel = context.dataset.label || '';
            const value = context.parsed.y;
            const label = confusionMatrix.labels[context.dataIndex] || '';
            return `Predicted ${datasetLabel} as ${label}: ${value}%`;
          }
        }
      }
    }
  };
  
  // Topic distribution doughnut chart data
  const topicDistributionData = React.useMemo(() => {
    if (metrics && metrics.topic_distribution && Array.isArray(metrics.topic_distribution)) {
      // Use real data
      const labels = metrics.topic_distribution.map(t => t.name || `Topic ${t.id}`);
      const data = metrics.topic_distribution.map(t => t.count || t.percentage || 0);
      
      return {
        labels,
        datasets: [
          {
            data,
            backgroundColor: [
              '#232252',
              '#2e6cdb',
              '#9364eb',
              '#e750ae',
              '#f8986f',
              '#e1e5eb'
            ],
            borderWidth: 1
          }
        ]
      };
    }
    
    // Return empty data if not available
    return {
      labels: [],
      datasets: [{ data: [], backgroundColor: [], borderWidth: 1 }]
    };
  }, [metrics]);
  
  // Topic distribution options
  const topicDistributionOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'right',
      },
      title: {
        display: true,
        text: 'Topic Distribution',
        font: {
          size: 18
        }
      }
    }
  };

  // Function to render forecast vs actual chart
  const renderForecastChart = () => {
    if (!forecastData) {
      return (
        <div className="no-data-message">
          <p>No forecast data available</p>
        </div>
      );
    }
    
    const chartData = {
      labels: forecastData.dates || [],
      datasets: [
        {
          label: 'Actual Values',
          data: forecastData.actual || [],
          borderColor: '#232252',
          backgroundColor: 'rgba(35, 34, 82, 0.1)',
          tension: 0.3,
          pointRadius: 4
        },
        {
          label: 'Predicted Values',
          data: forecastData.predicted || [],
          borderColor: '#e750ae',
          backgroundColor: 'rgba(231, 80, 174, 0.1)',
          borderDash: [5, 5],
          tension: 0.3,
          pointRadius: 4
        }
      ]
    };
    
    return (
      <Line 
        data={chartData}
        options={{
          responsive: true,
          plugins: {
            title: {
              display: true,
              text: 'Prediction vs Actual Values',
              font: { size: 18 }
            }
          },
          scales: {
            y: {
              beginAtZero: false
            }
          }
        }}
      />
    );
  };
  
  // Function to render feature importance
  const renderFeatureImportance = () => {
    if (!featureImportance || !Array.isArray(featureImportance) || featureImportance.length === 0) {
      return (
        <div className="no-data-message">
          <p>No feature importance data available</p>
        </div>
      );
    }
    
    // Sort features by importance
    const sortedFeatures = [...featureImportance].sort((a, b) => b.importance - a.importance);
    
    return (
      <div className="feature-importance-grid">
        {sortedFeatures.map((feature, index) => (
          <div className="feature-item" key={index}>
            <div className="feature-name">{feature.name}</div>
            <div className="feature-bar-container">
              <div className="feature-bar" style={{ width: `${feature.importance * 100}%` }}></div>
              <span className="feature-value">{(feature.importance * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}
      </div>
    );
  };
  
  // Function to render sentiment examples
  const renderSentimentExamples = () => {
    if (!sentimentExamples || !Array.isArray(sentimentExamples) || sentimentExamples.length === 0) {
      return (
        <div className="no-data-message">
          <p>No sentiment example data available</p>
        </div>
      );
    }
    
    // Display up to 3 examples
    const exampleClasses = {
      positive: sentimentExamples.find(ex => ex.sentiment_score > 0.3),
      neutral: sentimentExamples.find(ex => ex.sentiment_score >= -0.1 && ex.sentiment_score <= 0.1),
      negative: sentimentExamples.find(ex => ex.sentiment_score < -0.3)
    };
    
    const getSentimentEmoji = (score) => {
      if (score >= 0.5) return '😄';
      if (score >= 0.1) return '🙂';
      if (score > -0.1) return '😐';
      if (score > -0.5) return '🙁';
      return '😠';
    };
    
    return (
      <div className="sentiment-examples-grid">
        {Object.entries(exampleClasses).map(([className, example]) => {
          if (!example) return null;
          
          return (
            <div className="sentiment-example" key={className}>
              <div className={`sentiment-example-text ${className}`}>
                "{example.text}"
              </div>
              <div className="sentiment-example-result">
                <div className="sentiment-emoji">{getSentimentEmoji(example.sentiment_score)}</div>
                <div className="sentiment-label">
                  {className.charAt(0).toUpperCase() + className.slice(1)} ({example.sentiment_score.toFixed(2)})
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="model-evaluation-page">
      <div className="model-evaluation-header">
        <h1 className="page-title">Model Evaluation</h1>
        <p className="schedule-info">Pipeline runs automatically every 6 hours to evaluate model performance</p>
        {selectedModel === 'topic_model' && (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '15px' }}>
            <ModelVersionBadge 
              version={modelVersions.find(v => v.id === selectedVersion)?.name || 'V1.0.2'} 
              date={modelVersions.find(v => v.id === selectedVersion)?.date ? formatDateTime(modelVersions.find(v => v.id === selectedVersion)?.date) : '16.5.2025, 20:28:13'} 
            />
          </div>
        )}
      </div>
      
      {/* Model Selector */}
      <div className="model-selector">
        <div className="model-selector-title">Select Model:</div>
        <div className="model-selector-buttons">
          <button 
            className={`model-selector-button ${selectedModel === 'topic_model' ? 'active' : ''}`}
            onClick={() => setSelectedModel('topic_model')}
          >
            Topic Model
          </button>
          <button 
            className={`model-selector-button ${selectedModel === 'sentiment_analysis' ? 'active' : ''}`}
            onClick={() => setSelectedModel('sentiment_analysis')}
          >
            Sentiment Analysis
          </button>
          <button 
            className={`model-selector-button ${selectedModel === 'trend_prediction' ? 'active' : ''}`}
            onClick={() => setSelectedModel('trend_prediction')}
          >
            Trend Prediction
          </button>
        </div>
      </div>
      
      {/* Version Selector */}
      <div className="version-selector">
        <div className="version-selector-title">Model Versions:</div>
        <div className="version-cards">
          {modelVersions.length > 0 ? (
            modelVersions.map(version => (
              <div 
                key={version.id}
                className={`version-card ${selectedVersion === version.id ? 'active' : ''} ${version.status === 'production' ? 'production' : ''}`}
                onClick={() => handleVersionSelect(version.id)}
              >
                <div className="version-name">{version.name}</div>
                <div className="version-date">{formatDateTime(version.date)}</div>
                {version.status === 'production' && (
                  <div className="version-status">Production</div>
                )}
              </div>
            ))
          ) : (
            <div className="no-versions">No model versions available</div>
          )}
        </div>
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
        <>
          <div className="metrics-overview">
            <div className="metrics-card">
              <h2>{selectedModel === 'topic_model' ? 'Topic Model Quality Metrics' : 
                  selectedModel === 'sentiment_analysis' ? 'Sentiment Analysis Performance' : 
                  'Trend Prediction Accuracy'}</h2>
              <div className="metrics-grid">
                {selectedModel === 'topic_model' && (
                  <>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.coherence_score || 0) * 1).toFixed(2)}</div>
                      <div className="metric-label">Coherence Score</div>
                      <div className="metric-description">
                        Measures how semantically coherent the topics are. Higher is better.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.diversity_score || 0) * 1).toFixed(2)}</div>
                      <div className="metric-label">Diversity Score</div>
                      <div className="metric-description">
                        Measures how distinct the topics are from each other. Higher is better.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{(((metrics.document_coverage || 0) * 100)).toFixed(0)}%</div>
                      <div className="metric-label">Document Coverage</div>
                      <div className="metric-description">
                        Percentage of documents assigned to at least one topic.
                      </div>
                    </div>
                    {metrics.total_documents ? (
                      <div className="metric-item">
                        <div className="metric-value">{formatNumber(metrics.total_documents)}</div>
                        <div className="metric-label">Total Documents</div>
                        <div className="metric-description">
                          Number of documents processed in the analysis.
                        </div>
                      </div>
                    ) : null}
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.silhouette_score || 0) * 1).toFixed(2)}</div>
                      <div className="metric-label">Silhouette Score</div>
                      <div className="metric-description">
                        Measures how well-separated the topics are. Higher is better.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.topic_quality || 0) * 1).toFixed(2)}</div>
                      <div className="metric-label">Topic Quality</div>
                      <div className="metric-description">
                        Overall quality score of the topics. Higher is better.
                      </div>
                    </div>
                  </>
                )}
                
                {selectedModel === 'sentiment_analysis' && metrics && (
                  <>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.accuracy || 0) * 100).toFixed(1)}%</div>
                      <div className="metric-label">Accuracy</div>
                      <div className="metric-description">
                        Overall accuracy of sentiment predictions.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.precision || 0) * 100).toFixed(1)}%</div>
                      <div className="metric-label">Precision</div>
                      <div className="metric-description">
                        Ability to avoid false positives in sentiment classification.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.recall || 0) * 100).toFixed(1)}%</div>
                      <div className="metric-label">Recall</div>
                      <div className="metric-description">
                        Ability to find all relevant sentiment cases.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.f1_score || 0) * 100).toFixed(1)}%</div>
                      <div className="metric-label">F1 Score</div>
                      <div className="metric-description">
                        Balance between precision and recall.
                      </div>
                    </div>
                    {metrics.training_samples && (
                      <div className="metric-item">
                        <div className="metric-value">{formatNumber(metrics.training_samples)}</div>
                        <div className="metric-label">Training Samples</div>
                        <div className="metric-description">
                          Number of samples used to train the model.
                        </div>
                      </div>
                    )}
                    {metrics.test_samples && (
                      <div className="metric-item">
                        <div className="metric-value">{formatNumber(metrics.test_samples)}</div>
                        <div className="metric-label">Test Samples</div>
                        <div className="metric-description">
                          Number of samples used to evaluate the model.
                        </div>
                      </div>
                    )}
                  </>
                )}
                
                {selectedModel === 'trend_prediction' && metrics && (
                  <>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.mape || 0) * 100).toFixed(1)}%</div>
                      <div className="metric-label">MAPE</div>
                      <div className="metric-description">
                        Mean Absolute Percentage Error - lower is better.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{((metrics.r_squared || 0) * 100).toFixed(1)}%</div>
                      <div className="metric-label">R²</div>
                      <div className="metric-description">
                        Coefficient of determination - higher is better.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{(metrics.rmse || 0).toFixed(2)}</div>
                      <div className="metric-label">RMSE</div>
                      <div className="metric-description">
                        Root Mean Square Error - lower is better.
                      </div>
                    </div>
                    <div className="metric-item">
                      <div className="metric-value">{(metrics.mae || 0).toFixed(2)}</div>
                      <div className="metric-label">MAE</div>
                      <div className="metric-description">
                        Mean Absolute Error - lower is better.
                      </div>
                    </div>
                    {metrics.time_series_length && (
                      <div className="metric-item">
                        <div className="metric-value">{formatNumber(metrics.time_series_length)}</div>
                        <div className="metric-label">Time Series Length</div>
                        <div className="metric-description">
                          Number of time points in the training data.
                        </div>
                      </div>
                    )}
                    {metrics.forecast_horizon && (
                      <div className="metric-item">
                        <div className="metric-value">{metrics.forecast_horizon}</div>
                        <div className="metric-label">Forecast Horizon</div>
                        <div className="metric-description">
                          How far into the future predictions are made.
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
          
          {/* Charts Section */}
          <div className="evaluation-charts">
            {/* Topic Model Charts */}
            {selectedModel === 'topic_model' && (
              <>
                <div className="charts-row">
                  <div className="chart-container">
                    {metrics ? (
                      <Radar data={radarChartData} options={radarChartOptions} />
                    ) : (
                      <div className="no-data-message">No radar chart data available</div>
                    )}
                  </div>
                  <div className="chart-container">
                    {metrics && metrics.topic_distribution && metrics.topic_distribution.length > 0 ? (
                      <Doughnut data={topicDistributionData} options={topicDistributionOptions} />
                    ) : (
                      <div className="no-data-message">No topic distribution data available</div>
                    )}
                  </div>
                </div>
                
                <div className="charts-row">
                  <div className="chart-container full-width">
                    {metricsHistory && metricsHistory.length > 0 ? (
                      <Line data={metricsHistoryData} options={metricsHistoryOptions} />
                    ) : (
                      <div className="no-data-message">No metrics history data available</div>
                    )}
                  </div>
                </div>
              </>
            )}
            
            {/* Sentiment Analysis Charts */}
            {selectedModel === 'sentiment_analysis' && (
              <>
                <div className="charts-row">
                  <div className="chart-container full-width">
                    {confusionMatrix ? (
                      <Bar data={prepareConfusionMatrixData()} options={confusionMatrixOptions} />
                    ) : (
                      <div className="no-data-message">No confusion matrix data available</div>
                    )}
                  </div>
                </div>
                
                <div className="sentiment-examples">
                  <h3>Example Classifications</h3>
                  {renderSentimentExamples()}
                </div>
              </>
            )}
            
            {/* Trend Prediction Charts */}
            {selectedModel === 'trend_prediction' && (
              <>
                <div className="charts-row">
                  <div className="chart-container full-width">
                    {renderForecastChart()}
                  </div>
                </div>
                
                <div className="prediction-features">
                  <h3>Important Prediction Features</h3>
                  {renderFeatureImportance()}
                </div>
              </>
            )}
          </div>
          
          {/* Model Monitoring */}
          <div className="model-monitoring">
            <h2>Model Monitoring</h2>
            <div className="monitoring-grid">
              <div className="monitoring-item">
                <div className="monitoring-header">
                  <h3>Model Health</h3>
                  <div className="monitoring-status status-healthy">
                    {metrics.model_health_status || "HEALTHY"}
                  </div>
                </div>
                <div className="monitoring-content">
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Prediction Drift</div>
                    <div className="monitoring-metric-value">
                      {metrics.prediction_drift ? `${(metrics.prediction_drift * 100).toFixed(1)}%` : 'N/A'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Feature Drift</div>
                    <div className="monitoring-metric-value">
                      {metrics.feature_drift ? `${(metrics.feature_drift * 100).toFixed(1)}%` : 'N/A'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Data Quality</div>
                    <div className="monitoring-metric-value">
                      {metrics.data_quality ? `${(metrics.data_quality * 100).toFixed(1)}%` : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="monitoring-item">
                <div className="monitoring-header">
                  <h3>Inference Stats</h3>
                  <div className="monitoring-stats">Last 7 days</div>
                </div>
                <div className="monitoring-content">
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Total Requests</div>
                    <div className="monitoring-metric-value">
                      {metrics.total_requests ? formatNumber(metrics.total_requests) : 'N/A'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Avg. Latency</div>
                    <div className="monitoring-metric-value">
                      {metrics.avg_latency ? `${metrics.avg_latency}ms` : 'N/A'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Error Rate</div>
                    <div className="monitoring-metric-value">
                      {metrics.error_rate !== undefined ? `${(metrics.error_rate * 100).toFixed(2)}%` : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="monitoring-item">
                <div className="monitoring-header">
                  <h3>Retraining Status</h3>
                  <div className="monitoring-status status-pending">
                    {metrics.training_status || "PENDING"}
                  </div>
                </div>
                <div className="monitoring-content">
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Next Scheduled</div>
                    <div className="monitoring-metric-value">
                      {metrics.next_training_date ? formatDate(metrics.next_training_date) : 'N/A'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Last Training</div>
                    <div className="monitoring-metric-value">
                      {metrics.last_training_date ? formatDate(metrics.last_training_date) : 'N/A'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">New Data</div>
                    <div className="monitoring-metric-value">
                      {metrics.new_data_samples ? `+${formatNumber(metrics.new_data_samples)} samples` : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
      
      {!loading && !error && !metrics && (
        <div className="no-data-container">
          <div className="no-data-message">
            <p>No evaluation data available for the selected model and time period.</p>
            <p>Please try selecting a different model or date range.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelEvaluation; 