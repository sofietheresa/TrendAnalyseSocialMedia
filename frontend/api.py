from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
import urllib.parse

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
        
        # Ensure platform is valid
        if platform not in ['reddit', 'tiktok', 'youtube']:
            return jsonify({'error': 'Invalid platform specified'}), 400
        
        # Initialize database engine if it doesn't exist
        db_name = f"{platform}_data"
        if db_name not in db_engines:
            db_engines[db_name] = get_db_connection(db_name)
        
        # Dynamically create the appropriate column selection query based on platform
        if platform == 'reddit':
            query = text(f"""
                SELECT id, title, text, author, created_at, url, scraped_at
                FROM {platform}_data
                ORDER BY scraped_at DESC
                LIMIT :limit
            """)
        elif platform == 'tiktok':
            query = text(f"""
                SELECT id, text, author, create_time as created_at, url, scraped_at
                FROM {platform}_data
                ORDER BY scraped_at DESC
                LIMIT :limit
            """)
        elif platform == 'youtube':
            query = text(f"""
                SELECT id, title, description as text, author, published_at as created_at, url, scraped_at
                FROM {platform}_data
                ORDER BY scraped_at DESC
                LIMIT :limit
            """)
        
        with db_engines[db_name].connect() as conn:
            result = conn.execute(query, {'limit': limit})
            data = []
            for row in result:
                item = dict(row._mapping)
                # Convert datetime objects to ISO format strings
                for key, value in item.items():
                    if isinstance(value, datetime):
                        item[key] = value.isoformat()
                data.append(item)
            
            return jsonify({'data': data})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 