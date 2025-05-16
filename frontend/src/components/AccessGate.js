import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

// Set this to a secure random string in production
const ACCESS_TOKEN = 'social-media-trends-2025-secure';

const AccessGate = ({ children }) => {
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const location = useLocation();

  useEffect(() => {
    // Check if token exists in localStorage or as URL parameter
    const storedToken = localStorage.getItem('accessToken');
    const queryParams = new URLSearchParams(location.search);
    const urlToken = queryParams.get('access');

    if (storedToken === ACCESS_TOKEN) {
      setIsAuthorized(true);
    } else if (urlToken === ACCESS_TOKEN) {
      // If valid token is in URL, store it and grant access
      localStorage.setItem('accessToken', ACCESS_TOKEN);
      setIsAuthorized(true);
    }
  }, [location]);

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    
    if (password === 'TrendAnalyse2025') {
      localStorage.setItem('accessToken', ACCESS_TOKEN);
      setIsAuthorized(true);
      setError('');
    } else {
      setError('Ungültige Zugangsdaten');
      setTimeout(() => setError(''), 3000);
    }
  };

  if (isAuthorized) {
    return children;
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#f9f9f9',
      fontFamily: 'Sora, Arial, sans-serif'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '10px',
        padding: '30px',
        boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)',
        width: '90%',
        maxWidth: '400px',
        textAlign: 'center'
      }}>
        <h1 style={{ 
          color: '#6a33a0', 
          marginBottom: '20px',
          fontWeight: '700'
        }}>
          Social Media Trend Analysis
        </h1>
        
        <p style={{ marginBottom: '25px', color: '#555' }}>
          Diese Anwendung ist zugriffsbeschränkt. Bitte geben Sie das Passwort ein oder verwenden Sie einen autorisierten Link.
        </p>

        <form onSubmit={handlePasswordSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Passwort eingeben"
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '5px',
                border: '1px solid #ddd',
                fontSize: '16px'
              }}
            />
          </div>

          {error && (
            <p style={{ color: 'red', margin: '10px 0' }}>{error}</p>
          )}

          <button
            type="submit"
            style={{
              backgroundColor: '#6a33a0',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              padding: '12px 20px',
              fontSize: '16px',
              cursor: 'pointer',
              width: '100%'
            }}
          >
            Zugriff anfordern
          </button>
        </form>
      </div>
      
      <div style={{ marginTop: '20px', fontSize: '14px', color: '#888' }}>
        Zugriff nur für autorisierte Benutzer. Für Support kontaktieren Sie den Administrator.
      </div>
    </div>
  );
};

export default AccessGate; 