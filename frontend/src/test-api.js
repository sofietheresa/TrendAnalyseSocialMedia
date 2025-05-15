/**
 * Test script to check API connectivity
 * This can be run with Node.js to test the API outside of the React app
 */

const axios = require('axios');

// API URL
const API_URL = 'https://trendanalysesocialmedia-production.up.railway.app';

console.log('Testing API connectivity to:', API_URL);

// Test endpoints
const endpoints = [
  '/',
  '/health',
  '/api/scraper-status',
  '/api/daily-stats'
];

async function testEndpoint(endpoint) {
  console.log(`\nTesting ${API_URL}${endpoint}...`);
  try {
    const start = Date.now();
    const response = await axios.get(`${API_URL}${endpoint}`, {
      timeout: 10000
    });
    const duration = Date.now() - start;
    
    console.log(`✅ Success (${duration}ms) - Status: ${response.status}`);
    console.log('Response data:', JSON.stringify(response.data, null, 2).substring(0, 500) + '...');
    return true;
  } catch (error) {
    console.log(`❌ Error - ${error.message}`);
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log('Response data:', error.response.data);
    }
    return false;
  }
}

async function runTests() {
  console.log('=== API CONNECTIVITY TEST ===');
  const results = [];
  
  for (const endpoint of endpoints) {
    const success = await testEndpoint(endpoint);
    results.push({ endpoint, success });
  }
  
  console.log('\n=== TEST RESULTS ===');
  results.forEach(({ endpoint, success }) => {
    console.log(`${endpoint}: ${success ? '✅ PASS' : '❌ FAIL'}`);
  });
  
  const successCount = results.filter(r => r.success).length;
  console.log(`\nSuccess rate: ${successCount}/${results.length} endpoints`);
}

runTests().catch(error => {
  console.error('Test script error:', error);
}); 