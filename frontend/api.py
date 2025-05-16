from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
import urllib.parse
import random

app = Flask(__name__)
# CORS für lokale Entwicklung erlauben
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # React Dev Server
            "https://trendanalysesocialmedia.vercel.app",  # Produktions-URL
            "https://trendanalysesocialmedia-production.up.railway.app"  # Railway App URL
        ]
    }
})

def get_db_connection(db_name):
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    result = urllib.parse.urlparse(url)
    conn_str = f"postgresql://{result.username}:{result.password}@{result.hostname}:{result.port}/{db_name}"
    return create_engine(conn_str)

# Dictionary für die Datenbankverbindungen
db_engines = {}

@app.route('/api/scraper-status')
def get_scraper_status():
    try:
        # Check if any data was added in the last 20 minutes to determine if scraper is running
        cutoff_time = datetime.now() - timedelta(minutes=20)
        
        status = {
            'reddit': {'running': False, 'total_posts': 0, 'last_update': None},
            'tiktok': {'running': False, 'total_posts': 0, 'last_update': None},
            'youtube': {'running': False, 'total_posts': 0, 'last_update': None}
        }
        
        # Initialize database engines if they don't exist
        for db in ['reddit_data', 'tiktok_data', 'youtube_data']:
            if db not in db_engines:
                db_engines[db] = get_db_connection(db)
        
        # Check Reddit
        with db_engines['reddit_data'].connect() as conn:
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM reddit_data"))
            count, last_update = result.fetchone()
            status['reddit'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        # Check TikTok
        with db_engines['tiktok_data'].connect() as conn:
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM tiktok_data"))
            count, last_update = result.fetchone()
            status['tiktok'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        # Check YouTube
        with db_engines['youtube_data'].connect() as conn:
            result = conn.execute(text("SELECT COUNT(*), MAX(scraped_at) FROM youtube_data"))
            count, last_update = result.fetchone()
            status['youtube'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-stats')
def get_daily_stats():
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        stats = {
            'reddit': [],
            'tiktok': [],
            'youtube': []
        }
        
        # Initialize database engines if they don't exist
        for db in ['reddit_data', 'tiktok_data', 'youtube_data']:
            if db not in db_engines:
                db_engines[db] = get_db_connection(db)
        
        # Get Reddit daily stats
        with db_engines['reddit_data'].connect() as conn:
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM reddit_data
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['reddit'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
        
        # Get TikTok daily stats
        with db_engines['tiktok_data'].connect() as conn:
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM tiktok_data
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['tiktok'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
        
        # Get YouTube daily stats
        with db_engines['youtube_data'].connect() as conn:
            result = conn.execute(text("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM youtube_data
                WHERE scraped_at >= :start_date
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """), {'start_date': start_date})
            stats['youtube'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in result]
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-data')
def get_recent_data():
    try:
        platform = request.args.get('platform', 'reddit')
        limit = min(int(request.args.get('limit', 10)), 100)  # Limit to max 100 records
        
        print(f"Fetching {platform} data with limit {limit}")
        
        # Ensure platform is valid
        if platform not in ['reddit', 'tiktok', 'youtube']:
            return jsonify({'error': 'Invalid platform specified'}), 400
        
        # Initialize database engine if it doesn't exist
        db_name = f"{platform}_data"
        if db_name not in db_engines:
            print(f"Initializing database connection for {db_name}")
            db_engines[db_name] = get_db_connection(db_name)
        
        # Try both table formats: platform_data and platform_posts
        table_names = [f"{platform}_data", f"{platform}_posts"]
        
        # Dynamically create the appropriate column selection query based on platform
        if platform == 'reddit':
            for table_name in table_names:
                try:
                    query = text(f"""
                        SELECT COUNT(*) FROM {table_name}
                    """)
                    with db_engines[db_name].connect() as conn:
                        result = conn.execute(query)
                        if result.scalar() > 0:
                            print(f"Using table {table_name}")
                            query = text(f"""
                                SELECT id, title, text, author, created_at, url, scraped_at
                                FROM {table_name}
                                ORDER BY scraped_at DESC
                                LIMIT :limit
                            """)
                            break
                except:
                    continue
            else:
                # If no table found, default to platform_data
                print(f"No valid table found, defaulting to {platform}_data")
                query = text(f"""
                    SELECT id, title, text, author, created_at, url, scraped_at
                    FROM {platform}_data
                    ORDER BY scraped_at DESC
                    LIMIT :limit
                """)
                
        elif platform == 'tiktok':
            for table_name in table_names:
                try:
                    query = text(f"""
                        SELECT COUNT(*) FROM {table_name}
                    """)
                    with db_engines[db_name].connect() as conn:
                        result = conn.execute(query)
                        if result.scalar() > 0:
                            print(f"Using table {table_name}")
                            query = text(f"""
                                SELECT id, text, author, create_time as created_at, url, scraped_at
                                FROM {table_name}
                                ORDER BY scraped_at DESC
                                LIMIT :limit
                            """)
                            break
                except:
                    continue
            else:
                # If no table found, default to platform_data
                print(f"No valid table found, defaulting to {platform}_data")
                query = text(f"""
                    SELECT id, text, author, create_time as created_at, url, scraped_at
                    FROM {platform}_data
                    ORDER BY scraped_at DESC
                    LIMIT :limit
                """)
                
        elif platform == 'youtube':
            for table_name in table_names:
                try:
                    query = text(f"""
                        SELECT COUNT(*) FROM {table_name}
                    """)
                    with db_engines[db_name].connect() as conn:
                        result = conn.execute(query)
                        if result.scalar() > 0:
                            print(f"Using table {table_name}")
                            query = text(f"""
                                SELECT id, title, description as text, author, published_at as created_at, url, scraped_at
                                FROM {table_name}
                                ORDER BY scraped_at DESC
                                LIMIT :limit
                            """)
                            break
                except:
                    continue
            else:
                # If no table found, default to platform_data
                print(f"No valid table found, defaulting to {platform}_data")
                query = text(f"""
                    SELECT id, title, description as text, author, published_at as created_at, url, scraped_at
                    FROM {platform}_data
                    ORDER BY scraped_at DESC
                    LIMIT :limit
                """)
        
        with db_engines[db_name].connect() as conn:
            print(f"Executing query: {query}")
            result = conn.execute(query, {'limit': limit})
            data = []
            for row in result:
                item = dict(row._mapping)
                # Convert datetime objects to ISO format strings
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
                data.append(item)
            
            print(f"Found {len(data)} records for {platform}")
            return jsonify({'data': data})
            
    except Exception as e:
        print(f"Error in get_recent_data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'data': []}), 500

@app.route('/api/db/predictions')
def get_predictions():
    """
    Get topic predictions from ML models.
    
    Query Parameters:
    - start_date: (optional) Start date for the prediction period (YYYY-MM-DD)
    - end_date: (optional) End date for the prediction period (YYYY-MM-DD)
    
    Returns prediction data for future trends based on ML models.
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Use default dates if not provided
        if not start_date:
            start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
        # Convert to datetime objects
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Generate prediction data (mock data for now)
        predictions = generate_mock_predictions(start_dt, end_dt, num_topics=5)
        
        response = {
            'predictions': predictions,
            'time_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'prediction_trends': generate_mock_prediction_trends(predictions, start_dt, end_dt)
        }
        
        return jsonify(response)
    except Exception as e:
        print(f"Error in get_predictions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def generate_mock_predictions(start_date, end_date, num_topics=5):
    """Generate mock prediction data for topics."""
    topics = [
        {"id": 1, "name": "Artificial Intelligence", "keywords": ["AI", "machine learning", "neural networks", "deep learning", "GPT"]},
        {"id": 2, "name": "Climate Change", "keywords": ["environment", "global warming", "renewable energy", "sustainability", "carbon"]},
        {"id": 3, "name": "Digital Privacy", "keywords": ["data protection", "encryption", "surveillance", "security", "GDPR"]},
        {"id": 4, "name": "Quantum Computing", "keywords": ["qubits", "quantum supremacy", "superposition", "entanglement", "quantum algorithms"]},
        {"id": 5, "name": "Space Exploration", "keywords": ["Mars", "NASA", "SpaceX", "astronomy", "satellites"]},
        {"id": 6, "name": "Cryptocurrencies", "keywords": ["Bitcoin", "blockchain", "Ethereum", "NFT", "DeFi"]},
        {"id": 7, "name": "Remote Work", "keywords": ["WFH", "hybrid work", "virtual collaboration", "digital nomad", "productivity"]},
        {"id": 8, "name": "Mental Health", "keywords": ["wellness", "therapy", "mindfulness", "psychology", "self-care"]}
    ]
    
    # Randomly select topics for predictions
    selected_topics = random.sample(topics, min(num_topics, len(topics)))
    
    # Generate date range for forecast data (7 days from start_date)
    forecast_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    predictions = []
    for topic in selected_topics:
        # Generate random confidence between 60% and 95%
        confidence = round(random.uniform(0.6, 0.95), 2)
        
        # Generate random sentiment score between -0.8 and 0.8
        sentiment_score = round(random.uniform(-0.8, 0.8), 2)
        
        # Generate forecast data (daily post counts)
        max_value = random.randint(80, 300)
        forecast_data = {}
        for date in forecast_dates:
            # Generate a slightly upward trend with some randomness
            day_index = forecast_dates.index(date)
            trend_factor = 1 + (day_index * 0.1)  # Increases by 10% each day
            randomness = random.uniform(0.8, 1.2)  # +/- 20% random variation
            value = max_value * trend_factor * randomness
            forecast_data[date] = round(value)
        
        predictions.append({
            "topic_id": topic["id"],
            "topic_name": topic["name"],
            "confidence": confidence,
            "sentiment_score": sentiment_score,
            "keywords": topic["keywords"],
            "forecast_data": forecast_data,
            "forecast_max": max(forecast_data.values())
        })
    
    # Sort predictions by confidence (highest first)
    predictions.sort(key=lambda x: x["confidence"], reverse=True)
    
    return predictions

def generate_mock_prediction_trends(predictions, start_date, end_date):
    """Generate mock trend data for the predictions chart."""
    # Create a date range from start_date to end_date
    delta = (end_date - start_date).days + 1
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta)]
    
    trends = {}
    for prediction in predictions:
        topic_id = prediction["topic_id"]
        trends[topic_id] = {}
        
        # Base value - higher for topics with higher confidence
        base_value = random.randint(50, 100) * prediction["confidence"]
        
        # Generate trend values for each date
        for i, date in enumerate(dates):
            # Create a slightly upward trend with random variations
            trend_factor = 1 + (i * 0.05)  # Increases by 5% each day
            randomness = random.uniform(0.9, 1.1)  # +/- 10% random variation
            value = base_value * trend_factor * randomness
            trends[topic_id][date] = round(value)
    
    return trends

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 