import requests
import json

# Test the API
response = requests.get('http://localhost:8000/api/topic-model')

# Print status code and pretty print the JSON response
print(f"Status code: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
    
    # Check if topics are present
    if 'topics' in data and data['topics']:
        print(f"\nFound {len(data['topics'])} topics:")
        for i, topic in enumerate(data['topics']):
            print(f"  {i+1}. {topic.get('name', 'Unnamed')} (ID: {topic.get('id', 'unknown')})")
            keywords = topic.get('keywords', [])
            if keywords:
                print(f"     Keywords: {', '.join(keywords[:3])}...")
    else:
        print("\nNo topics found in the response!")
        
    # Check topic counts by date
    if 'topic_counts_by_date' in data and data['topic_counts_by_date']:
        print(f"\nTopic counts by date are available for {len(data['topic_counts_by_date'])} topics")
    else:
        print("\nNo topic counts by date found!")
        
    # Check time range
    if 'time_range' in data:
        print(f"\nTime range: {data['time_range'].get('start_date', 'unknown')} to {data['time_range'].get('end_date', 'unknown')}")
else:
    print(f"Error: {response.text}") 