import asyncio
import os
import csv
import logging
from TikTokApi import TikTokApi
from dotenv import load_dotenv
from pathlib import Path


# .env laden
load_dotenv()

ms_token = os.getenv("MS_TOKEN")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "../data/raw/tiktok_data.csv")
csv_path = os.path.normpath(csv_path)

log_path =  Path(os.path.join(BASE_DIR,"../../logs/tiktok.log"))
log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


async def trending_videos():
    if not ms_token:
        logging.error("MS_TOKEN fehlt. Bitte prüfe deine .env-Datei.")
        return

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,
            browser=os.getenv("TIKTOK_BROWSER", "chromium"),
            headless=False 
        )

        data = []

        logging.info(" Lade Trending-Videos von TikTok ...")

        async for video in api.trending.videos(count=30):
            info = video.as_dict
            logging.debug(f"Video gefunden: {info.get('id')}")
            data.append({
                "id": info.get("id"),
                "description": info.get("desc"),
                "author_username": info.get("author", {}).get("uniqueId"),
                "author_id": info.get("author", {}).get("id"),
                "likes": info.get("stats", {}).get("diggCount"),
                "shares": info.get("stats", {}).get("shareCount"),
                "comments": info.get("stats", {}).get("commentCount"),
                "plays": info.get("stats", {}).get("playCount"),
                "video_url": info.get("video", {}).get("downloadAddr"),
                "created_time": info.get("createTime"),
            })

        if not data:
            logging.warning("⚠️ Keine Videos gefunden.")
            return

        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        file_exists = os.path.isfile(csv_path)
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(data)

        logging.info(f"✅ Erfolgreich {len(data)} Videos in '{csv_path}' gespeichert.")


if __name__ == "__main__":
    asyncio.run(trending_videos())
