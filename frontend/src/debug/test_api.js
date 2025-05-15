// A simple script to test the API endpoints directly
const fetch = require('node-fetch');

const API_URL = 'http://localhost:8000';

async function testAPIEndpoints() {
  console.log('Testing API endpoints...');
  
  try {
    // Test health endpoint
    console.log('\nTesting /health endpoint:');
    const healthResponse = await fetch(`${API_URL}/health`);
    console.log('Status:', healthResponse.status);
    console.log('Response:', await healthResponse.json());
    
    // Test debug routes endpoint
    console.log('\nTesting /debug/routes endpoint:');
    const routesResponse = await fetch(`${API_URL}/debug/routes`);
    console.log('Status:', routesResponse.status);
    const routes = await routesResponse.json();
    
    // Filter for mlops routes
    const mlopsRoutes = routes.routes.filter(route => route.path.includes('mlops'));
    console.log('MLOPS Routes:', mlopsRoutes);
    
    // Test all pipelines endpoint
    console.log('\nTesting /api/mlops/pipelines endpoint:');
    const pipelinesResponse = await fetch(`${API_URL}/api/mlops/pipelines`);
    console.log('Status:', pipelinesResponse.status);
    console.log('Response:', await pipelinesResponse.json());
    
    // Test trend_analysis pipeline endpoint
    console.log('\nTesting /api/mlops/pipelines/trend_analysis endpoint:');
    const pipelineResponse = await fetch(`${API_URL}/api/mlops/pipelines/trend_analysis`);
    console.log('Status:', pipelineResponse.status);
    console.log('Response:', await pipelineResponse.json());
    
    // Test executions endpoint
    console.log('\nTesting /api/mlops/pipelines/trend_analysis/executions endpoint:');
    const executionsResponse = await fetch(`${API_URL}/api/mlops/pipelines/trend_analysis/executions`);
    console.log('Status:', executionsResponse.status);
    console.log('Response:', await executionsResponse.json());
    
  } catch (error) {
    console.error('Error testing API endpoints:', error);
  }
}

testAPIEndpoints().then(() => console.log('API testing complete')); 