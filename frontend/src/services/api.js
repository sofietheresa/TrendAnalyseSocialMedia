import axios from 'axios';

// API URL configuration - using a unified API that includes both main and drift API functionality
const API_URL = process.env.REACT_APP_API_URL || 
                'http://localhost:8002';

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
export const useMockApi = false; // Set to false to use real API endpoints

console.log('Using mock API:', useMockApi);

// Create a global state for tracking mock data usage
export let usingMockData = useMockApi; // Initialize with our config value

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
    // If we're configured to use mock data, skip real API call attempts
    if (useMockApi) {
        setMockDataStatus(true);
        throw new Error('Using mock data by configuration');
    }

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
        // Check if we should use mock data by configuration
        if (useMockApi) {
            console.log(`Using mock data for ${platform} by configuration`);
            setMockDataStatus(true);
            
            // Import and return mock data directly
            const { getMockData } = await import('../mock-api/data');
            const mockData = getMockData(platform, limit);
            
            return {
                data: mockData,
                isMockData: true,
                message: `Using mock data for ${platform} (configured to use mock data)`
            };
        }
        
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
        // Check if we should use mock data by configuration
        if (useMockApi) {
            console.log(`Using mock topic model data by configuration`);
            setMockDataStatus(true);
            
            // Generate mock topic data
            const mockTopicData = generateMockTopicData(numTopics, startDate, endDate);
            
            return mockTopicData;
        }
        
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
        
        // Generate mock topic data as fallback
        const mockTopicData = generateMockTopicData(numTopics, startDate, endDate);
        return mockTopicData;
    }
};

/**
 * Generates mock topic model data for testing and development
 * @param {number} numTopics - Number of topics to generate
 * @param {string} startDate - Start date for time range (ISO format)
 * @param {string} endDate - End date for time range (ISO format)
 * @returns {Object} Mock topic model data
 */
const generateMockTopicData = (numTopics = 5, startDate = null, endDate = null) => {
    // Use provided dates or generate defaults
    const actualStartDate = startDate || new Date(Date.now() - 3*24*60*60*1000).toISOString().split('T')[0];
    const actualEndDate = endDate || new Date().toISOString().split('T')[0];
    
    // Convert dates to Date objects for calculations
    const startDateObj = new Date(actualStartDate);
    const endDateObj = new Date(actualEndDate);
    
    // Calculate number of days in the range
    const diffTime = Math.abs(endDateObj - startDateObj);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    
    // Generate date array for the range
    const dateArray = [];
    for (let i = 0; i < diffDays; i++) {
        const date = new Date(startDateObj);
        date.setDate(date.getDate() + i);
        dateArray.push(date.toISOString().split('T')[0]);
    }
    
    // Generate realistic topic names
    const mockTopicNames = [
        "Nachhaltigkeit & Umweltschutz",
        "Wirtschaftliche Entwicklung",
        "Digitale Transformation",
        "Politische Diskussionen",
        "Künstliche Intelligenz",
        "Gesundheit & Wohlbefinden",
        "Technologische Innovation",
        "Work-Life-Balance",
        "Energiewende & Klimaschutz",
        "Gesellschaftlicher Wandel"
    ];
    
    // Generate mock topics
    const mockTopics = [];
    
    // Add "Other" topic as ID -1
    mockTopics.push({
        id: -1,
        name: "Other",
        keywords: ["miscellaneous", "various", "other", "misc", "etc"],
        weight: 0.05,
        coherence_score: 0.35
    });
    
    // Add regular topics
    for (let i = 0; i < Math.min(numTopics, mockTopicNames.length); i++) {
        mockTopics.push({
            id: i,
            name: mockTopicNames[i],
            keywords: generateMockKeywords(mockTopicNames[i]),
            weight: (0.95 - (i * 0.1)).toFixed(2),
            coherence_score: (0.9 - (i * 0.05)).toFixed(2)
        });
    }
    
    // Generate mock topic counts by date
    const mockTopicCountsByDate = {};
    
    // For each topic (except "Other")
    for (let i = 0; i < mockTopics.length; i++) {
        if (mockTopics[i].id === -1) continue;
        
        const topicId = mockTopics[i].id;
        mockTopicCountsByDate[topicId] = {};
        
        // Generate random counts for each date with some trend pattern
        // Topics earlier in the list get higher numbers to show as "trending"
        const baseCount = 50 - (i * 5);
        
        dateArray.forEach(date => {
            // Generate random count with trend pattern
            const dayOfMonth = new Date(date).getDate();
            const trendFactor = Math.sin(dayOfMonth / 5) + 1; // Creates a wave pattern
            const randomVariation = Math.random() * 15;
            
            // Ensure count is positive
            const count = Math.max(5, Math.floor((baseCount + randomVariation) * trendFactor));
            
            mockTopicCountsByDate[topicId][date] = count;
        });
    }
    
    return {
        topics: mockTopics,
        topic_counts_by_date: mockTopicCountsByDate,
        metrics: {
            coherence_score: 0.78,
            diversity_score: 0.65,
            document_coverage: 0.92,
            total_documents: 15764
        },
        time_range: {
            start_date: actualStartDate,
            end_date: actualEndDate
        },
        isMockData: true
    };
};

// Funktion zur Generierung von realistischen Keywords für ein Thema
const generateMockKeywords = (topicName) => {
    // Vordefinierte Keywords für bestimmte Themen
    const keywordsByTopic = {
        "Nachhaltigkeit & Umweltschutz": ["umweltschutz", "nachhaltigkeit", "klimaschutz", "recycling", "umweltbewusstsein", "ressourcenschonung", "ökologisch"],
        "Wirtschaftliche Entwicklung": ["wirtschaftswachstum", "konjunktur", "finanzmärkte", "inflation", "wirtschaftspolitik", "arbeitsmarkt", "investitionen"],
        "Digitale Transformation": ["digitalisierung", "digital", "transformation", "industrie4.0", "automatisierung", "prozessoptimierung", "digitale-strategie"],
        "Politische Diskussionen": ["politik", "demokratie", "wahlen", "parteien", "gesetzgebung", "bundestag", "diskurs", "politische-debatte"],
        "Künstliche Intelligenz": ["ki", "ai", "maschinelles-lernen", "deep-learning", "neuronale-netze", "chatgpt", "algorithmik", "chatbots"],
        "Gesundheit & Wohlbefinden": ["gesundheit", "wohlbefinden", "prävention", "fitness", "ernährung", "mental-health", "gesundheitsvorsorge"],
        "Technologische Innovation": ["innovation", "technologie", "forschung", "entwicklung", "hightech", "zukunftstechnologien", "tech-trends"],
        "Work-Life-Balance": ["work-life-balance", "homeoffice", "remote-arbeit", "arbeitszeitmodelle", "freizeit", "vereinbarkeit", "lebensqualität"],
        "Energiewende & Klimaschutz": ["energiewende", "erneuerbare-energien", "klimaneutralität", "co2-reduktion", "klimaschutz", "solarenergie", "windkraft"],
        "Gesellschaftlicher Wandel": ["gesellschaftswandel", "demografie", "wertewandel", "diversität", "inklusion", "integration", "sozialer-wandel"]
    };
    
    // Wenn vorhandene Keywords für das Thema existieren, diese verwenden
    if (keywordsByTopic[topicName]) {
        return keywordsByTopic[topicName];
    }
    
    // Generische Keywords für nicht definierte Themen
    const words = topicName.toLowerCase().split(/\s+|&/);
    const baseKeywords = words.filter(w => w.length > 3);
    
    // Zusätzliche generische Keywords hinzufügen
    const genericKeywords = ["diskussion", "trend", "entwicklung", "thema", "debatte"];
    
    // Kombinationen erstellen
    const combinedKeywords = [];
    for (let i = 0; i < Math.min(baseKeywords.length, 2); i++) {
        for (let j = i + 1; j < baseKeywords.length; j++) {
            combinedKeywords.push(`${baseKeywords[i]}-${baseKeywords[j]}`);
        }
    }
    
    // Ergebnisarray aus Basis, Kombinationen und Generika erstellen
    const result = [...baseKeywords];
    
    // Füge einige (nicht alle) kombinierte Keywords hinzu
    if (combinedKeywords.length > 0) {
        result.push(...combinedKeywords.slice(0, Math.min(3, combinedKeywords.length)));
    }
    
    // Füge einige generische Keywords hinzu
    result.push(...genericKeywords.slice(0, 3));
    
    // Begrenze die Gesamtanzahl der Keywords
    return result.slice(0, 7);
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
    // Return error object with empty data
    return { 
      error: `Failed to execute pipeline: ${error.message}`,
      execution_id: "", 
      pipeline_id: pipelineId,
      status: "failed",
      startTime: "",
      message: ""
    };
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

export default api; 