import React from 'react';

const Metrics = () => {
  const grafanaUrl = process.env.REACT_APP_GRAFANA_URL || 'http://localhost:3001';
  const dashboardUrl = `${grafanaUrl}/d/social-media-dashboard/social-media-analysis-dashboard?orgId=1&refresh=5s`;

  return (
    <div className="metrics-container" style={{ height: '100vh', width: '100%' }}>
      <iframe
        src={dashboardUrl}
        width="100%"
        height="100%"
        frameBorder="0"
        title="Metrics Dashboard"
      />
    </div>
  );
};

export default Metrics; 