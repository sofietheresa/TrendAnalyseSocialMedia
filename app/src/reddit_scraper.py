import os
import praw
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import logging

#  .env einladen
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
csv_path = (BASE_DIR / "../data/raw/reddit_data.csv").resolve()

# Logging
log_path = (BASE_DIR / "../../logs/reddit.log").resolve()
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# scrape Reddit
def scrape_reddit():
    try:
        logging.info(" Starte Reddit-Scraping...")

        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_ID"),
            client_secret=os.getenv("REDDIT_SECRET"),
            user_agent=os.getenv("USER_AGENT")
        )

        subreddits = ["all", "popular", "trendingreddits", "trendingsubreddits"]
        post_limit = 100
        all_posts = []
        scrape_time = datetime.now()

        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.hot(limit=post_limit):
                if post.is_self:
                    all_posts.append({
                        "subreddit": sub,
                        "title": post.title,
                        "text": post.selftext,
                        "score": post.score,
                        "comments": post.num_comments,
                        "created": datetime.fromtimestamp(post.created),
                        "url": post.url,
                        "scraped_at": scrape_time
                    })

        df = pd.DataFrame(all_posts)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        if csv_path.exists():
            df_existing = pd.read_csv(csv_path)
            df = pd.concat([df_existing, df], ignore_index=True)

        df.drop_duplicates(subset=["title", "text", "subreddit"], inplace=True)
        df.to_csv(csv_path, index=False)

        logging.info(f" {len(df)} Einträge gespeichert unter {csv_path}")

    except Exception as e:
        logging.error(f" Fehler beim Reddit-Scraping: {e}")

if __name__ == "__main__":
    scrape_reddit()
