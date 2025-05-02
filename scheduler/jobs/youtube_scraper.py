import logging
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
import pandas as pd
import os
from datetime import datetime

# === Setup ===
DATA_PATH = Path("/app/data/raw/youtube_data.csv")
LOG_PATH = Path("/app/logs/youtube.log")

# .env laden
load_dotenv()

# Logging einrichten
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# YouTube API
API_KEY = os.getenv("YT_KEY")
if not API_KEY:
    logging.error(" Kein YT_KEY gefunden. Bitte .env prüfen.")
    raise EnvironmentError("YT_KEY fehlt")

youtube = build("youtube", "v3", developerKey=API_KEY)

# === Scraper Funktion ===
def scrape_youtube_trending(region="DE", max_results=50):
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
                "scraped_at": scrape_time
            })

        # CSV schreiben
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(videos)

        if DATA_PATH.exists():
            df_existing = pd.read_csv(DATA_PATH)
            df = pd.concat([df_existing, df], ignore_index=True)

        df.drop_duplicates(subset=["video_id"], inplace=True)
        df.to_csv(DATA_PATH, index=False)

        logging.info(f"✅ {len(df)} Videos gespeichert unter: {DATA_PATH}")

    except Exception as e:
        logging.error(f"❌ Fehler beim YouTube-Scraping: {e}")
        print(f" Fehler: {e}")

# === Direkter Aufruf ===
if __name__ == "__main__":
    scrape_youtube_trending()
