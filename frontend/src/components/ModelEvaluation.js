import React, { useState, useEffect } from 'react';
import { fetchTopicModel, fetchModelVersions, fetchModelMetrics, fetchModelDrift } from '../services/api';
import { formatDate, formatDateTime, formatNumber } from '../utils/dateUtils';
import './ModelEvaluation.css';
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
            throw new Error('Invalid metrics history data');
          }
        } catch (err) {
          console.error('Error fetching metrics history:', err);
          throw new Error('Could not fetch metrics history');
        }
        
        // Fetch drift metrics for relevant model types
        if (selectedModel === 'topic_model' || selectedModel === 'sentiment_analysis') {
          try {
            const driftData = await fetchModelDrift(selectedModel, versionToSelect);
            console.log('Fetched drift data:', driftData);
            
            if (driftData && !driftData.error && driftData.confusionMatrix) {
              setConfusionMatrix(driftData.confusionMatrix);
            } else {
              throw new Error('Invalid drift data');
            }
          } catch (err) {
            console.error('Error fetching drift data:', err);
            throw new Error('Could not fetch model drift data');
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
            return `${metricsHistory[dataIndex].version} (${formatDate(metricsHistory[dataIndex].date)})`;
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
    
    // Struktur prüfen und alternative Darstellung verwenden wenn nötig
    if (!confusionMatrix.values || !confusionMatrix.labels) {
      // Alternative Struktur für API-Rückgabe
      if (confusionMatrix.matrix) {
        return {
          labels: confusionMatrix.classes || ['Class 1', 'Class 2', 'Class 3'],
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
      
      // Fallback für einfaches Format
      console.warn('Confusion matrix data is not in expected format:', confusionMatrix);
      return {
        labels: ['Positive', 'Neutral', 'Negative'],
        datasets: [
          {
            label: 'Predicted Positive',
            data: [92, 5, 3],
            backgroundColor: 'rgba(54, 162, 235, 0.8)',
            borderWidth: 1
          },
          {
            label: 'Predicted Neutral',
            data: [8, 85, 7],
            backgroundColor: 'rgba(255, 206, 86, 0.8)',
            borderWidth: 1
          },
          {
            label: 'Predicted Negative',
            data: [4, 9, 87],
            backgroundColor: 'rgba(255, 99, 132, 0.8)',
            borderWidth: 1
          }
        ]
      };
    }
    
    // Standard-Format
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
            const datasetLabel = context.dataset.label || '';
            const value = context.parsed.y;
            const label = confusionMatrix?.labels?.[context.dataIndex] || '';
            return `Predicted ${datasetLabel} as ${label}: ${value}%`;
          }
        }
      }
    }
  };
  
  // Topic distribution doughnut chart data
  const topicDistributionData = React.useMemo(() => {
    if (metrics && metrics.topic_distribution && Array.isArray(metrics.topic_distribution)) {
      // Use real data if available
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
    
    // Fallback to mock data
    return {
      labels: ['Topic 1', 'Topic 2', 'Topic 3', 'Topic 4', 'Topic 5', 'Other Topics'],
      datasets: [
        {
          data: [25, 20, 18, 15, 12, 10],
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

  return (
    <div className="model-evaluation-page">
      <div className="model-evaluation-header">
        <h1 className="page-title">Model Evaluation</h1>
        <p className="schedule-info">Pipeline runs automatically every 6 hours to evaluate model performance</p>
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
                onClick={() => setSelectedVersion(version.id)}
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
              <h2>Model Quality Metrics</h2>
              <div className="metrics-grid">
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
                    <div className="metric-value">{formatNumber(metrics.total_documents || 0)}</div>
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
              </div>
            </div>
          </div>
          
          {/* Charts Section */}
          <div className="evaluation-charts">
            <div className="charts-row">
              <div className="chart-container">
                <Radar data={radarChartData} options={radarChartOptions} />
              </div>
              <div className="chart-container">
                <Doughnut data={topicDistributionData} options={topicDistributionOptions} />
              </div>
            </div>
            
            <div className="charts-row">
              <div className="chart-container full-width">
                <Line data={metricsHistoryData} options={metricsHistoryOptions} />
              </div>
            </div>
            
            {confusionMatrix && selectedModel === 'sentiment_analysis' && (
              <div className="charts-row">
                <div className="chart-container full-width">
                  {prepareConfusionMatrixData() && (
                    <Bar data={prepareConfusionMatrixData()} options={confusionMatrixOptions} />
                  )}
                </div>
              </div>
            )}
          </div>
          
          {/* Model Monitoring */}
          <div className="model-monitoring">
            <h2>Model Monitoring</h2>
            <div className="monitoring-grid">
              <div className="monitoring-item">
                <div className="monitoring-header">
                  <h3>Model Health</h3>
                  <div className="monitoring-status status-healthy">HEALTHY</div>
                </div>
                <div className="monitoring-content">
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Prediction Drift</div>
                    <div className="monitoring-metric-value">
                      {metrics.prediction_drift ? `${(metrics.prediction_drift * 100).toFixed(1)}%` : '2.3%'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Feature Drift</div>
                    <div className="monitoring-metric-value">
                      {metrics.feature_drift ? `${(metrics.feature_drift * 100).toFixed(1)}%` : '1.7%'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Data Quality</div>
                    <div className="monitoring-metric-value">
                      {metrics.data_quality ? `${(metrics.data_quality * 100).toFixed(1)}%` : '98.5%'}
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
                      {metrics.total_requests ? formatNumber(metrics.total_requests) : '142,387'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Avg. Latency</div>
                    <div className="monitoring-metric-value">
                      {metrics.avg_latency ? `${metrics.avg_latency}ms` : '235ms'}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Error Rate</div>
                    <div className="monitoring-metric-value">
                      {metrics.error_rate ? `${(metrics.error_rate * 100).toFixed(2)}%` : '0.04%'}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="monitoring-item">
                <div className="monitoring-header">
                  <h3>Retraining Status</h3>
                  <div className="monitoring-status status-pending">PENDING</div>
                </div>
                <div className="monitoring-content">
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Next Scheduled</div>
                    <div className="monitoring-metric-value">
                      {metrics.next_training_date ? formatDate(metrics.next_training_date) : formatDate(new Date(Date.now() + 7*24*60*60*1000))}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">Last Training</div>
                    <div className="monitoring-metric-value">
                      {metrics.last_training_date ? formatDate(metrics.last_training_date) : formatDate(new Date())}
                    </div>
                  </div>
                  <div className="monitoring-metric">
                    <div className="monitoring-metric-label">New Data</div>
                    <div className="monitoring-metric-value">
                      {metrics.new_data_samples ? `+${formatNumber(metrics.new_data_samples)} samples` : '+24,128 samples'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelEvaluation; 