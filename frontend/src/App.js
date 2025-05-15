// src/App.js
import React, { useState } from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import StatsPanel from './components/StatsPanel';

// Message bubble icon component
const MessageIcon = () => (
  <svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path 
      d="M60 0C26.9 0 0 24.1 0 53.8C0 83.5 26.9 107.6 60 107.6C93.1 107.6 120 83.5 120 53.8C120 24.1 93.1 0 60 0Z" 
      fill="url(#paint0_linear)" 
    />
    <circle cx="40" cy="54" r="8" fill="#ffffff" fillOpacity="0.9" />
    <circle cx="60" cy="54" r="8" fill="#ffffff" fillOpacity="0.9" />
    <circle cx="80" cy="54" r="8" fill="#ffffff" fillOpacity="0.9" />
    <defs>
      <linearGradient id="paint0_linear" x1="10" y1="10" x2="110" y2="110" gradientUnits="userSpaceOnUse">
        <stop stopColor="#9364eb" />
        <stop offset="0.5" stopColor="#e750ae" />
        <stop offset="1" stopColor="#f8986f" />
      </linearGradient>
    </defs>
  </svg>
);

// Homepage component
const Homepage = () => {
  return (
    <main className="app-content">
      {/* Title */}
      <h1 className="main-title">
        <span style={{ fontWeight: 900, letterSpacing: '0.03em' }}>SOCIAL MEDIA</span>
        <br />
        <span style={{ fontWeight: 400, fontSize: '0.8em' }}>Trend Analysis</span>
      </h1>
      
      {/* Topics Stack */}
      <div className="topics-stack-section">
        <div className="topic-stack topic-stack-1">Topic 1</div>
        <div className="topic-stack topic-stack-2">Topic 2</div>
        <div className="topic-stack topic-stack-3">Topic 3</div>
        <div className="topic-stack topic-stack-4">Topic 4</div>
        <div className="topic-stack topic-stack-5">Topic 5</div>
      </div>
    </main>
  );
};

// Stats page component
const StatsPage = () => {
  return (
    <main className="app-content">
      <h1 className="page-title">Statistics Overview</h1>
      <StatsPanel />
    </main>
  );
};

// Simple placeholder for other pages
const PlaceholderPage = ({ title }) => (
  <main className="app-content">
    <h1 className="page-title">{title}</h1>
    <div className="placeholder-content">
      <p>This page is under construction.</p>
    </div>
  </main>
);

function App() {
  const [activePage, setActivePage] = useState('home');

  return (
    <Router>
      <div className="App">
        {/* Navigation */}
        <nav className="app-nav">
          <Link 
            to="/" 
            className="nav-link" 
            onClick={() => setActivePage('home')}
            style={{ fontWeight: activePage === 'home' ? 700 : 400 }}
          >
            Startseite
          </Link>
          <Link 
            to="/pipeline" 
            className="nav-link" 
            onClick={() => setActivePage('pipeline')}
            style={{ fontWeight: activePage === 'pipeline' ? 700 : 400 }}
          >
            Pipeline
          </Link>
          <Link 
            to="/stats" 
            className="nav-link" 
            onClick={() => setActivePage('stats')}
            style={{ fontWeight: activePage === 'stats' ? 700 : 400 }}
          >
            Statistiken
          </Link>
          <Link 
            to="/logs" 
            className="nav-link" 
            onClick={() => setActivePage('logs')}
            style={{ fontWeight: activePage === 'logs' ? 700 : 400 }}
          >
            Logs
          </Link>
          <Link 
            to="/docs" 
            className="nav-link" 
            onClick={() => setActivePage('docs')}
            style={{ fontWeight: activePage === 'docs' ? 700 : 400 }}
          >
            Doku
          </Link>
        </nav>
        
        {/* Page Routes */}
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="/pipeline" element={<PlaceholderPage title="Pipeline" />} />
          <Route path="/logs" element={<PlaceholderPage title="Logs" />} />
          <Route path="/docs" element={<PlaceholderPage title="Documentation" />} />
        </Routes>
        
        {/* Footer */}
        <footer className="app-footer">
          <p>© 2025 TrendAnalyseSocialMedia</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
