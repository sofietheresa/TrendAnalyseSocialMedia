import axios from "axios";

// API URL configuration - directly setting Railway API URL to ensure consistent data source
const API_URL = "https://trendanalysesocialmedia-production.up.railway.app"; // Railway API server
// Always enable DB endpoints to ensure real data
const ENABLE_DB_ENDPOINTS = true;

console.log("API_URL set to:", API_URL);
console.log("Using DB endpoints:", ENABLE_DB_ENDPOINTS ? "Yes" : "No");

// Improved Axios configuration
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache", // Prevents caching of responses
  },
  // Longer timeout for potentially slow connections
  timeout: 60000, // Increased timeout to handle Railway API delays
  // Disable CORS credentials since we're using direct API
  withCredentials: false,
});

// IMPORTANT: Always set to false to ensure we use real data
export const useMockApi = false;

console.log("Using real API from Railway");

// Create a global state for tracking mock data usage - Always false
export let usingMockData = false;

// Function to check and set mock data usage state - Always sets to false
export const setMockDataStatus = (isMockData) => {
  // Always false - we always want real data
  usingMockData = false;

  // Dispatch an event so components can react
  window.dispatchEvent(
    new CustomEvent("mockdatachange", {
      detail: { usingMockData: false },
    }),
  );
};

// Get the current mock data status - Always returns false
export const getMockDataStatus = () => false;

// Improved retry/connection logic
const MAX_RETRIES = 3;
const RETRY_DELAY = 2000; // 2 seconds between retries for Railway API

// Helper function for API calls with better retry logic - No fallback to mock
const apiCall = async (
  endpoint,
  method = "get",
  data = null,
  options = {},
  retries = MAX_RETRIES,
) => {
  try {
    const config = {
      ...options,
      method,
      url: endpoint,
      data: method !== "get" ? data : undefined,
      params: method === "get" ? data : undefined,
    };

    const response = await api(config);
    return response.data;
  } catch (error) {
    console.error(`Failed API call to ${endpoint}:`, error);

    if (retries > 0) {
      console.log(
        `Retrying API call to ${endpoint}, ${retries} attempts left...`,
      );
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      return apiCall(endpoint, method, data, options, retries - 1);
    }

    // Always throw errors - never return empty data or fallback to mock
    throw new Error(
      `API Error: Failed to fetch data from ${endpoint}. ${error.message || "Please try again later."}`,
    );
  }
};

// API-Funktionen mit verbessertem Error-Handling
export const fetchScraperStatus = async () => {
  console.log("Fetching scraper status...");
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);
    
    const response = await apiCall("/api/scraper-status");
    console.log("Scraper status raw response:", response);

    if (!response) {
      throw new Error("No scraper status data received from server");
    }

    // If the API returns "running" as a string "true", convert it to a boolean
    Object.keys(response).forEach((platform) => {
      if (response[platform] && response[platform].running === "true") {
        response[platform].running = true;
      }
    });

    return response;
  } catch (error) {
    console.error("Error fetching scraper status:", error);
    throw error; // Always throw error instead of returning empty data
  }
};

export const fetchDailyStats = async () => {
  console.log("Fetching daily stats...");
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);
    
    return await apiCall("/api/daily-stats");
  } catch (error) {
    console.error("Error fetching daily stats:", error);
    throw error;
  }
};

// Verbesserte Funktion zum Abrufen aktueller Social-Media-Daten aus der DB
export const fetchRecentData = async (platform = "all", limit = 10) => {
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
          platform: platform !== "all" ? platform : undefined,
          limit,
        },
        timeout: 60000,
      });

      console.log(
        `Erfolgreich ${platform}-Daten aus DB abgerufen:`,
        response.status,
      );

      // Verarbeite die Antwortdaten
      if (response.data) {
        if (Array.isArray(response.data)) {
          return { data: response.data };
        } else if (response.data.data && Array.isArray(response.data.data)) {
          return response.data;
        } else {
          // Versuche, die Daten intelligent zu parsen
          console.log("Verarbeite Antwortdatentyp:", typeof response.data);

          // Wenn response.data eine Array-Eigenschaft enthält, verwende diese
          for (const key in response.data) {
            if (
              Array.isArray(response.data[key]) &&
              response.data[key].length > 0
            ) {
              console.log(`Array-Daten in Eigenschaft "${key}" gefunden`);
              return { data: response.data[key] };
            }
          }

          // Wenn keine Array-Eigenschaft gefunden, aber response.data ein Objekt ist
          if (typeof response.data === "object") {
            console.log(
              "Antwortdaten sind ein Objekt ohne Arrays, gebe als einzelnes Element-Array zurück",
            );
            return { data: [response.data] };
          }

          return { data: [] };
        }
      }

      throw new Error("Keine verwertbaren Daten in der API-Antwort");
    } catch (dbError) {
      console.log(
        `DB-Endpunkt fehlgeschlagen: ${dbError.message}. Versuche Standard-API...`,
      );
    }

    // Standard-API-Endpunkt versuchen
    try {
      console.log(`API-Versuch für ${platform} Daten`);
      const response = await api.get(`/api/recent-data`, {
        params: { platform, limit },
        timeout: 60000,
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
            if (
              Array.isArray(response.data[key]) &&
              response.data[key].length > 0
            ) {
              return { data: response.data[key] };
            }
          }

          if (typeof response.data === "object") {
            return { data: [response.data] };
          }

          return { data: [] };
        }
      }

      throw new Error("Keine verwertbaren Daten in der API-Antwort");
    } catch (error) {
      console.error(`Fehler beim Abrufen von ${platform}-Daten:`, error);
      throw new Error(
        `Fehler beim Abrufen von ${platform}-Daten: ${error.message}`,
      );
    }
  } catch (error) {
    console.error(
      `Alle Versuche für ${platform}-Daten sind fehlgeschlagen:`,
      error,
    );
    throw error;
  }
};

// Other API functions using the enhanced apiCall helper
export const fetchSocialMediaData = async () => {
  try {
    return await apiCall("/data");
  } catch (error) {
    console.error("Error fetching social media data:", error);
    throw error;
  }
};

export const fetchTrendAnalysis = async (platform = null) => {
  try {
    const params = platform ? { platform } : {};
    const response = await api.get("/trends", { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching trend analysis:", error);
    throw error;
  }
};

export const searchContent = async (query, platform = null) => {
  try {
    const params = { query, ...(platform && { platform }) };
    const response = await api.get("/search", { params });
    return response.data;
  } catch (error) {
    console.error("Error searching content:", error);
    throw error;
  }
};

export const fetchTopics = async (startDate, endDate) => {
  try {
    const response = await api.get("/api/db/topics", {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching topics:", error);
    if (error.response) {
      throw new Error(
        `Serverfehler: ${error.response.data.detail || "Unbekannter Fehler"}`,
      );
    } else if (error.request) {
      throw new Error("Keine Verbindung zum Server möglich");
    } else {
      throw new Error("Fehler beim Laden der Daten");
    }
  }
};

// Improved function to fetch topic model data with BERT via Railway API
export const fetchTopicModel = async (
  startDate = null,
  endDate = null,
  platforms = ["reddit", "tiktok", "youtube"],
  numTopics = 5,
) => {
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);

    console.log("Fetching topic model data from Railway API with params:", {
      start_date: startDate,
      end_date: endDate,
      platforms,
      num_topics: numTopics,
    });

    // First try the direct topic-model endpoint
    try {
      // Der Standard-Endpunkt für das Topic-Modell funktioniert laut Tests
      console.log("Accessing Railway topic-model endpoint");
      const response = await api.get("/api/topic-model", {
        params: {
          start_date: startDate,
          end_date: endDate,
          platforms: platforms.join(","),
          num_topics: numTopics,
        },
        timeout: 60000, // 60 second timeout
      });

      console.log("Railway API Topic model response:", response.data);

      // Check if topics is actually an array to avoid rendering issues
      if (response.data && Array.isArray(response.data.topics) && response.data.topics.length > 0) {
        return response.data;
      } else {
        console.warn(
          "Invalid or empty topics format in Railway API response:",
          response.data.topics,
        );
        throw new Error("Invalid or empty topic format returned from Railway API");
      }
    } catch (frontendApiError) {
      console.warn("Frontend API call failed, trying backend API:", frontendApiError);
      
      // Try fetching from backend API as fallback
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
      console.log(`Trying backend API at ${backendUrl}/api/topic-model`);
      
      const backendResponse = await axios.get(`${backendUrl}/api/topic-model`, {
        params: {
          start_date: startDate,
          end_date: endDate,
          platforms: platforms.join(","),
          num_topics: numTopics,
        },
        timeout: 60000,
      });
      
      console.log("Backend API response:", backendResponse.data);
      
      // Check if topics is actually an array to avoid rendering issues
      if (backendResponse.data && Array.isArray(backendResponse.data.topics) && backendResponse.data.topics.length > 0) {
        // Add a flag indicating this came from the backend API
        backendResponse.data.source = "backend_api";
        return backendResponse.data;
      } else {
        console.warn(
          "Invalid or empty topics format in backend API response",
          backendResponse.data
        );
        throw new Error("Invalid or empty topic format returned from both APIs");
      }
    }
  } catch (error) {
    console.error("Error fetching topic model data from all available APIs:", error);
    throw error;
  }
};

/**
 * Funktion zum Abrufen von Modellmetriken von der Railway API
 *
 * @param {string} modelName - Modellname
 * @param {string} version - Optionale Modellversion
 * @returns {Promise<Object>} - Modellmetriken
 */
export const fetchModelMetrics = async (modelName, version = null) => {
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);

    console.log(
      `Abrufen von Modellmetriken für ${modelName} ${version ? `(Version: ${version})` : ""} von Railway API`
    );
    
    // Der MLOps-Endpunkt für Metriken sollte verwendet werden
    const mlopsUrl = `/api/mlops/models/${modelName}/metrics${version ? `?version=${version}` : ""}`;
    console.log(`Rufe Railway API-Endpoint auf: ${mlopsUrl}`);
    
    const dbResponse = await api.get(mlopsUrl, { timeout: 60000 });
    console.log("Railway API Modellmetriken-Antwort:", dbResponse.data);

    if (
      !dbResponse.data ||
      typeof dbResponse.data !== "object" ||
      Object.keys(dbResponse.data).length === 0
    ) {
      throw new Error("Invalid or empty metrics data from Railway API");
    }

    return dbResponse.data;
  } catch (error) {
    console.error("Fehler beim Abrufen von Modellmetriken von Railway API:", error);
    throw error;
  }
};

/**
 * Funktion zum Abrufen von Modell-Drift-Daten von der Railway API
 *
 * @param {string} modelName - Modellname
 * @param {string} version - Optionale Modellversion
 * @returns {Promise<Object>} - Drift-Metriken
 */
export const fetchModelDrift = async (modelName, version = null) => {
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);

    // Der MLOps-Endpunkt für Drift-Daten sollte verwendet werden
    const mlopsUrl = `/api/mlops/models/${modelName}/drift${version ? `?version=${version}` : ""}`;
    console.log(`Abrufen von Modell-Drift-Daten von Railway API: ${mlopsUrl}`);

    const dbResponse = await api.get(mlopsUrl, { timeout: 60000 });
    console.log("Railway API Modell-Drift-Antwort:", dbResponse.data);

    if (
      !dbResponse.data ||
      typeof dbResponse.data !== "object" ||
      Object.keys(dbResponse.data).length === 0
    ) {
      throw new Error("Invalid or empty drift data from Railway API");
    }

    return dbResponse.data;
  } catch (error) {
    console.error("Fehler beim Abrufen von Modell-Drift-Daten von Railway API:", error);
    throw error;
  }
};

export const fetchSourceStats = async () => {
  try {
    const response = await api.get("/api/db/sources/stats");
    return response.data;
  } catch (error) {
    console.error("Error fetching source statistics:", error);
    if (error.response) {
      throw new Error(
        `Serverfehler: ${error.response.data.detail || "Unbekannter Fehler"}`,
      );
    } else if (error.request) {
      throw new Error("Keine Verbindung zum Server möglich");
    } else {
      throw new Error("Fehler beim Laden der Quellenstatistiken");
    }
  }
};

export const fetchLogs = async (source = "all") => {
  try {
    let logs = [];
    if (source === "all" || source === "tiktok") {
      const tiktokResponse = await api.get("/logs/tiktok.log");
      logs = [...logs, ...parseLogs(tiktokResponse.data, "TikTok")];
    }
    if (source === "all" || source === "reddit") {
      const redditResponse = await api.get("/logs/reddit.log");
      logs = [...logs, ...parseLogs(redditResponse.data, "Reddit")];
    }
    if (source === "all" || source === "youtube") {
      const youtubeResponse = await api.get("/logs/youtube.log");
      logs = [...logs, ...parseLogs(youtubeResponse.data, "YouTube")];
    }

    // Sortiere Logs nach Zeitstempel
    return logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  } catch (error) {
    console.error("Error fetching logs:", error);
    if (error.response) {
      throw new Error(
        `Serverfehler: ${error.response.data.detail || "Unbekannter Fehler"}`,
      );
    } else if (error.request) {
      throw new Error("Keine Verbindung zum Server möglich");
    } else {
      throw new Error("Fehler beim Laden der Logs");
    }
  }
};

const parseLogs = (logText, source) => {
  return logText
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      const [timestamp, level, ...messageParts] = line.split(" ");
      return {
        timestamp,
        level: level.replace("[", "").replace("]", ""),
        message: messageParts.join(" "),
        source,
      };
    });
};

export const fetchPresentation = async () => {
  try {
    const response = await api.get("/docs/SocialMediaTA_draft.pptx", {
      responseType: "blob",
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching presentation:", error);
    if (error.response) {
      throw new Error(
        `Serverfehler: ${error.response.data.detail || "Unbekannter Fehler"}`,
      );
    } else if (error.request) {
      throw new Error("Keine Verbindung zum Server möglich");
    } else {
      throw new Error("Fehler beim Laden der Präsentation");
    }
  }
};

export const fetchAnalysisData = async () => {
  try {
    const response = await api.get("/api/db/analysis");
    return response.data;
  } catch (error) {
    console.error("Error fetching analysis data:", error);
    if (error.response) {
      throw new Error(
        `Serverfehler: ${error.response.data.detail || "Unbekannter Fehler"}`,
      );
    } else if (error.request) {
      throw new Error("Keine Verbindung zum Server möglich");
    } else {
      throw new Error("Fehler beim Laden der Analysedaten");
    }
  }
};

export const fetchPredictions = async (startDate = null, endDate = null) => {
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);
    
    console.log("Fetching predictions with params:", { startDate, endDate });
    
    // Railway API prediction endpoint hat funktioniert
    const response = await api.get("/api/db/predictions", {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
      timeout: 60000, // 60 second timeout
    });

    console.log("Received predictions from Railway API:", response.data);
    
    if (!response.data || (typeof response.data === 'object' && Object.keys(response.data).length === 0)) {
      throw new Error("No prediction data returned from Railway API");
    }
    
    return response.data;
  } catch (error) {
    console.error("Error fetching predictions from Railway API:", error);
    throw error;
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
      : "/api/mlops/pipelines";

    console.log(`Fetching pipelines from: ${url}`);

    const response = await api.get(url);
    console.log("Pipeline response:", response.data);

    // Validate response data
    if (
      !response.data ||
      (pipelineId && Object.keys(response.data).length === 0)
    ) {
      throw new Error(
        `No pipeline data available for ${pipelineId || "any pipelines"}`,
      );
    }

    return response.data;
  } catch (error) {
    console.error("Error fetching pipeline data:", error);
    throw new Error(`Failed to fetch pipeline data: ${error.message}`);
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

    // Use the unified API with a longer timeout
    const response = await api.get(url, {
      timeout: 45000, // 45 seconds timeout for potentially slow responses
    });
    console.log("Pipeline executions response:", response.data);

    // Ensure the response is an array before returning
    if (!response.data || !Array.isArray(response.data)) {
      throw new Error(
        `Invalid response format for pipeline executions: expected array`
      );
    }

    return response.data;
  } catch (error) {
    console.error("Error fetching pipeline executions:", error);
    throw new Error(`Failed to fetch pipeline executions: ${error.message}`);
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
    console.log("Pipeline execution response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error executing pipeline:", error);
    throw new Error(`Failed to execute pipeline: ${error.message}`);
  }
};

/**
 * Funktion zum Abrufen von Modellversionen von der Railway API
 *
 * @param {string} modelName - Modellname
 * @returns {Promise<Array>} - Modellversionen
 */
export const fetchModelVersions = async (modelName) => {
  try {
    // Always reset mock data status at start of request
    setMockDataStatus(false);

    console.log(`Abrufen von Modellversionen für ${modelName} von Railway API`);
    
    // Der MLOps-Endpunkt funktioniert laut Test, nicht der DB-Endpunkt
    const endpoint = `/api/mlops/models/${modelName}/versions`;
    console.log(`Verwende Railway API-Endpunkt: ${endpoint}`);
    
    const response = await api.get(endpoint, { timeout: 60000 });
    console.log("Railway API Modellversionen-Antwort:", response.data);

    // Stelle sicher, dass wir immer ein Array zurückgeben
    if (!Array.isArray(response.data)) {
      console.error("Railway API returned non-array data for model versions:", response.data);
      throw new Error(`No valid model versions available for ${modelName} from Railway API`);
    }

    if (response.data.length === 0) {
      console.warn(`No model versions found for ${modelName} in Railway API`);
    }

    return response.data;
  } catch (error) {
    console.error("Fehler beim Abrufen von Modellversionen von Railway API:", error);
    throw error;
  }
};

// Function to fetch posts related to a specific topic from Railway API
export const fetchPostsByTopic = async (topicId) => {
  try {
    console.log(`Fetching posts for topic ID: ${topicId} from Railway API`);

    // Always reset mock data status at start of request
    setMockDataStatus(false);

    // Direkter Zugriff auf Railway API Endpoint
    const endpoint = `/api/db/posts/by-topic/${topicId}`;
    console.log(`Accessing Railway API endpoint: ${endpoint}`);
    
    const response = await api.get(endpoint, { timeout: 60000 });
    console.log(`Railway API posts response for topic ${topicId}:`, response.data);
    
    if (!response.data || !Array.isArray(response.data) || response.data.length === 0) {
      console.warn(`No posts found for topic ${topicId} in Railway API`);
      return []; // Return empty array instead of throwing error to handle no-data case gracefully
    }
    
    return response.data;
  } catch (error) {
    console.error(`Error fetching posts for topic ${topicId} from Railway API:`, error);
    throw error; // Immer Fehler werfen statt Fallback auf Mock-Daten
  }
};

export default api;
