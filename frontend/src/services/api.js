import axios from 'axios';

// API URL configuration - using a unified API that includes both main and drift API functionality
const API_URL = process.env.REACT_APP_API_URL || 
                'http://localhost:3001';  // Mock API server

console.log('API_URL set to:', API_URL);

// Improved Axios configuration
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',  // Prevents caching of responses
    },
    // Longer timeout for potentially slow connections
    timeout: 45000,
    // Disable CORS credentials since we're using proxy
    withCredentials: false
});

// IMPORTANT: Set this to false when real FastAPI endpoints are available
// This is a temporary configuration until the backend API is fully implemented
export const useMockApi = true; // Using mock API server

console.log('Using mock API:', useMockApi);

// Create a global state for tracking mock data usage
export let usingMockData = true; // Using mock data

// Function to check and set mock data usage state
export const setMockDataStatus = (isMockData) => {
    usingMockData = isMockData;
    // Dispatch an event so components can react
    window.dispatchEvent(new CustomEvent('mockdatachange', { 
        detail: { usingMockData } 
    }));
};

// Get the current mock data status
export const getMockDataStatus = () => usingMockData;

// Improved retry/connection logic
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second between retries

// Helper function for API calls with better retry logic
const apiCall = async (endpoint, method = 'get', data = null, options = {}, retries = MAX_RETRIES) => {
    // Force real data - don't use mock data even if configured
    // Reset mock data status
    setMockDataStatus(false);
    
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
        
        if (retries > 0) {
            console.log(`Retrying API call to ${endpoint}, ${retries} attempts left...`);
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
            return apiCall(endpoint, method, data, options, retries - 1);
        }
        
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

// New function to fetch recent social media data with improved reliability
export const fetchRecentData = async (platform = 'reddit', limit = 10) => {
    console.log(`Fetching recent ${platform} data (limit: ${limit})...`);
    
    try {
        // Always reset mock data status at start of request
        setMockDataStatus(false);
        
        // Try direct API call with proper retry mechanism
        for (let retry = 0; retry < MAX_RETRIES; retry++) {
            try {
                console.log(`API attempt ${retry + 1}/${MAX_RETRIES} for ${platform} data`);
                
                // Make the API request
                const response = await api.get(`/api/recent-data`, { 
                    params: { platform, limit },
                    // Increase timeout for this specific request
                    timeout: 60000
                });
                
                console.log(`Successfully fetched ${platform} data:`, response.status);
                
                // Process the response data
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
                        console.log('Processing response data type:', typeof response.data);
                        
                        // If response.data contains any array property, use that
                        for (const key in response.data) {
                            if (Array.isArray(response.data[key]) && response.data[key].length > 0) {
                                console.log(`Found array data in property "${key}"`);
                                return { data: response.data[key] };
                            }
                        }
                        
                        // If no array property found but response.data is an object
                        if (typeof response.data === 'object') {
                            console.log('Response data is an object without arrays, returning as single item array');
                            return { data: [response.data] };
                        }
                        
                        return { data: [] };
                    }
                }
                
                // If we get here, we didn't find usable data
                throw new Error('No usable data in API response');
                
            } catch (error) {
                if (retry < MAX_RETRIES - 1) {
                    console.log(`Retrying after ${RETRY_DELAY}ms, ${MAX_RETRIES - retry - 1} attempts left...`);
                    await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
                } else {
                    console.error(`All ${MAX_RETRIES} attempts failed:`, error);
                    throw error;
                }
            }
        }
        
        // This should never be reached due to the loop and error handling above
        throw new Error(`Failed to fetch ${platform} data after ${MAX_RETRIES} attempts`);
        
    } catch (error) {
        console.error(`Error fetching ${platform} data:`, error);
        throw new Error(`Failed to fetch ${platform} data: ${error.message}`);
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
        // Always reset mock data status at start of request
        setMockDataStatus(false);
        
        console.log("Fetching topic model data with params:", { 
            start_date: startDate, 
            end_date: endDate, 
            platforms, 
            num_topics: numTopics 
        });
        
        // Try POST first with improved error handling and explicit timeout
        try {
            console.log("Trying POST method to /api/topic-model");
            const response = await api.post('/api/topic-model', {
                start_date: startDate,
                end_date: endDate,
                platforms: platforms,
                num_topics: numTopics
            }, {
                timeout: 60000 // 60 second timeout
            });
            
            console.log("Topic model POST response:", response.data);
            
            // Check if topics is actually an array to avoid rendering issues
            if (response.data && !Array.isArray(response.data.topics)) {
                console.warn("Invalid topics format in POST response:", response.data.topics);
                response.data.topics = [];
            }
            
            return response.data;
        } 
        catch (postError) {
            console.warn(`POST request failed: ${postError.message}. Trying GET method...`);
            
            // If POST fails, try GET method
            console.log("Trying GET method to /api/topic-model");
            const getResponse = await api.get('/api/topic-model', {
                params: {
                    start_date: startDate,
                    end_date: endDate,
                    platforms: platforms.join(','),
                    num_topics: numTopics
                },
                timeout: 60000 // 60 second timeout
            });
            
            console.log("Topic model GET response:", getResponse.data);
            
            // Check if topics is actually an array to avoid rendering issues
            if (getResponse.data && !Array.isArray(getResponse.data.topics)) {
                console.warn("Invalid topics format in GET response:", getResponse.data.topics);
                getResponse.data.topics = [];
            }
            
            return getResponse.data;
        }
    } catch (error) {
        console.error('All topic model API endpoints failed:', error);
        
        // Try alternative endpoint if both main endpoints fail
        try {
            console.log("Trying alternative endpoint for topic model data...");
            const altResponse = await api.get('/api/db/topics', {
                params: {
                    start_date: startDate,
                    end_date: endDate
                },
                timeout: 60000 // 60 second timeout
            });
            
            console.log("Alternative topic model response:", altResponse.data);
            
            // Check for valid data structure
            if (altResponse.data && !Array.isArray(altResponse.data.topics)) {
                console.warn("Invalid topics format in alternative response:", altResponse.data.topics);
                altResponse.data.topics = [];
            }
            
            return altResponse.data;
        } catch (altError) {
            console.error('Error fetching from alternative endpoint:', altError);
            
            // Return an appropriate error response
            throw new Error("Failed to fetch topic model data from all available endpoints. Please try again later.");
        }
    }
};

/**
 * Fetch model drift data
 * 
 * @param {string} modelName - Model name
 * @param {string} version - Optional model version
 * @returns {Promise<Object>} - Drift metrics
 */
export const fetchModelDrift = async (modelName, version = null) => {
  try {
    const url = `/api/mlops/models/${modelName}/drift${version ? `?version=${version}` : ''}`;
    console.log(`Fetching model drift from: ${url}`);
    
    const response = await api.get(url);
    console.log('Model drift response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching model drift data:', error);
    // Return empty data instead of mock data
    return { 
      timestamp: "",
      dataset_drift: false,
      share_of_drifted_columns: 0,
      drifted_columns: []
    };
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

export const fetchPredictions = async (startDate = null, endDate = null) => {
    try {
        // Versuche zuerst, Vorhersagen von der Haupt-API zu holen
        console.log("Fetching predictions with params:", { startDate, endDate });
        
        const response = await api.get('/api/db/predictions', {
            params: {
                start_date: startDate,
                end_date: endDate
            }
        });
        
        console.log("Received predictions:", response.data);
        return response.data;
    } catch (error) {
        console.error('Error fetching predictions:', error);
        
        // Versuche alternative Endpunkte, falls der Hauptendpunkt fehlschlägt
        try {
            console.log("Trying alternative endpoint for predictions...");
            const altResponse = await api.get('/api/predictions', {
                params: {
                    start_date: startDate,
                    end_date: endDate
                }
            });
            
            console.log("Alternative predictions response:", altResponse.data);
            return altResponse.data;
        } catch (altError) {
            console.error('Error fetching from alternative endpoint:', altError);
            
            // Throw an error instead of returning mock data
            throw new Error("Failed to fetch prediction data from all available endpoints. Please try again later.");
        }
    }
};

// ML-Ops API Functions

/**
 * Fetch ML pipeline data
 * 
 * @param {string} pipelineId - Optional pipeline ID to fetch a specific pipeline
 * @returns {Promise<Object>} - Pipeline data
 */
export const fetchPipelines = async (pipelineId = null) => {
  try {
    const url = pipelineId 
      ? `/api/mlops/pipelines/${pipelineId}`
      : '/api/mlops/pipelines';
    
    console.log(`Fetching pipelines from: ${url}`);
    
    const response = await api.get(url);
    console.log('Pipeline response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching pipeline data:', error);
    // Return empty object instead of error message
    return pipelineId ? {} : {};
  }
};

/**
 * Fetch pipeline executions
 * 
 * @param {string} pipelineId - Pipeline ID
 * @returns {Promise<Array>} - Pipeline executions
 */
export const fetchPipelineExecutions = async (pipelineId) => {
  try {
    const url = `/api/mlops/pipelines/${pipelineId}/executions`;
    console.log(`Fetching pipeline executions from: ${url}`);
    
    // Use the unified API
    const response = await api.get(url);
    console.log('Pipeline executions response:', response.data);
    // Ensure we always return an array
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Error fetching pipeline executions:', error);
    // Return empty array instead of error message
    return [];
  }
};

/**
 * Execute a pipeline
 * 
 * @param {string} pipelineId - Pipeline ID
 * @returns {Promise<Object>} - Execution details
 */
export const executePipeline = async (pipelineId) => {
  try {
    console.log(`Executing pipeline: ${pipelineId}`);
    
    const url = `/api/mlops/pipelines/${pipelineId}/execute`;
    console.log(`Executing pipeline at: ${url}`);
    
    const response = await api.post(url);
    console.log('Pipeline execution response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error executing pipeline:', error);
    throw new Error(`Failed to execute pipeline: ${error.message}`);
  }
};

/**
 * Fetch model versions
 * 
 * @param {string} modelName - Model name
 * @returns {Promise<Array>} - Model versions
 */
export const fetchModelVersions = async (modelName) => {
  try {
    console.log(`Fetching model versions for: ${modelName}`);
    const response = await api.get(`/api/mlops/models/${modelName}/versions`);
    console.log('Model versions response:', response.data);
    // Ensure we always return an array
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Error fetching model versions:', error);
    return [];
  }
};

/**
 * Fetch model metrics
 * 
 * @param {string} modelName - Model name
 * @param {string} version - Optional model version
 * @returns {Promise<Object>} - Model metrics
 */
export const fetchModelMetrics = async (modelName, version = null) => {
  try {
    const url = `/api/mlops/models/${modelName}/metrics${version ? `?version=${version}` : ''}`;
    console.log(`Fetching model metrics from: ${url}`);
    const response = await api.get(url);
    console.log('Model metrics response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching model metrics:', error);
    return {};
  }
};

export default api; 