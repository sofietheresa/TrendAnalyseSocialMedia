import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState(null);
  const [stepStatus, setStepStatus] = useState({
    data_ingestion: 'idle',
    preprocessing: 'idle',
    data_exploration: 'idle',
    prediction: 'idle'
  });

  const runPipelineStep = async (step) => {
    try {
      setStepStatus(prev => ({ ...prev, [step]: 'running' }));
      const response = await fetch(`/api/run-pipeline/${step}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setStepStatus(prev => ({ ...prev, [step]: 'completed' }));
      return data;
    } catch (error) {
      setStepStatus(prev => ({ ...prev, [step]: 'error' }));
      setError(error.message);
      throw error;
    }
  };

  const runFullPipeline = async () => {
    try {
      setStatus('running');
      setError(null);
      
      // Run each step in sequence
      await runPipelineStep('data_ingestion');
      await runPipelineStep('preprocessing');
      await runPipelineStep('data_exploration');
      await runPipelineStep('prediction');
      
      setStatus('completed');
    } catch (error) {
      setStatus('error');
      setError(error.message);
    }
  };

  const getButtonClass = (status) => {
    switch (status) {
      case 'running': return 'button-running';
      case 'completed': return 'button-completed';
      case 'error': return 'button-error';
      default: return 'button-idle';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Social Media Trend Analysis</h1>
      </header>
      
      <main className="App-main">
        <section className="pipeline-controls">
          <h2>Pipeline Steuerung</h2>
          
          <div className="pipeline-buttons">
            <button 
              className={`pipeline-button ${getButtonClass(status)}`}
              onClick={runFullPipeline}
              disabled={status === 'running'}
            >
              Gesamte Pipeline starten
            </button>
          </div>

          <div className="step-buttons">
            <h3>Einzelne Schritte</h3>
            <button 
              className={`step-button ${getButtonClass(stepStatus.data_ingestion)}`}
              onClick={() => runPipelineStep('data_ingestion')}
              disabled={stepStatus.data_ingestion === 'running'}
            >
              Daten-Import
            </button>
            
            <button 
              className={`step-button ${getButtonClass(stepStatus.preprocessing)}`}
              onClick={() => runPipelineStep('preprocessing')}
              disabled={stepStatus.preprocessing === 'running'}
            >
              Vorverarbeitung
            </button>
            
            <button 
              className={`step-button ${getButtonClass(stepStatus.data_exploration)}`}
              onClick={() => runPipelineStep('data_exploration')}
              disabled={stepStatus.data_exploration === 'running'}
            >
              Daten-Exploration
            </button>
            
            <button 
              className={`step-button ${getButtonClass(stepStatus.prediction)}`}
              onClick={() => runPipelineStep('prediction')}
              disabled={stepStatus.prediction === 'running'}
            >
              Vorhersage
            </button>
          </div>
        </section>

        {error && (
          <div className="error-message">
            <h3>Fehler</h3>
            <p>{error}</p>
          </div>
        )}

        <section className="status-section">
          <h2>Status</h2>
          <div className="status-grid">
            <div className="status-item">
              <span>Daten-Import:</span>
              <span className={stepStatus.data_ingestion}>{stepStatus.data_ingestion}</span>
            </div>
            <div className="status-item">
              <span>Vorverarbeitung:</span>
              <span className={stepStatus.preprocessing}>{stepStatus.preprocessing}</span>
            </div>
            <div className="status-item">
              <span>Daten-Exploration:</span>
              <span className={stepStatus.data_exploration}>{stepStatus.data_exploration}</span>
            </div>
            <div className="status-item">
              <span>Vorhersage:</span>
              <span className={stepStatus.prediction}>{stepStatus.prediction}</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App; 