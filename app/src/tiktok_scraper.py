from TikTokApi import TikTokApi
import asyncio
import os
import csv
from dotenv import load_dotenv

# Load .env values
load_dotenv()

ms_token = os.getenv("MS_TOKEN")
csv_path = os.getenv("OUTPUT_PATH", "trending_videos.csv")


async def trending_videos():
    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,
            browser=os.getenv("TIKTOK_BROWSER", "chromium")
        )

        data = []

        async for video in api.trending.videos(count=30):
            info = video.as_dict
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

        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        file_exists = os.path.isfile(csv_path)
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(data)

        print(f"\n✅ Erfolgreich {len(data)} Videos in '{csv_path}' gespeichert.")


if __name__ == "__main__":
    asyncio.run(trending_videos())
