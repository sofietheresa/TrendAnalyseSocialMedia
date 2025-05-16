"""
Test script for checking API endpoints
"""
import requests
import json

def test_debug_routes():
    """Test the debug/routes endpoint to see all available routes"""
    url = "http://localhost:8000/debug/routes"
    try:
        print(f"Fetching routes from {url}...")
        response = requests.get(url)
        if response.status_code == 200:
            routes = response.json()["routes"]
            
            # Print all routes
            print("\nAvailable routes:")
            for route in routes:
                methods = route.get("methods", ["GET"])
                print(f"{', '.join(methods)} {route['path']}")
                
            # Check for drift endpoint
            drift_paths = [r for r in routes if "drift" in r["path"]]
            if drift_paths:
                print("\nFound drift endpoints:")
                for path in drift_paths:
                    print(f"- {path['path']}")
            else:
                print("\nNo drift endpoints found!")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

def test_model_drift_endpoint():
    """Test the model drift endpoint"""
    url = "http://localhost:8000/api/mlops/models/topic_model/drift"
    params = {"version": "v1.0.2"}
    
    try:
        print(f"\nTesting model drift endpoint: {url}")
        response = requests.get(url, params=params)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_debug_routes()
    test_model_drift_endpoint() 