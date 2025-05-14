import React from 'react';
import { Link } from 'react-router-dom';
import { useData } from '../context/DataContext';

const Navigation = () => {
    const { lastUpdate, error } = useData();

    return (
        <nav className="navbar">
            <div className="nav-brand">
                Social Media Trend Analysis
            </div>
            <div className="nav-links">
                <Link to="/" className="nav-link">Dashboard</Link>
                <Link to="/trends" className="nav-link">Trends</Link>
                <Link to="/search" className="nav-link">Suche</Link>
                <Link to="/analytics" className="nav-link">Analytics</Link>
            </div>
            <div className="nav-info">
                {error && <span className="error-badge">Fehler beim Laden</span>}
                {lastUpdate && (
                    <span className="update-badge">
                        Letztes Update: {new Date(lastUpdate).toLocaleTimeString()}
                    </span>
                )}
            </div>
        </nav>
    );
};

export default Navigation; 