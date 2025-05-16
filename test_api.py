import requests

def test_api():
    # Try both ports
    urls = [
        "http://localhost:8000/api/mlops/models/topic_model/drift",
        "http://localhost:8001/api/mlops/models/topic_model/drift"
    ]
    params = {"version": "v1.0.2"}
    
    for url in urls:
        try:
            print(f"Testing {url}...")
            response = requests.get(url, params=params)
            print(f"Status code: {response.status_code}")
            if response.status_code == 200:
                print("Response data:")
                print(response.json())
                return  # Exit once we get a successful response
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception for {url}: {e}")
            
    print("Failed to get data from both endpoints")

if __name__ == "__main__":
    test_api() 