import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
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

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function App() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch('/status');
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError('Fehler beim Laden des Status');
    }
  };

  const runPipeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/run-pipeline', {
        method: 'POST',
      });
      const data = await response.json();
      setResults(data);
      fetchStatus();
    } catch (err) {
      setError('Fehler beim Ausführen der Pipeline');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Alle 30 Sekunden aktualisieren
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <header>
        <h1>Social Media Analysis Dashboard</h1>
      </header>

      <main>
        <section className="status-section">
          <h2>Status</h2>
          {status && (
            <div className="status-info">
              <p>Letztes Update: {status.last_update || 'Keine Daten'}</p>
              <p>Verfügbare Ergebnisse: {status.available_results.length}</p>
            </div>
          )}
        </section>

        <section className="actions-section">
          <button 
            onClick={runPipeline} 
            disabled={loading}
            className="run-button"
          >
            {loading ? 'Pipeline läuft...' : 'Pipeline starten'}
          </button>
        </section>

        {error && (
          <section className="error-section">
            <p className="error-message">{error}</p>
          </section>
        )}

        {results && (
          <section className="results-section">
            <h2>Letzte Ergebnisse</h2>
            <div className="results-content">
              <pre>{JSON.stringify(results, null, 2)}</pre>
            </div>
          </section>
        )}
      </main>

      <style jsx>{`
        .App {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }

        header {
          text-align: center;
          margin-bottom: 40px;
        }

        section {
          background: white;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 20px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .run-button {
          background: #007bff;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
        }

        .run-button:disabled {
          background: #ccc;
        }

        .error-message {
          color: #dc3545;
          padding: 10px;
          background: #f8d7da;
          border-radius: 4px;
        }

        .results-content {
          background: #f8f9fa;
          padding: 15px;
          border-radius: 4px;
          overflow-x: auto;
        }

        pre {
          margin: 0;
          white-space: pre-wrap;
        }
      `}</style>
    </div>
  );
}

export default App; 