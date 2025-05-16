"""
Test the dedicated drift API
"""
import requests
import json

def test_drift_api():
    """Test the dedicated drift API server"""
    base_url = "http://localhost:8080"
    
    # Test the root endpoint
    try:
        print(f"Testing root endpoint at {base_url}...")
        response = requests.get(base_url)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test the model drift endpoint
    drift_url = f"{base_url}/api/mlops/models/topic_model/drift"
    params = {"version": "v1.0.2"}
    
    try:
        print(f"\nTesting model drift endpoint at {drift_url}...")
        response = requests.get(drift_url, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_drift_api() 