// Test-Script für direkte Railway API-Endpunkte (nur funktionierende Endpunkte)
const axios = require('axios');

const API_URL = 'https://trendanalysesocialmedia-production.up.railway.app';

/**
 * Funktion zum Testen der Railway API-Endpunkte
 */
async function testRailwayEndpoints() {
  console.log('\n=== TRENDANALYSE SOCIAL MEDIA RAILWAY API TEST ===');
  console.log(`Testing Railway API endpoints at: ${API_URL}`);
  console.log('=================================================\n');
  
  try {
    // 1. Health-Check
    try {
      console.log('Testing /health endpoint...');
      const healthResponse = await axios.get(`${API_URL}/health`);
      console.log('Health status:', healthResponse.status, healthResponse.data);
      console.log('Database connection:', healthResponse.data.components?.database || 'unknown');
    } catch (error) {
      console.error('ERROR: Health check failed', error.message);
    }
    
    // 2. Scraper Status
    try {
      console.log('\nTesting /api/scraper-status endpoint...');
      const scraperStatus = await axios.get(`${API_URL}/api/scraper-status`);
      console.log('Scraper status:', scraperStatus.status);
      console.log('Scraper data:', scraperStatus.data);
    } catch (error) {
      console.error('ERROR: Scraper status endpoint failed', error.message);
    }
    
    // 3. Daily Stats
    try {
      console.log('\nTesting /api/daily-stats endpoint...');
      const dailyStats = await axios.get(`${API_URL}/api/daily-stats`);
      console.log('Daily stats status:', dailyStats.status);
      console.log('Daily stats data:', dailyStats.data);
    } catch (error) {
      console.error('ERROR: Daily stats endpoint failed', error.message);
    }
    
    // 4. Topic Model - Funktionierender Endpunkt
    try {
      console.log('\nTesting /api/topic-model endpoint...');
      const topicModelResponse = await axios.get(`${API_URL}/api/topic-model`);
      console.log('Topic model status:', topicModelResponse.status);
      console.log('Topics received:', topicModelResponse.data.topics?.length || 0);
      if (topicModelResponse.data.topics?.length > 0) {
        console.log('Sample topic:', JSON.stringify(topicModelResponse.data.topics[0]).substring(0, 200) + '...');
      }
    } catch (error) {
      console.error('ERROR: Topic model endpoint failed', error.message);
    }
    
    // 5. DB Predictions - Funktionierender Endpunkt
    try {
      console.log('\nTesting /api/db/predictions endpoint...');
      const predictionsResponse = await axios.get(`${API_URL}/api/db/predictions`);
      console.log('Predictions status:', predictionsResponse.status);
      console.log('Data received:', !!predictionsResponse.data);
      console.log('Is real data:', predictionsResponse.data?.is_real_data || 'unknown');
      console.log('Sample data:', JSON.stringify(predictionsResponse.data).substring(0, 200) + '...');
    } catch (error) {
      console.error('ERROR: Predictions endpoint failed', error.message);
    }
    
    // 6. MLOps Models Versions - Funktionierender Endpunkt
    try {
      console.log('\nTesting /api/mlops/models/topic_prediction/versions endpoint...');
      const versionsResponse = await axios.get(`${API_URL}/api/mlops/models/topic_prediction/versions`);
      console.log('Versions status:', versionsResponse.status);
      console.log('Versions count:', versionsResponse.data.length);
      if (versionsResponse.data.length > 0) {
        console.log('Sample version:', JSON.stringify(versionsResponse.data[0]));
      }
    } catch (error) {
      console.error('ERROR: MLOps model versions endpoint failed', error.message);
    }
    
    // 7. MLOps Models Metrics - Angenommen funktionierend
    try {
      console.log('\nTesting /api/mlops/models/topic_prediction/metrics endpoint...');
      const metricsResponse = await axios.get(`${API_URL}/api/mlops/models/topic_prediction/metrics`);
      console.log('Metrics status:', metricsResponse.status);
      console.log('Data received:', !!metricsResponse.data);
      console.log('Sample metrics:', JSON.stringify(metricsResponse.data).substring(0, 200) + '...');
    } catch (error) {
      console.error('ERROR: MLOps model metrics endpoint failed', error.message);
    }
    
    // 8. MLOps Models Drift - Angenommen funktionierend
    try {
      console.log('\nTesting /api/mlops/models/topic_prediction/drift endpoint...');
      const driftResponse = await axios.get(`${API_URL}/api/mlops/models/topic_prediction/drift`);
      console.log('Drift status:', driftResponse.status);
      console.log('Data received:', !!driftResponse.data);
      console.log('Sample drift data:', JSON.stringify(driftResponse.data).substring(0, 200) + '...');
    } catch (error) {
      console.error('ERROR: MLOps model drift endpoint failed', error.message);
    }
    
    console.log('\n=== RAILWAY API TEST COMPLETE ===');
    
  } catch (error) {
    console.error('\nERROR during API endpoint testing:', error);
  }
}

// Führe den Test aus
testRailwayEndpoints(); 