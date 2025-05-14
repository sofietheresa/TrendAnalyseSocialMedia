import React, { createContext, useState, useContext, useEffect } from 'react';
import { fetchSocialMediaData } from '../services/api';

const DataContext = createContext();

export const useData = () => {
    const context = useContext(DataContext);
    if (!context) {
        throw new Error('useData must be used within a DataProvider');
    }
    return context;
};

export const DataProvider = ({ children }) => {
    const [socialMediaData, setSocialMediaData] = useState({
        reddit: [],
        tiktok: [],
        youtube: []
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    const loadData = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await fetchSocialMediaData();
            
            // Gruppiere Daten nach Plattform
            const groupedData = {
                reddit: data.filter(item => item.platform === 'reddit'),
                tiktok: data.filter(item => item.platform === 'tiktok'),
                youtube: data.filter(item => item.platform === 'youtube')
            };
            
            setSocialMediaData(groupedData);
            setLastUpdate(new Date());
        } catch (err) {
            setError(err.message);
            console.error('Error loading data:', err);
        } finally {
            setLoading(false);
        }
    };

    // Lade Daten beim ersten Render
    useEffect(() => {
        loadData();
    }, []);

    // Aktualisiere Daten alle 5 Minuten
    useEffect(() => {
        const interval = setInterval(loadData, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    const value = {
        socialMediaData,
        loading,
        error,
        lastUpdate,
        refreshData: loadData
    };

    return (
        <DataContext.Provider value={value}>
            {children}
        </DataContext.Provider>
    );
}; 