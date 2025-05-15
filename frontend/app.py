import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
from zenml.client import Client
import plotly.express as px
from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime, timedelta
import urllib.parse

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
DB_PATH = BASE_DIR / "data" / "social_media.db"

app = Flask(__name__)
CORS(app)

def get_db_connection(db_name):
    url = os.getenv("DATABASE_URL")
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

def load_data(table: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    return df

# --- Seitenaufbau ---
st.set_page_config(page_title="Social Media Dashboard", layout="wide")
st.sidebar.title("📁 Navigation")
page = st.sidebar.radio("Seite wählen:", [
    "📊 Dashboard",
    "🗣️ Reddit",
    "🎵 TikTok",
    "📺 YouTube",
    "📋 Logs",
    "📦 Orchestration"
])

# --- Dashboard ---
if page == "📊 Dashboard":
    st.title("📊 Übersicht")
    try:
        reddit = load_data("reddit_data")[["created_utc", "scraped_at"]].copy()
        reddit["source"] = "Reddit"

        tiktok = load_data("tiktok_data")[["created_time", "scraped_at"]].copy()
        tiktok = tiktok.rename(columns={"created_time": "created_utc"})
        tiktok["source"] = "TikTok"

        youtube = load_data("youtube_data")[["published_at"]].copy()
        youtube["scraped_at"] = youtube["published_at"]
        youtube["created_utc"] = pd.to_datetime(youtube["scraped_at"]).astype(int) // 10**9
        youtube["source"] = "YouTube"

        df = pd.concat([reddit, tiktok, youtube], ignore_index=True)
        df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s", errors="coerce")
        df["date"] = df["created_utc"].dt.date
        # Nur April und Mai anzeigen
        df = df[(df["created_utc"].dt.month.isin([4, 5])) & (df["created_utc"].dt.year == 2025)]
        counts = df.groupby(["date", "source"]).size().unstack(fill_value=0)

        st.line_chart(counts)

    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {e}")

# --- Reddit ---
elif page == "🗣️ Reddit":
    st.title("🗣️ Reddit Daten")
    st.dataframe(load_data("reddit_data"))

# --- TikTok ---
elif page == "🎵 TikTok":
    st.title("🎵 TikTok Daten")
    st.dataframe(load_data("tiktok_data"))

# --- YouTube ---
elif page == "📺 YouTube":
    st.title("📺 YouTube Daten")
    st.dataframe(load_data("youtube_data"))

# --- Logs ---
elif page == "📋 Logs":
    st.title("📋 Logs")
    for log_file in ["reddit.log", "tiktok.log", "youtube.log"]:
        path = LOG_DIR / log_file
        if path.exists():
            st.subheader(f"📄 {log_file}")
            with open(path) as f:
                # Logs anzeigen (automatisch gescrollt)
                logs = path.read_text()
                st.text_area("📄 " + log_file, logs, height=300, key=log_file)
                st.markdown(f"<script>var textarea = window.document.querySelector('textarea#{log_file}'); textarea.scrollTop = textarea.scrollHeight;</script>", unsafe_allow_html=True)

        else:
            st.warning(f"{log_file} nicht gefunden.")

# --- Orchestration ---
elif page == "📦 Orchestration":
    st.title("📦 ZenML Orchestration Dashboard")

    client = Client()
    try:
        pipelines = client.list_pipelines()

        for pipeline in pipelines:
            st.subheader(f"🧪 Pipeline: `{pipeline.name}`")

            # Letzten Run finden
            runs = client.list_pipeline_runs(pipeline_name=pipeline.name, size=1).items
            if runs:
                last_run = runs[0]
                st.write(f"Letzter Status: `{last_run.status}`")
                st.write(f"Letzter Run: {last_run.created.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.info("Noch kein Lauf vorhanden.")

            if st.button(f"🚀 Starte `{pipeline.name}`", key=f"run_{pipeline.name}"):
                client.run_pipeline(pipeline.name)
                st.success(f"✅ Pipeline `{pipeline.name}` gestartet.")

        # Stack-Infos anzeigen
        st.subheader("🧱 Aktiver Stack")
        stack = client.active_stack
        st.markdown(f"**Stack Name:** `{stack.name}`")
        st.markdown("**Orchestrator:** `{}`".format(stack.orchestrator.flavor))
        st.markdown("**Artifact Store:** `{}`".format(stack.artifact_store.uri))
        st.markdown("**Experiment Tracker:** `{}`".format(stack.experiment_tracker.name if stack.experiment_tracker else "–"))

    except Exception as e:
        st.error(f"❌ Fehler beim Abrufen von ZenML-Pipelines: {e}")

if __name__ == '__main__':
    app.run(debug=True)

