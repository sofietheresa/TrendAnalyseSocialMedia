from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime, timedelta
import urllib.parse

app = Flask(__name__)
CORS(app)

def get_db_connection(db_name):
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    result = urllib.parse.urlparse(url)
    new_url = f"{result.scheme}://{result.username}:{result.password}@{result.hostname}:{result.port}/{db_name}"
    return psycopg2.connect(new_url)

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
        
        # Check Reddit
        with get_db_connection('reddit_data') as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*), MAX(scraped_at) FROM reddit_data")
                count, last_update = cur.fetchone()
                status['reddit'].update({
                    'running': last_update and last_update > cutoff_time,
                    'total_posts': count,
                    'last_update': last_update.isoformat() if last_update else None
                })
        
        # Check TikTok
        with get_db_connection('tiktok_data') as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*), MAX(scraped_at) FROM tiktok_data")
                count, last_update = cur.fetchone()
                status['tiktok'].update({
                    'running': last_update and last_update > cutoff_time,
                    'total_posts': count,
                    'last_update': last_update.isoformat() if last_update else None
                })
        
        # Check YouTube
        with get_db_connection('youtube_data') as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*), MAX(scraped_at) FROM youtube_data")
                count, last_update = cur.fetchone()
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
        
        # Get Reddit daily stats
        with get_db_connection('reddit_data') as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DATE(scraped_at) as date, COUNT(*) as count
                    FROM reddit_data
                    WHERE scraped_at >= %s
                    GROUP BY DATE(scraped_at)
                    ORDER BY date
                """, (start_date,))
                stats['reddit'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in cur.fetchall()]
        
        # Get TikTok daily stats
        with get_db_connection('tiktok_data') as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DATE(scraped_at) as date, COUNT(*) as count
                    FROM tiktok_data
                    WHERE scraped_at >= %s
                    GROUP BY DATE(scraped_at)
                    ORDER BY date
                """, (start_date,))
                stats['tiktok'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in cur.fetchall()]
        
        # Get YouTube daily stats
        with get_db_connection('youtube_data') as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DATE(scraped_at) as date, COUNT(*) as count
                    FROM youtube_data
                    WHERE scraped_at >= %s
                    GROUP BY DATE(scraped_at)
                    ORDER BY date
                """, (start_date,))
                stats['youtube'] = [{'date': row[0].isoformat(), 'count': row[1]} for row in cur.fetchall()]
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 