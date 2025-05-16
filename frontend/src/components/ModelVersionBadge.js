import React from 'react';

/**
 * A badge component to display the topic model version information
 * with proper layout that prevents text overlap
 */
const ModelVersionBadge = ({ version = 'V1.0.2', date = '16.5.2025, 20:28:13' }) => {
  return (
    <div className="model-version-badge">
      <div className="model-version-header">Topic Model {version}</div>
      <div className="model-version-date">{date}</div>
    </div>
  );
};

export default ModelVersionBadge; 