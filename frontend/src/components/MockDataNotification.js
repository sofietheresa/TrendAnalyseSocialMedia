import React, { useState, useEffect } from 'react';
import { getMockDataStatus, useMockApi } from '../services/api';

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
        top: '80px', // Position below navbar
        left: '50%',
        transform: 'translateX(-50%)',
        backgroundColor: '#f8d7da',
        color: '#842029',
        borderRadius: '5px',
        padding: '10px 15px',
        fontSize: '14px',
        boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
        zIndex: 1000,
        maxWidth: '500px',
        border: '1px solid #f5c2c7',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center'
      }}
    >
      <div>
        <div style={{ fontWeight: 'bold', marginBottom: '5px', fontSize: '16px' }}>
          ⚠️ ENTWICKLUNGSMODUS: Mock-Daten in Verwendung
        </div>
        <div>
          {useMockApi ? (
            <span>
              Die Anwendung verwendet derzeit Testdaten, da die echten API-Endpunkte noch entwickelt werden.
            </span>
          ) : (
            <span>
              API-Verbindung nicht verfügbar. Es werden Testdaten angezeigt, bis die Verbindung wiederhergestellt ist.
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default MockDataNotification; 