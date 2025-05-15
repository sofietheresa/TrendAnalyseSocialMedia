import axios from 'axios';

// API URL configuration - sicherstellen, dass die Railway URL verwendet wird
const API_URL = process.env.REACT_APP_API_URL || 
               'https://trendanalysesocialmedia-production.up.railway.app';

console.log('API_URL set to:', API_URL);

// Verbesserte Axios-Konfiguration
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',  // Verhindert Caching von Antworten
    },
    // Longer timeout for potentially slow connections
    timeout: 45000,
    // Disable CORS credentials since we're using proxy
    withCredentials: false
});

// Clearly mark if mock data is being used for visibility
export const useMockApi = false; // Mock API explizit deaktivieren
console.log('Using mock API:', useMockApi);

// Create a global state for tracking mock data usage
export let usingMockData = false;

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
    try {
        // Reset mock data status
        setMockDataStatus(false);
        
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
        
        // Only use mock data if all retries failed
        setMockDataStatus(true);
        
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
        
        // Try direct API call first with proper retry mechanism
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
                    // Wait before retry with increasing delay
                    const delay = RETRY_DELAY * (retry + 1);
                    console.log(`Waiting ${delay}ms before retrying ${platform} data...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                } else {
                    // Last retry failed, propagate the error
                    throw error;
                }
            }
        }
        
        // This should never be reached due to the throw in the final retry
        throw new Error('Failed to fetch data after all retries');
        
    } catch (error) {
        console.error(`Error fetching ${platform} data after all retries:`, error);
        
        // Set mock data status to true since we're using mock data
        setMockDataStatus(true);
        
        // Last resort: use mock data
        try {
            const { getMockData } = await import('../mock-api/data');
            const mockData = getMockData(platform, limit);
            console.warn(`Using MOCK DATA for ${platform} as fallback due to API failure`);
            
            return { 
                data: mockData, 
                isMockData: true,
                message: `Using mock data for ${platform} (API unavailable after ${MAX_RETRIES} retries)`
            };
        } catch (mockError) {
            console.error(`Failed to load mock data for ${platform}:`, mockError);
            return { 
                data: [],
                error: `Failed to load ${platform} data: ${error.message || 'Unknown error'}`
            };
        }
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
        
        // Mark as using mock data
        setMockDataStatus(true);
        
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
    return { error: `Failed to fetch pipeline data: ${error.message}` };
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
    console.log(`Fetching pipeline executions for: ${pipelineId}`);
    const response = await api.get(`/api/mlops/pipelines/${pipelineId}/executions`);
    console.log('Pipeline executions response:', response.data);
    // Ensure we always return an array
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Error fetching pipeline executions:', error);
    return { error: `Failed to fetch pipeline executions: ${error.message}` };
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
    const response = await api.post(`/api/mlops/pipelines/${pipelineId}/execute`);
    console.log('Pipeline execution response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error executing pipeline:', error);
    return { error: 'Failed to execute pipeline. Please try again later.' };
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
    return { error: `Failed to fetch model versions: ${error.message}` };
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
    return { error: 'Failed to fetch model metrics. Please try again later.' };
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
    return { error: 'Failed to fetch model drift data. Please try again later.' };
  }
};

export default api; 