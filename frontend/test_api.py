import requests
import json

def test_endpoint(url):
    print(f"Testing: {url}")
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print("Error response:", response.text)
    except Exception as e:
        print(f"Error: {str(e)}")
    print("-" * 50)

# Test various endpoints
base_url = "http://localhost:5000"

# Test pipeline endpoints
test_endpoint(f"{base_url}/api/mlops/pipelines")
test_endpoint(f"{base_url}/api/mlops/pipelines/topic-modeling-pipeline")
test_endpoint(f"{base_url}/api/mlops/pipelines/topic-modeling-pipeline/executions")

# Test model endpoints
test_endpoint(f"{base_url}/api/mlops/models")
test_endpoint(f"{base_url}/api/mlops/models/topic-model/versions")
test_endpoint(f"{base_url}/api/mlops/models/sentiment-model/metrics")
test_endpoint(f"{base_url}/api/mlops/models/trend-prediction-model/drift")

print("All tests completed!") 