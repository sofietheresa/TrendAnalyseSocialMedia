// Test file to verify Railway API endpoints
const axios = require('axios');

const API_URL = 'https://trendanalysesocialmedia-production.up.railway.app';

async function testEndpoints() {
  try {
    console.log('Testing Railway API endpoints at:', API_URL);
    
    // Test scraper status endpoint
    try {
      console.log('Testing /api/scraper-status endpoint...');
      const scraperStatus = await axios.get(`${API_URL}/api/scraper-status`);
      console.log('Scraper status response:', scraperStatus.status, scraperStatus.data);
    } catch (error) {
      console.error('Error testing scraper status endpoint:', error.message);
    }
    
    // Test daily stats endpoint
    try {
      console.log('Testing /api/daily-stats endpoint...');
      const dailyStats = await axios.get(`${API_URL}/api/daily-stats`);
      console.log('Daily stats response:', dailyStats.status, dailyStats.data);
    } catch (error) {
      console.error('Error testing daily stats endpoint:', error.message);
    }
    
    // Test topic model endpoint
    try {
      console.log('Testing /api/topic-model endpoint...');
      const topicModel = await axios.get(`${API_URL}/api/topic-model`);
      console.log('Topic model response:', topicModel.status, 'Data received:', !!topicModel.data);
    } catch (error) {
      console.error('Error testing topic model endpoint:', error.message);
    }
    
    // Test different predictions endpoints
    const predictionEndpoints = [
      '/api/predictions',
      '/api/predictions/all',
      '/api/topic-predictions',
      '/api/topic-model/predictions',
      '/api/forecast'
    ];
    
    for (const endpoint of predictionEndpoints) {
      try {
        console.log(`Testing ${endpoint} endpoint...`);
        const response = await axios.get(`${API_URL}${endpoint}`);
        console.log(`${endpoint} response:`, response.status, 'Data received:', !!response.data);
        console.log('Sample data:', JSON.stringify(response.data).substring(0, 200) + '...');
      } catch (error) {
        console.error(`Error testing ${endpoint} endpoint:`, error.message);
      }
    }
    
    // Test models endpoint for model versions
    try {
      console.log('Testing /api/mlops/models/topic_prediction/versions endpoint...');
      const modelVersions = await axios.get(`${API_URL}/api/mlops/models/topic_prediction/versions`);
      console.log('Model versions response:', modelVersions.status, 'Data received:', !!modelVersions.data);
      console.log('Sample model versions:', JSON.stringify(modelVersions.data).substring(0, 200) + '...');
    } catch (error) {
      console.error('Error testing model versions endpoint:', error.message);
    }
    
  } catch (error) {
    console.error('Error during API endpoint testing:', error);
  }
}

testEndpoints(); 