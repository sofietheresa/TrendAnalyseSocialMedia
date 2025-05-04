import logging
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
import pandas as pd
import os
from datetime import datetime, timedelta

# === Setup ===
DATA_PATH = Path("/app/data/raw/youtube_data.csv")
LOG_PATH = Path("/app/logs/youtube.log")
MIN_HOURS_BETWEEN_SCRAPES = 6  # Mindestzeit zwischen Scrapes

# .env laden
load_dotenv()

# Logging einrichten
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# YouTube API
API_KEY = os.getenv("YT_KEY")
if not API_KEY:
    logging.error(" Kein YT_KEY gefunden. Bitte .env prüfen.")
    raise EnvironmentError("YT_KEY fehlt")

youtube = build("youtube", "v3", developerKey=API_KEY)

def should_scrape():
    """Prüft, ob seit dem letzten Scrape genügend Zeit vergangen ist"""
    if not DATA_PATH.exists():
        return True
    
    try:
        df = pd.read_csv(DATA_PATH)
        if df.empty:
            return True
        
        last_scrape = pd.to_datetime(df['scraped_at'].max())
        time_since_last = datetime.now() - last_scrape
        
        if time_since_last < timedelta(hours=MIN_HOURS_BETWEEN_SCRAPES):
            logging.info(f"⏳ Letzter Scrape vor {time_since_last.total_seconds() / 3600:.1f} Stunden - warte noch")
            return False
            
        return True
    except Exception as e:
        logging.warning(f"⚠️ Fehler beim Prüfen des letzten Scrape-Zeitpunkts: {e}")
        return True

def scrape_youtube_trending(region="DE", max_results=50):
    if not should_scrape():
        return
        
    try:
        logging.info("🔍 Starte YouTube-Scraping...")

        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=region,
            maxResults=max_results
        )
        response = request.execute()

        videos = []
        scrape_time = datetime.now()

        for item in response.get("items", []):
            snippet = item["snippet"]
            stats = item.get("statistics", {})

            videos.append({
                "video_id": item["id"],
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "view_count": stats.get("viewCount"),
                "like_count": stats.get("likeCount"),
                "comment_count": stats.get("commentCount"),
                "url": f"https://www.youtube.com/watch?v={item['id']}",
                "scraped_at": scrape_time.isoformat(),
                "trending_date": scrape_time.date().isoformat()
            })

        # CSV schreiben
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(videos)
        logging.info(f"🔄 Neue Daten: {len(df)} Videos gefunden")

        if DATA_PATH.exists():
            df_existing = pd.read_csv(DATA_PATH, on_bad_lines='warn')
            logging.info(f"📊 Bestehende Daten: {len(df_existing)} Videos")
            if len(df_existing) == 0:
                logging.warning("⚠️ Bestehende CSV-Datei ist leer!")
            
            # Nur als Duplikat markieren, wenn Video-ID UND Trending-Datum gleich sind
            df = pd.concat([df_existing, df], ignore_index=True)
            logging.info(f"🔄 Nach Zusammenführung: {len(df)} Videos")
        else:
            logging.warning("⚠️ Keine bestehende CSV-Datei gefunden - erstelle neue Datei")

        before_dedup = len(df)
        df.drop_duplicates(subset=["video_id", "trending_date"], inplace=True)
        after_dedup = len(df)
        if before_dedup != after_dedup:
            logging.info(f"🔍 {before_dedup - after_dedup} Duplikate entfernt")

        # Nach Video-ID und Trending-Datum sortieren
        df = df.sort_values(["video_id", "trending_date"], ascending=[True, False])

        df.to_csv(DATA_PATH, index=False)
        logging.info(f"✅ {len(df)} Videos gespeichert unter: {DATA_PATH}")

    except Exception as e:
        logging.error(f"❌ Fehler beim YouTube-Scraping: {e}")
        print(f" Fehler: {e}")

# === Direkter Aufruf ===
if __name__ == "__main__":
    scrape_youtube_trending()
