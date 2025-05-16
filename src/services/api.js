import axios from 'axios';

// API URL configuration - using a unified API that includes both main and drift API functionality
const API_URL = process.env.REACT_APP_API_URL || 
                'http://localhost:3001';  // Changed to use the mock server

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
export const useMockApi = true; // Changed to true to use mock API

console.log('Using mock API:', useMockApi);

// Create a global state for tracking mock data usage
export let usingMockData = true; // Initialize with true to force mock data

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
    setMockDataStatus(true);
    
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