// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';

import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

function App() {

  // Default-Dummy-Daten, damit immer etwas angezeigt wird
  const [topics, setTopics] = useState([
    { topic: 'Topic 1', count: 123 },
    { topic: 'Topic 2', count: 87 },
    { topic: 'Topic 3', count: 56 }
  ]);
  const [sourceCounts, setSourceCounts] = useState({ Tiktok: 101, Youtube: 102, Reddit: 103 });

  const [fetchError, setFetchError] = useState(false);
  useEffect(() => {
    fetch('/data/processed/exploration_results.json')
      .then(res => {
        if (!res.ok) throw new Error('Datei nicht gefunden');
        return res.json();
      })
      .then(data => {
        if (data.top_topics) {
          setTopics(data.top_topics.slice(0, 5));
        } else if (data.topics) {
          setTopics(data.topics.slice(0, 5));
        }
        if (data.sources) {
          setSourceCounts(data.sources);
        }
      })
      .catch(err => {
        setFetchError(true);
        // Dummy-Daten bleiben erhalten
      });
  }, []);

  return (
    <Router>
      <div className="gradient-bg">
        <nav className="app-nav">
          <Link to="/" className="nav-link">Startseite</Link>
          <Link to="/daten" className="nav-link">Daten</Link>
          <Link to="/logs" className="nav-link">Logs</Link>
          <Link to="/pipeline" className="nav-link">Pipeline</Link>
          <Link to="/doku" className="nav-link">Doku</Link>
        </nav>
        {fetchError && (
          <div style={{ color: 'red', textAlign: 'center', margin: '1em' }}>
            Hinweis: Es konnten keine aktuellen Daten geladen werden. Dummy-Daten werden angezeigt.
          </div>
        )}
        <Routes>
          <Route path="/" element={
            <>
              <header className="App-header">
                <h1 className="main-title" style={{ fontFamily: 'Arial, sans-serif' }}>SOCIAL MEDIA Trend Analysis</h1>
              </header>
              <main className="App-main">
                <section className="topics-stack-section">
                  {topics.slice(0, 3).map((topic, i) => (
                    <div
                      key={topic.topic}
                      className={`topic-stack topic-stack-${i+1}`}
                      style={{
                        fontFamily: 'Arial, sans-serif',
                        fontWeight: i === 0 ? 900 : 700,
                        fontSize: i === 0 ? '3.2rem' : i === 1 ? '2.4rem' : '2rem',
                        opacity: i === 0 ? 1 : i === 1 ? 0.7 : 0.5,
                        textAlign: 'center',
                        color: '#2a2253',
                        margin: 0,
                        marginBottom: '0.2em',
                        letterSpacing: '0.01em',
                        lineHeight: 1.1
                      }}
                    >
                      {topic.topic}
                    </div>
                  ))}
                </section>

                <section className="postcount-row">
                  <div className="postcount-grid">
                    {Object.entries(sourceCounts).slice(0, 3).map(([quelle, anzahl], i) => (
                      <div key={quelle} className="postcount-col">
                        <div className="postcount-number">{String(i+1).padStart(2, '0')}</div>
                        <div className="postcount-source">{quelle}</div>
                      </div>
                    ))}
                  </div>
                </section>
              </main>
            </>
          } />
          <Route path="/daten" element={<Daten />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/doku" element={<Doku />} />
        </Routes>
      </div>
    </Router>
  );
}

function Daten() {
  return <div className="page-content"><h2 style={{ fontFamily: 'Arial, sans-serif' }}>Daten-Ansicht</h2><p style={{ fontFamily: 'Arial, sans-serif' }}>Hier könnten Daten angezeigt werden.</p></div>;
}
function Logs() {
  return <div className="page-content"><h2 style={{ fontFamily: 'Arial, sans-serif' }}>Logs</h2><p style={{ fontFamily: 'Arial, sans-serif' }}>Hier könnten Logs angezeigt werden.</p></div>;
}
function Pipeline() {
  return <div className="page-content"><h2 style={{ fontFamily: 'Arial, sans-serif' }}>Pipeline</h2><p style={{ fontFamily: 'Arial, sans-serif' }}>Hier könnte die Pipeline-Ansicht stehen.</p></div>;
}
function Doku() {
  return <div className="page-content"><h2 style={{ fontFamily: 'Arial, sans-serif' }}>Dokumentation</h2><p style={{ fontFamily: 'Arial, sans-serif' }}>Hier könnte die Doku stehen.</p></div>;
}

export default App;
