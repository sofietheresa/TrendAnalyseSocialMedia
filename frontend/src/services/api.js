import axios from 'axios';

// API URL configuration - using a unified API that includes both main and drift API functionality
const API_URL = process.env.REACT_APP_API_URL || 
                'http://localhost:8000';  // FastAPI server

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
export const useMockApi = false; // Using real API server

console.log('Using mock API:', useMockApi);

// Create a global state for tracking mock data usage
export let usingMockData = false; // Always using real data

// Function to check and set mock data usage state
export const setMockDataStatus = (isMockData) => {
    // Override to always use real data
    usingMockData = false;
    
    // Dispatch an event so components can react
    window.dispatchEvent(new CustomEvent('mockdatachange', { 
        detail: { usingMockData: false } 
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

// Verbesserte Funktion zum Abrufen aktueller Social-Media-Daten aus der DB
export const fetchRecentData = async (platform = 'all', limit = 10) => {
    console.log(`Fetching recent ${platform} data (limit: ${limit})...`);
    
    try {
        // Always reset mock data status at start of request
        setMockDataStatus(false);
        
        // Versuche direkten DB-Endpunkt zuerst
        try {
            console.log(`Direkter DB-Zugriffsversuch für ${platform}-Daten`);
            
            // Mache den API-Request
            const response = await api.get(`/api/db/posts/recent`, { 
                params: { 
                    platform: platform !== 'all' ? platform : undefined, 
                    limit 
                },
                timeout: 60000
            });
            
            console.log(`Erfolgreich ${platform}-Daten aus DB abgerufen:`, response.status);
            
            // Verarbeite die Antwortdaten
            if (response.data) {
                if (Array.isArray(response.data)) {
                    return { data: response.data };
                } else if (response.data.data && Array.isArray(response.data.data)) {
                    return response.data;
                } else {
                    // Versuche, die Daten intelligent zu parsen
                    console.log('Verarbeite Antwortdatentyp:', typeof response.data);
                    
                    // Wenn response.data eine Array-Eigenschaft enthält, verwende diese
                    for (const key in response.data) {
                        if (Array.isArray(response.data[key]) && response.data[key].length > 0) {
                            console.log(`Array-Daten in Eigenschaft "${key}" gefunden`);
                            return { data: response.data[key] };
                        }
                    }
                    
                    // Wenn keine Array-Eigenschaft gefunden, aber response.data ein Objekt ist
                    if (typeof response.data === 'object') {
                        console.log('Antwortdaten sind ein Objekt ohne Arrays, gebe als einzelnes Element-Array zurück');
                        return { data: [response.data] };
                    }
                    
                    return { data: [] };
                }
            }
            
            throw new Error('Keine verwertbaren Daten in der API-Antwort');
        } catch (dbError) {
            console.log(`DB-Endpunkt fehlgeschlagen: ${dbError.message}. Versuche Standard-API...`);
        }
        
        // Standard-API-Endpunkt versuchen
        try {
            console.log(`API-Versuch für ${platform} Daten`);
            const response = await api.get(`/api/recent-data`, { 
                params: { platform, limit },
                timeout: 60000
            });
            
            console.log(`Erfolgreich ${platform}-Daten abgerufen:`, response.status);
            
            // Verarbeite Antwortdaten
            if (response.data) {
                if (Array.isArray(response.data)) {
                    return { data: response.data };
                } else if (response.data.data && Array.isArray(response.data.data)) {
                    return response.data;
                } else {
                    for (const key in response.data) {
                        if (Array.isArray(response.data[key]) && response.data[key].length > 0) {
                            return { data: response.data[key] };
                        }
                    }
                    
                    if (typeof response.data === 'object') {
                        return { data: [response.data] };
                    }
                    
                    return { data: [] };
                }
            }
            
            throw new Error('Keine verwertbaren Daten in der API-Antwort');
        } catch (error) {
            console.error(`Fehler beim Abrufen von ${platform}-Daten:`, error);
            throw new Error(`Fehler beim Abrufen von ${platform}-Daten: ${error.message}`);
        }
    } catch (error) {
        console.error(`Alle Versuche für ${platform}-Daten sind fehlgeschlagen:`, error);
        throw error;
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

// Improved function to fetch topic model data with BERT from PostgreSQL database
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
        
        // Try direct DB endpoint first with explicit timeout
        try {
            console.log("Trying direct DB endpoint at /api/db/topic-model");
            const response = await api.get('/api/db/topic-model', {
                params: {
                    start_date: startDate,
                    end_date: endDate,
                    platforms: platforms.join(','),
                    num_topics: numTopics
                },
                timeout: 60000 // 60 second timeout
            });
            
            console.log("DB Topic model response:", response.data);
            
            // Check if topics is actually an array to avoid rendering issues
            if (response.data && !Array.isArray(response.data.topics)) {
                console.warn("Invalid topics format in DB response:", response.data.topics);
                response.data.topics = [];
            }
            
            return response.data;
        } catch (dbError) {
            console.warn(`DB endpoint failed: ${dbError.message}. Trying alternative endpoints...`);
        }
        
        // Try POST to /api/topic-model
        try {
            console.log("Trying POST method to /api/topic-model");
            const postResponse = await api.post('/api/topic-model', {
                start_date: startDate,
                end_date: endDate,
                platforms: platforms,
                num_topics: numTopics
            }, {
                timeout: 60000 // 60 second timeout
            });
            
            console.log("Topic model POST response:", postResponse.data);
            
            // Check if topics is actually an array to avoid rendering issues
            if (postResponse.data && !Array.isArray(postResponse.data.topics)) {
                console.warn("Invalid topics format in POST response:", postResponse.data.topics);
                postResponse.data.topics = [];
            }
            
            return postResponse.data;
        } catch (postError) {
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
        
        // Try fallback endpoint if both main endpoints fail
        try {
            console.log("Trying fallback endpoint for topic model data...");
            const fallbackResponse = await api.get('/api/db/topics', {
                params: {
                    start_date: startDate,
                    end_date: endDate
                },
                timeout: 60000 // 60 second timeout
            });
            
            console.log("Fallback topic model response:", fallbackResponse.data);
            
            // Check for valid data structure
            if (fallbackResponse.data && !Array.isArray(fallbackResponse.data.topics)) {
                console.warn("Invalid topics format in fallback response:", fallbackResponse.data.topics);
                fallbackResponse.data.topics = [];
            }
            
            return fallbackResponse.data;
        } catch (fallbackError) {
            console.error('Error fetching from fallback endpoint:', fallbackError);
            
            // Return an appropriate error response
            throw new Error("Failed to fetch topic model data from all available endpoints. Please try again later.");
        }
    }
};

/**
 * Verbesserte Funktion zum Abrufen von Modell-Drift-Daten direkt aus der DB
 * 
 * @param {string} modelName - Modellname
 * @param {string} version - Optionale Modellversion
 * @returns {Promise<Object>} - Drift-Metriken
 */
export const fetchModelDrift = async (modelName, version = null) => {
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);
    
    // Versuche zuerst DB-Endpunkt
    try {
      const dbUrl = `/api/db/models/${modelName}/drift${version ? `?version=${version}` : ''}`;
      console.log(`Abrufen von DB-Modell-Drift-Daten von: ${dbUrl}`);
      
      const dbResponse = await api.get(dbUrl, { timeout: 30000 });
      console.log('DB-Modell-Drift-Antwort:', dbResponse.data);
      return dbResponse.data;
    } catch (dbError) {
      console.warn(`DB-Endpunkt für Drift fehlgeschlagen: ${dbError.message}`);
    }
    
    // Versuche ML-Ops API-Endpunkt
    const url = `/api/mlops/models/${modelName}/drift${version ? `?version=${version}` : ''}`;
    console.log(`Abrufen von ML-Ops-Modell-Drift-Daten von: ${url}`);
    
    const response = await api.get(url, { timeout: 30000 });
    console.log('ML-Ops-Modell-Drift-Antwort:', response.data);
    return response.data;
  } catch (error) {
    console.error('Fehler beim Abrufen von Modell-Drift-Daten:', error);
    
    // Versuche alternativen Endpunkt als letzten Ausweg
    try {
      console.log(`Abrufen von Drift-Daten über Fallback-Endpunkt für ${modelName}`);
      const fallbackUrl = `/api/models/${modelName}/drift${version ? `?version=${version}` : ''}`;
      const fallbackResponse = await api.get(fallbackUrl, { timeout: 30000 });
      console.log('Fallback-Drift-Antwort:', fallbackResponse.data);
      return fallbackResponse.data;
    } catch (fallbackError) {
      console.error('Fallback-Endpunkt für Drift-Daten fehlgeschlagen:', fallbackError);
      
      // Leere Daten zurückgeben anstatt Mock-Daten
      return { 
        timestamp: "",
        dataset_drift: false,
        share_of_drifted_columns: 0,
        drifted_columns: [],
        confusionMatrix: null
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

export const fetchPredictions = async (startDate = null, endDate = null) => {
    try {
        // Always reset mock data status at start of request
        setMockDataStatus(false);
        
        // Versuche zuerst, Vorhersagen direkt aus der PostgreSQL-DB zu holen
        console.log("Fetching predictions with params:", { startDate, endDate });
        
        const response = await api.get('/api/db/predictions', {
            params: {
                start_date: startDate,
                end_date: endDate
            },
            timeout: 60000 // 60 second timeout
        });
        
        console.log("Received predictions from DB:", response.data);
        return response.data;
    } catch (error) {
        console.error('Error fetching predictions from DB:', error);
        
        // Versuche alternative Endpunkte, falls der Hauptendpunkt fehlschlägt
        try {
            console.log("Trying alternative endpoint for predictions...");
            const altResponse = await api.get('/api/predictions', {
                params: {
                    start_date: startDate,
                    end_date: endDate
                },
                timeout: 60000 // 60 second timeout
            });
            
            console.log("Alternative predictions response:", altResponse.data);
            return altResponse.data;
        } catch (altError) {
            console.error('Error fetching from alternative endpoint:', altError);
            
            // Last attempt at a more basic endpoint
            try {
                console.log("Trying basic predictions endpoint...");
                const basicResponse = await api.get('/api/predictions/all', {
                    timeout: 60000 // 60 second timeout
                });
                
                console.log("Basic predictions response:", basicResponse.data);
                return basicResponse.data;
            } catch (basicError) {
                console.error('Error fetching from basic endpoint:', basicError);
                
                // Instead of returning empty data, throw an error to be handled by the component
                throw new Error("Failed to fetch prediction data from all available endpoints. Please verify your database connection and try again later.");
            }
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
 * Verbesserte Funktion zum Abrufen von Modellversionen direkt aus der DB
 * 
 * @param {string} modelName - Modellname
 * @returns {Promise<Array>} - Modellversionen
 */
export const fetchModelVersions = async (modelName) => {
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);
    
    // Versuche zuerst DB-Endpunkt
    try {
      console.log(`Abrufen von DB-Modellversionen für: ${modelName}`);
      const dbResponse = await api.get(`/api/db/models/${modelName}/versions`, { timeout: 30000 });
      console.log('DB-Modellversionen-Antwort:', dbResponse.data);
      
      // Stelle sicher, dass wir immer ein Array zurückgeben
      if (Array.isArray(dbResponse.data) && dbResponse.data.length > 0) {
        return dbResponse.data;
      }
      console.warn('Keine gültigen Versionen von DB-Endpunkt erhalten');
    } catch (dbError) {
      console.warn(`DB-Endpunkt für Versionen fehlgeschlagen: ${dbError.message}`);
    }
    
    // Versuche ML-Ops API-Endpunkt
    console.log(`Abrufen von ML-Ops-Modellversionen für: ${modelName}`);
    const response = await api.get(`/api/mlops/models/${modelName}/versions`, { timeout: 30000 });
    console.log('ML-Ops-Modellversionen-Antwort:', response.data);
    
    // Stelle sicher, dass wir immer ein Array zurückgeben
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Fehler beim Abrufen von Modellversionen:', error);
    
    // Versuche alternativen Endpunkt als letzten Ausweg
    try {
      console.log(`Abrufen von Versionen über Fallback-Endpunkt für ${modelName}`);
      const fallbackResponse = await api.get(`/api/models/${modelName}/versions`, { timeout: 30000 });
      console.log('Fallback-Versionen-Antwort:', fallbackResponse.data);
      return Array.isArray(fallbackResponse.data) ? fallbackResponse.data : [];
    } catch (fallbackError) {
      console.error('Fallback-Endpunkt für Versionen fehlgeschlagen:', fallbackError);
      return [];
    }
  }
};

/**
 * Verbesserte Funktion zum Abrufen von Modellmetriken direkt aus der DB
 * 
 * @param {string} modelName - Modellname
 * @param {string} version - Optionale Modellversion
 * @returns {Promise<Object>} - Modellmetriken
 */
export const fetchModelMetrics = async (modelName, version = null) => {
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);

    // Versuche zuerst DB-Endpunkt
    try {
      console.log(`Abrufen von DB-Modellmetriken für ${modelName} ${version ? `(Version: ${version})` : ''}`);
      const dbUrl = `/api/db/models/${modelName}/metrics${version ? `?version=${version}` : ''}`;
      const dbResponse = await api.get(dbUrl, { timeout: 30000 });
      console.log('DB-Modellmetriken-Antwort:', dbResponse.data);
      return dbResponse.data;
    } catch (dbError) {
      console.warn(`DB-Endpunkt für Metriken fehlgeschlagen: ${dbError.message}`);
    }

    // Versuche ML-Ops API-Endpunkt
    const url = `/api/mlops/models/${modelName}/metrics${version ? `?version=${version}` : ''}`;
    console.log(`Abrufen von ML-Ops-Modellmetriken von: ${url}`);
    const response = await api.get(url, { timeout: 30000 });
    console.log('ML-Ops-Modellmetriken-Antwort:', response.data);
    return response.data;
  } catch (error) {
    console.error('Fehler beim Abrufen von Modellmetriken:', error);
    
    // Versuche alternativen Endpunkt als letzten Ausweg
    try {
      console.log(`Abrufen von Metriken über Fallback-Endpunkt für ${modelName}`);
      const fallbackUrl = `/api/models/${modelName}/evaluation`;
      const fallbackResponse = await api.get(fallbackUrl, { timeout: 30000 });
      console.log('Fallback-Metriken-Antwort:', fallbackResponse.data);
      return fallbackResponse.data;
    } catch (fallbackError) {
      console.error('Fallback-Endpunkt für Metriken fehlgeschlagen:', fallbackError);
      return {};
    }
  }
};

// New function to fetch posts related to a specific topic
export const fetchPostsByTopic = async (topicId) => {
    try {
        console.log(`Fetching posts for topic ID: ${topicId}`);
        
        // Always reset mock data status at start of request
        setMockDataStatus(false);
        
        // Try PostgreSQL direct endpoint first 
        try {
            console.log("Trying direct PostgreSQL endpoint");
            const response = await api.get(`/api/db/posts/by-topic/${topicId}`);
            console.log(`Direct DB posts response for topic ${topicId}:`, response.data);
            if (response.data && response.data.length > 0) {
                return response.data;
            }
            console.log("No posts found in direct PostgreSQL response");
        } catch (directDbError) {
            console.warn("Direct PostgreSQL endpoint failed:", directDbError);
        }
        
        // Try alternative DB endpoint
        try {
            console.log("Trying DB topics endpoint");
            const response = await api.get(`/api/db/topics/${topicId}/posts`);
            console.log(`DB posts for topic ${topicId} response:`, response.data);
            if (response.data && response.data.length > 0) {
                return response.data;
            }
            console.log("No posts found in DB endpoint");
        } catch (error) {
            console.error(`Error fetching DB posts for topic ${topicId}:`, error);
        }
        
        // Try basic API endpoint as last resort
        try {
            console.log("Trying basic API endpoint for topic posts");
            const altResponse = await api.get(`/api/topics/${topicId}/posts`);
            console.log("Basic API endpoint response:", altResponse.data);
            return altResponse.data;
        } catch (altError) {
            console.error('Error fetching from basic API endpoint:', altError);
            throw new Error(`Failed to fetch posts for topic ${topicId}. Please try again later.`);
        }
    } catch (error) {
        console.error(`All attempts to fetch posts for topic ${topicId} failed:`, error);
        throw error;
    }
};

export default api; 