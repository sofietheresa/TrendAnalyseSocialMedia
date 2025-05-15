from flask import Flask, jsonify
from flask_cors import CORS
import asyncpg
import os
from datetime import datetime, timedelta
import urllib.parse
import asyncio
from functools import wraps

app = Flask(__name__)
CORS(app)

async def get_db_pool(db_name):
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    result = urllib.parse.urlparse(url)
    conn_str = f"postgresql://{result.username}:{result.password}@{result.hostname}:{result.port}/{db_name}"
    return await asyncpg.create_pool(conn_str)

# Globaler Pool für Datenbankverbindungen
db_pools = {}

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

@app.route('/api/scraper-status')
@async_route
async def get_scraper_status():
    try:
        # Check if any data was added in the last 20 minutes to determine if scraper is running
        cutoff_time = datetime.now() - timedelta(minutes=20)
        
        status = {
            'reddit': {'running': False, 'total_posts': 0, 'last_update': None},
            'tiktok': {'running': False, 'total_posts': 0, 'last_update': None},
            'youtube': {'running': False, 'total_posts': 0, 'last_update': None}
        }
        
        # Initialize connection pools if they don't exist
        for db in ['reddit_data', 'tiktok_data', 'youtube_data']:
            if db not in db_pools:
                db_pools[db] = await get_db_pool(db)
        
        # Check Reddit
        async with db_pools['reddit_data'].acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*), MAX(scraped_at) FROM reddit_data")
            count, last_update = row['count'], row['max']
            status['reddit'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        # Check TikTok
        async with db_pools['tiktok_data'].acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*), MAX(scraped_at) FROM tiktok_data")
            count, last_update = row['count'], row['max']
            status['tiktok'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        # Check YouTube
        async with db_pools['youtube_data'].acquire() as conn:
            row = await conn.fetchrow("SELECT COUNT(*), MAX(scraped_at) FROM youtube_data")
            count, last_update = row['count'], row['max']
            status['youtube'].update({
                'running': last_update and last_update > cutoff_time,
                'total_posts': count,
                'last_update': last_update.isoformat() if last_update else None
            })
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-stats')
@async_route
async def get_daily_stats():
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        stats = {
            'reddit': [],
            'tiktok': [],
            'youtube': []
        }
        
        # Initialize connection pools if they don't exist
        for db in ['reddit_data', 'tiktok_data', 'youtube_data']:
            if db not in db_pools:
                db_pools[db] = await get_db_pool(db)
        
        # Get Reddit daily stats
        async with db_pools['reddit_data'].acquire() as conn:
            rows = await conn.fetch("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM reddit_data
                WHERE scraped_at >= $1
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """, start_date)
            stats['reddit'] = [{'date': row['date'].isoformat(), 'count': row['count']} for row in rows]
        
        # Get TikTok daily stats
        async with db_pools['tiktok_data'].acquire() as conn:
            rows = await conn.fetch("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM tiktok_data
                WHERE scraped_at >= $1
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """, start_date)
            stats['tiktok'] = [{'date': row['date'].isoformat(), 'count': row['count']} for row in rows]
        
        # Get YouTube daily stats
        async with db_pools['youtube_data'].acquire() as conn:
            rows = await conn.fetch("""
                SELECT DATE(scraped_at) as date, COUNT(*) as count
                FROM youtube_data
                WHERE scraped_at >= $1
                GROUP BY DATE(scraped_at)
                ORDER BY date
            """, start_date)
            stats['youtube'] = [{'date': row['date'].isoformat(), 'count': row['count']} for row in rows]
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 