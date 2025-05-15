import React, { useState, useEffect } from 'react';
import { getMockDataStatus } from '../services/api';

/**
 * Component that displays a notification when mock data is being used
 */
const MockDataNotification = () => {
  const [showNotification, setShowNotification] = useState(getMockDataStatus());

  useEffect(() => {
    // Setup event listener for mock data changes
    const handleMockDataChange = (event) => {
      setShowNotification(event.detail.usingMockData);
    };

    // Add event listener
    window.addEventListener('mockdatachange', handleMockDataChange);

    // Initial check
    setShowNotification(getMockDataStatus());

    // Cleanup
    return () => {
      window.removeEventListener('mockdatachange', handleMockDataChange);
    };
  }, []);

  if (!showNotification) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '15px',
        right: '15px',
        backgroundColor: '#f8d7da',
        color: '#842029',
        borderRadius: '5px',
        padding: '10px 15px',
        fontSize: '14px',
        boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
        zIndex: 1000,
        maxWidth: '300px',
        border: '1px solid #f5c2c7'
      }}
    >
      <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
        ⚠️ Mock-Daten in Verwendung
      </div>
      <div>
        API-Verbindung nicht verfügbar. Es werden Testdaten angezeigt, bis die Verbindung wiederhergestellt ist.
      </div>
    </div>
  );
};

export default MockDataNotification; 