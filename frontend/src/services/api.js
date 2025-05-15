import axios from 'axios';

// API URL configuration with Railway deployment URL
const API_URL = process.env.REACT_APP_API_URL || 
                'https://trendanalysesocialmedia-production.up.railway.app';

console.log('API_URL set to:', API_URL);

// Axios-Instanz mit Standardkonfiguration und Debug-Info
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json'
    },
    // Add longer timeout for debugging
    timeout: 30000,
    // Enable CORS with credentials
    withCredentials: false
});

// Detailed Error Handler
api.interceptors.request.use(
    config => {
        console.log(`🚀 Making ${config.method.toUpperCase()} request to: ${config.baseURL}${config.url}`);
        return config;
    },
    error => {
        console.error('❌ Request error:', error);
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    response => {
        console.log(`✅ Response from ${response.config.url}:`, response.status);
        return response;
    },
    error => {
        console.error('❌ API Error Details:', {
            url: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            data: error.response?.data,
            message: error.message
        });
        return Promise.reject(error);
    }
);

// Helper function for better error handling
const apiCall = async (endpoint, method = 'get', data = null, options = {}) => {
    try {
        const config = { 
            ...options,
            method,
            url: endpoint,
            data: method !== 'get' ? data : undefined,
            params: method === 'get' ? data : undefined
        };
        
        const response = await api(config);
        return response.data;
    } catch (error) {
        console.error(`Failed API call to ${endpoint}:`, error);
        
        // Enhance error message with details
        const enhancedError = new Error(
            `API Error (${error.response?.status || 'network'}): ${error.message}`
        );
        enhancedError.originalError = error;
        enhancedError.status = error.response?.status;
        enhancedError.data = error.response?.data;
        
        throw enhancedError;
    }
};

// API-Funktionen mit verbessertem Error-Handling
export const fetchScraperStatus = async () => {
    console.log("Fetching scraper status...");
    try {
        const response = await apiCall('/api/scraper-status');
        console.log("Scraper status raw response:", response);
        
        // If the API returns "running" as a string "true", convert it to a boolean
        if (response) {
            Object.keys(response).forEach(platform => {
                if (response[platform] && response[platform].running === "true") {
                    response[platform].running = true;
                }
            });
        }
        
        return response;
    } catch (error) {
        console.error('Error fetching scraper status:', error);
        throw error;
    }
};

export const fetchDailyStats = async () => {
    console.log("Fetching daily stats...");
    try {
        return await apiCall('/api/daily-stats');
    } catch (error) {
        console.error('Error fetching daily stats:', error);
        throw error;
    }
};

// New function to fetch recent social media data
export const fetchRecentData = async (platform = 'reddit', limit = 10) => {
    console.log(`Fetching recent ${platform} data (limit: ${limit})...`);
    try {
        const response = await api.get(`/api/recent-data`, { 
            params: { platform, limit } 
        });
        
        console.log(`Received ${platform} data:`, response);
        
        if (response.data) {
            // If response.data is an array, return it directly wrapped in an object
            if (Array.isArray(response.data)) {
                return { data: response.data };
            }
            // If response.data.data exists and is an array, return the response as is
            else if (response.data.data && Array.isArray(response.data.data)) {
                return response.data;
            }
            // Otherwise, try to parse the data intelligently
            else {
                console.warn('Response format not recognized:', response.data);
                
                // If response.data contains any array property, use that
                for (const key in response.data) {
                    if (Array.isArray(response.data[key]) && response.data[key].length > 0) {
                        console.log(`Found array data in property "${key}"`);
                        return { data: response.data[key] };
                    }
                }
                
                return { data: [] };
            }
        } else {
            console.warn('Empty response from API');
            return { data: [] };
        }
    } catch (error) {
        console.error(`Error fetching recent ${platform} data:`, error);
        // Return empty data rather than throwing to allow for graceful UI handling
        return { data: [] };
    }
};

// Other API functions using the enhanced apiCall helper
export const fetchSocialMediaData = async () => {
    try {
        return await apiCall('/data');
    } catch (error) {
        console.error('Error fetching social media data:', error);
        throw error;
    }
};

export const fetchTrendAnalysis = async (platform = null) => {
    try {
        const params = platform ? { platform } : {};
        const response = await api.get('/trends', { params });
        return response.data;
    } catch (error) {
        console.error('Error fetching trend analysis:', error);
        throw error;
    }
};

export const searchContent = async (query, platform = null) => {
    try {
        const params = { query, ...(platform && { platform }) };
        const response = await api.get('/search', { params });
        return response.data;
    } catch (error) {
        console.error('Error searching content:', error);
        throw error;
    }
};

export const fetchTopics = async (startDate, endDate) => {
    try {
        const response = await api.get('/api/db/topics', {
            params: { start_date: startDate, end_date: endDate }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching topics:', error);
        if (error.response) {
            throw new Error(`Serverfehler: ${error.response.data.detail || 'Unbekannter Fehler'}`);
        } else if (error.request) {
            throw new Error('Keine Verbindung zum Server möglich');
        } else {
            throw new Error('Fehler beim Laden der Daten');
        }
    }
};

// New function to fetch topic model data with BERT
export const fetchTopicModel = async (startDate = null, endDate = null, platforms = ["reddit", "tiktok", "youtube"], numTopics = 5) => {
    try {
        console.log("Fetching topic model data with params:", { 
            start_date: startDate, 
            end_date: endDate, 
            platforms, 
            num_topics: numTopics 
        });
        
        const response = await api.post('/api/topic-model', {
            start_date: startDate,
            end_date: endDate,
            platforms: platforms,
            num_topics: numTopics
        });
        
        console.log("Topic model response:", response.data);
        
        // Check if topics is actually an array to avoid rendering issues
        if (response.data && !Array.isArray(response.data.topics)) {
            console.warn("Invalid topics format in response:", response.data.topics);
            response.data.topics = [];
        }
        
        return response.data;
    } catch (error) {
        console.error('Error fetching topic model data:', error);
        
        // Provide detailed error messages based on the error type
        if (error.response) {
            console.error('Server response:', error.response.data);
            return {
                error: `Serverfehler: ${error.response.data.detail || 'Unbekannter Fehler'}`,
                topics: [],
                metrics: {
                    coherence_score: 0,
                    diversity_score: 0,
                    total_documents: 0,
                    document_coverage: 0
                },
                time_range: {
                    start_date: startDate || new Date(Date.now() - 3*24*60*60*1000).toISOString().split('T')[0],
                    end_date: endDate || new Date().toISOString().split('T')[0]
                }
            };
        } else if (error.request) {
            return {
                error: 'Keine Verbindung zum Server möglich',
                topics: [],
                metrics: null,
                time_range: {
                    start_date: startDate || new Date(Date.now() - 3*24*60*60*1000).toISOString().split('T')[0],
                    end_date: endDate || new Date().toISOString().split('T')[0]
                }
            };
        } else {
            return {
                error: 'Fehler beim Laden der Topic-Daten',
                topics: [],
                metrics: null,
                time_range: {
                    start_date: startDate || new Date(Date.now() - 3*24*60*60*1000).toISOString().split('T')[0],
                    end_date: endDate || new Date().toISOString().split('T')[0]
                }
            };
        }
    }
};

export const fetchSourceStats = async () => {
    try {
        const response = await api.get('/api/db/sources/stats');
        return response.data;
    } catch (error) {
        console.error('Error fetching source statistics:', error);
        if (error.response) {
            throw new Error(`Serverfehler: ${error.response.data.detail || 'Unbekannter Fehler'}`);
        } else if (error.request) {
            throw new Error('Keine Verbindung zum Server möglich');
        } else {
            throw new Error('Fehler beim Laden der Quellenstatistiken');
        }
    }
};

export const fetchLogs = async (source = 'all') => {
    try {
        let logs = [];
        if (source === 'all' || source === 'tiktok') {
            const tiktokResponse = await api.get('/logs/tiktok.log');
            logs = [...logs, ...parseLogs(tiktokResponse.data, 'TikTok')];
        }
        if (source === 'all' || source === 'reddit') {
            const redditResponse = await api.get('/logs/reddit.log');
            logs = [...logs, ...parseLogs(redditResponse.data, 'Reddit')];
        }
        if (source === 'all' || source === 'youtube') {
            const youtubeResponse = await api.get('/logs/youtube.log');
            logs = [...logs, ...parseLogs(youtubeResponse.data, 'YouTube')];
        }
        
        // Sortiere Logs nach Zeitstempel
        return logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    } catch (error) {
        console.error('Error fetching logs:', error);
        if (error.response) {
            throw new Error(`Serverfehler: ${error.response.data.detail || 'Unbekannter Fehler'}`);
        } else if (error.request) {
            throw new Error('Keine Verbindung zum Server möglich');
        } else {
            throw new Error('Fehler beim Laden der Logs');
        }
    }
};

const parseLogs = (logText, source) => {
    return logText.split('\n')
        .filter(line => line.trim())
        .map(line => {
            const [timestamp, level, ...messageParts] = line.split(' ');
            return {
                timestamp,
                level: level.replace('[', '').replace(']', ''),
                message: messageParts.join(' '),
                source
            };
        });
};

export const fetchPresentation = async () => {
    try {
        const response = await api.get('/docs/SocialMediaTA_draft.pptx', {
            responseType: 'blob'
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching presentation:', error);
        if (error.response) {
            throw new Error(`Serverfehler: ${error.response.data.detail || 'Unbekannter Fehler'}`);
        } else if (error.request) {
            throw new Error('Keine Verbindung zum Server möglich');
        } else {
            throw new Error('Fehler beim Laden der Präsentation');
        }
    }
};

export const fetchAnalysisData = async () => {
    try {
        const response = await api.get('/api/db/analysis');
        return response.data;
    } catch (error) {
        console.error('Error fetching analysis data:', error);
        if (error.response) {
            throw new Error(`Serverfehler: ${error.response.data.detail || 'Unbekannter Fehler'}`);
        } else if (error.request) {
            throw new Error('Keine Verbindung zum Server möglich');
        } else {
            throw new Error('Fehler beim Laden der Analysedaten');
        }
    }
};

export const fetchPredictions = async () => {
    try {
        const response = await api.get('/api/db/predictions');
        return response.data;
    } catch (error) {
        console.error('Error fetching predictions:', error);
        if (error.response) {
            throw new Error(`Serverfehler: ${error.response.data.detail || 'Unbekannter Fehler'}`);
        } else if (error.request) {
            throw new Error('Keine Verbindung zum Server möglich');
        } else {
            throw new Error('Fehler beim Laden der Vorhersagen');
        }
    }
};

export default api; 